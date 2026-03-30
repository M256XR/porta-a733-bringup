#!/usr/bin/env python3
"""Install Radxa vendor Linux onto Disk 3 for UEFI boot testing."""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import gzip
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
FILE_BEGIN = 0
FILE_FLAG_WRITE_THROUGH = 0x80000000
FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_UNLOCK_VOLUME = 0x0009001C
FSCTL_DISMOUNT_VOLUME = 0x00090020
INVALID_HANDLE_VALUE = ctypes.wintypes.HANDLE(-1).value

k32 = ctypes.windll.kernel32

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_VENDOR_BOOT = SCRIPT_DIR.parent / "roms" / "_work" / "radxa_vendor_boot"
VENDOR_IMAGE_CANDIDATES = (
    SCRIPT_DIR.parent / "roms" / "_work" / "radxa-cubie-a7z_bullseye_kde_b1.output_512.img",
    Path(r"D:\Projects\PortaRe0\software\roms\_work\radxa-cubie-a7z_bullseye_kde_b1.output_512.img"),
)
DISK_PATH = r"\\.\PhysicalDrive3"
BOOT_PROFILES = ("xorg-direct", "graphical-x11")

# Radxa vendor image GPT layout from fdisk -l
VENDOR_ROOT_START_SECTOR = 679_936
VENDOR_ROOT_SECTORS = 12_829_761
SECTOR_SIZE = 512
VENDOR_ROOT_OFFSET = VENDOR_ROOT_START_SECTOR * SECTOR_SIZE
VENDOR_ROOT_BYTES = VENDOR_ROOT_SECTORS * SECTOR_SIZE
VENDOR_ROOT_UUID = "dda3891f-a196-4377-be03-6fda49c5c988"
VENDOR_HDMI_EDID_HEX = (
    "00ffffffffffff003354010000000000"
    "0c1b0103800000780a07f59a564e8626"
    "1e505400000000000000000000000000"
    "000000000000ff4fa096500010a04623"
    "c2005aa000000018000000fc004c5330"
    "36305231535830312020000000ff0030"
    "303030303030302020202020000000fd"
    "00174b0ff01e000a2020202020200182"
    "02031774470000000000000023097f07"
    "66030c00300080ff4fa096500010a046"
    "23c2005aa000000018ff4fa096500010"
    "a04623c2005aa000000018ff4fa09650"
    "0010a04623c2005aa000000018ff4fa0"
    "96500010a04623c2005aa000000018ff"
    "4fa096500010a04623c2005aa0000000"
    "1800000000000000000000000000008d"
)


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_powershell(command: str) -> str:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
            "$OutputEncoding=[System.Text.Encoding]::UTF8; "
            + command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def to_wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{rest}"


def run_wsl_bash(script: str) -> None:
    subprocess.run(
        ["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-lc", script],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_wsl_bash_as_root(script: str, distro: str = "Ubuntu-22.04") -> None:
    subprocess.run(
        ["wsl", "-u", "root", "-d", distro, "--", "bash", "-lc", script],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run_wsl_script_as_root(script: str, distro: str = "Ubuntu-22.04") -> None:
    subprocess.run(
        ["wsl", "-u", "root", "-d", distro, "--", "bash", "-s"],
        input=script.encode("utf-8"),
        check=True,
    )


def parse_wsl_unc_path(path: Path) -> tuple[str, str] | None:
    path_text = str(path)
    prefix = "\\\\wsl.localhost\\"
    if not path_text.lower().startswith(prefix.lower()):
        return None
    rest = path_text[len(prefix):]
    parts = rest.split("\\")
    if len(parts) < 2:
        return None
    distro = parts[0]
    wsl_path = "/" + "/".join(parts[1:])
    return distro, wsl_path


def open_handle(path: str, write: bool = False):
    access = GENERIC_READ | (GENERIC_WRITE if write else 0)
    flags = FILE_FLAG_WRITE_THROUGH if write else 0
    handle = k32.CreateFileW(
        path,
        access,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        flags,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        fail(f"CreateFileW failed for {path} (err={k32.GetLastError()})")
    return handle


def ioctl(handle, code: int, label: str) -> None:
    transferred = ctypes.wintypes.DWORD(0)
    ok = k32.DeviceIoControl(handle, code, None, 0, None, 0, ctypes.byref(transferred), None)
    status = "OK" if ok else f"err={k32.GetLastError()}"
    print(f"  {label}: {status}")


def set_file_pointer(handle, offset: int) -> None:
    new_pos = ctypes.c_longlong()
    ok = k32.SetFilePointerEx(handle, ctypes.c_longlong(offset), ctypes.byref(new_pos), FILE_BEGIN)
    if not ok or new_pos.value != offset:
        fail(f"SetFilePointerEx failed at offset 0x{offset:X} (err={k32.GetLastError()})")


def lock_disk3_volumes():
    vol_ids = run_powershell(
        "Get-Partition -DiskNumber 3 | Get-Volume | ForEach-Object { $_.UniqueId }"
    ).splitlines()
    handles = []
    for vid in [v.strip() for v in vol_ids if v.strip()]:
        path = vid.rstrip("\\")
        print(f"Locking {path}")
        handle = open_handle(path, write=True)
        ioctl(handle, FSCTL_LOCK_VOLUME, "Lock")
        ioctl(handle, FSCTL_DISMOUNT_VOLUME, "Dismount")
        handles.append(handle)
    return handles


def unlock_handles(handles) -> None:
    for handle in handles:
        ioctl(handle, FSCTL_UNLOCK_VOLUME, "Unlock")
        k32.CloseHandle(handle)


def get_partition3_info() -> tuple[int, int]:
    output = run_powershell(
        "$p = Get-Partition -DiskNumber 3 -PartitionNumber 3; "
        "Write-Output ($p.Offset.ToString() + ',' + $p.Size.ToString())"
    )
    offset_text, size_text = output.split(",", 1)
    return int(offset_text), int(size_text)


def normalize_existing_dir(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"Path does not exist: {path}")
    if not path.is_dir():
        fail(f"Path is not a directory: {path}")
    return path


def resolve_vendor_image_path(path_text: str | None) -> Path:
    if path_text:
        path = Path(path_text)
        if not path.exists():
            fail(f"Vendor image not found: {path}")
        return path

    for candidate in VENDOR_IMAGE_CANDIDATES:
        if candidate.exists():
            return candidate

    fail(
        "Vendor image not found in default locations. "
        "Pass --vendor-image explicitly or place the raw image under roms/_work."
    )


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    shutil.copy2(src, dst)


def write_text_file(dst: Path, text: str, executable: bool = False) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    dst.write_text(text, encoding="utf-8", newline="\n")
    if executable:
        os.chmod(dst, 0o755)


def copy_executable(src: Path, dst: Path) -> None:
    copy_file(src, dst)
    os.chmod(dst, 0o755)


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        os.chmod(path, stat.S_IWRITE)
        path.unlink()


def ensure_symlink(link_path: Path, target: str) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    remove_path(link_path)
    os.symlink(target, link_path)


def mask_systemd_unit(rootfs: Path, unit_name: str) -> None:
    ensure_symlink(rootfs / "etc" / "systemd" / "system" / unit_name, "/dev/null")


def unmask_systemd_unit(rootfs: Path, unit_name: str) -> None:
    link_path = rootfs / "etc" / "systemd" / "system" / unit_name
    if not link_path.is_symlink():
        return
    if os.readlink(link_path) == "/dev/null":
        link_path.unlink()


def enable_systemd_unit(rootfs: Path, unit_name: str, target_name: str) -> None:
    wants_path = rootfs / "etc" / "systemd" / "system" / f"{target_name}.wants" / unit_name
    ensure_symlink(wants_path, f"../{unit_name}")


def disable_systemd_unit(rootfs: Path, unit_name: str, target_name: str) -> None:
    remove_path(rootfs / "etc" / "systemd" / "system" / f"{target_name}.wants" / unit_name)


def apply_vendor_rootfs_profile(rootfs: Path, profile: str) -> None:
    if profile not in BOOT_PROFILES:
        fail(f"Unsupported rootfs profile: {profile}")

    if not rootfs.exists() or not rootfs.is_dir():
        fail(f"Mounted rootfs directory not found: {rootfs}")

    wsl_unc = parse_wsl_unc_path(rootfs)
    if wsl_unc:
        distro, rootfs_wsl = wsl_unc
        build_dir_wsl = to_wsl_path(SCRIPT_DIR)
        script = [
            "set -e",
            f"ROOT='{rootfs_wsl}'",
            f"BUILD='{build_dir_wsl}'",
            "install -d \"${ROOT}/usr/share/sddm/scripts\" \"${ROOT}/usr/bin\" \"${ROOT}/etc/systemd/system\" \"${ROOT}/etc/sddm.conf.d\"",
            "install -m 0755 \"${BUILD}/vendor_Xsetup.sh\" \"${ROOT}/usr/share/sddm/scripts/Xsetup\"",
        ]
        if profile == "xorg-direct":
            script.extend(
                [
                    "install -m 0755 \"${BUILD}/vendor_porta-x11-direct.sh\" \"${ROOT}/usr/bin/porta-x11-direct\"",
                    "install -m 0755 \"${BUILD}/vendor_porta-x11-session.sh\" \"${ROOT}/usr/bin/porta-x11-session\"",
                    "install -m 0644 \"${BUILD}/vendor_porta-x11-direct.service\" \"${ROOT}/etc/systemd/system/porta-x11-direct.service\"",
                    "mkdir -p \"${ROOT}/etc/systemd/system/multi-user.target.wants\"",
                    "ln -snf ../porta-x11-direct.service \"${ROOT}/etc/systemd/system/multi-user.target.wants/porta-x11-direct.service\"",
                    "rm -f \"${ROOT}/etc/systemd/system/graphical.target.wants/porta-x11-direct.service\"",
                    "ln -snf /dev/null \"${ROOT}/etc/systemd/system/sddm.service\"",
                    "ln -snf /dev/null \"${ROOT}/etc/systemd/system/hdmi-toggle-once.service\"",
                    "rm -f \"${ROOT}/etc/sddm.conf.d/10-porta-x11.conf\"",
                ]
            )
        else:
            script.extend(
                [
                    "install -m 0644 \"${BUILD}/vendor_sddm_x11.conf\" \"${ROOT}/etc/sddm.conf.d/10-porta-x11.conf\"",
                    "[ \"$(readlink \"${ROOT}/etc/systemd/system/sddm.service\" 2>/dev/null || true)\" = /dev/null ] && rm -f \"${ROOT}/etc/systemd/system/sddm.service\" || true",
                    "ln -snf /dev/null \"${ROOT}/etc/systemd/system/hdmi-toggle-once.service\"",
                    "rm -f \"${ROOT}/etc/systemd/system/multi-user.target.wants/porta-x11-direct.service\"",
                    "rm -f \"${ROOT}/etc/systemd/system/graphical.target.wants/porta-x11-direct.service\"",
                ]
            )
        run_wsl_script_as_root("\n".join(script) + "\n", distro=distro)
        print(f"Applied rootfs profile '{profile}' to {rootfs} via WSL")
        return

    xsetup_target = rootfs / "usr" / "share" / "sddm" / "scripts" / "Xsetup"
    write_text_file(
        xsetup_target,
        (SCRIPT_DIR / "vendor_Xsetup.sh").read_text(encoding="utf-8"),
        executable=True,
    )

    if profile == "xorg-direct":
        copy_executable(SCRIPT_DIR / "vendor_porta-x11-direct.sh", rootfs / "usr" / "bin" / "porta-x11-direct")
        copy_executable(SCRIPT_DIR / "vendor_porta-x11-session.sh", rootfs / "usr" / "bin" / "porta-x11-session")
        write_text_file(
            rootfs / "etc" / "systemd" / "system" / "porta-x11-direct.service",
            (SCRIPT_DIR / "vendor_porta-x11-direct.service").read_text(encoding="utf-8"),
        )
        enable_systemd_unit(rootfs, "porta-x11-direct.service", "multi-user.target")
        disable_systemd_unit(rootfs, "porta-x11-direct.service", "graphical.target")
        mask_systemd_unit(rootfs, "sddm.service")
        mask_systemd_unit(rootfs, "hdmi-toggle-once.service")
        remove_path(rootfs / "etc" / "sddm.conf.d" / "10-porta-x11.conf")
    else:
        write_text_file(
            rootfs / "etc" / "sddm.conf.d" / "10-porta-x11.conf",
            (SCRIPT_DIR / "vendor_sddm_x11.conf").read_text(encoding="utf-8"),
        )
        unmask_systemd_unit(rootfs, "sddm.service")
        mask_systemd_unit(rootfs, "hdmi-toggle-once.service")
        disable_systemd_unit(rootfs, "porta-x11-direct.service", "multi-user.target")
        disable_systemd_unit(rootfs, "porta-x11-direct.service", "graphical.target")

    print(f"Applied rootfs profile '{profile}' to {rootfs}")


def align4(value: int) -> int:
    return (value + 3) & ~3


def append_newc_entry(archive: bytearray, name: str, data: bytes, mode: int) -> None:
    name_bytes = name.encode("ascii") + b"\0"
    header = (
        "070701"
        f"{0:08x}"
        f"{mode:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{1:08x}"
        f"{int(time.time()):08x}"
        f"{len(data):08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{0:08x}"
        f"{len(name_bytes):08x}"
        f"{0:08x}"
    ).encode("ascii")
    archive.extend(header)
    archive.extend(name_bytes)
    archive.extend(b"\0" * (align4(len(archive)) - len(archive)))
    archive.extend(data)
    archive.extend(b"\0" * (align4(len(archive)) - len(archive)))


def iter_newc_entries(data: bytes):
    i = 0
    while i + 110 <= len(data):
        if data[i:i + 6] != b"070701":
            fail("Unexpected initrd format while iterating cpio archive")
        fields = [int(data[i + 6 + j * 8:i + 14 + j * 8], 16) for j in range(13)]
        mode = fields[1]
        filesize = fields[6]
        namesize = fields[11]
        name_start = i + 110
        name_end = name_start + namesize
        name = data[name_start:name_end - 1].decode("utf-8", "replace") if namesize else ""
        data_start = align4(name_end)
        data_end = data_start + filesize
        yield name, mode, data[data_start:data_end]
        i = align4(data_end)
        if name == "TRAILER!!!":
            break


def find_newc_archive_end(data: bytes) -> int:
    i = 0
    while i + 110 <= len(data):
        if data[i:i + 6] != b"070701":
            fail("Unexpected initrd format while locating cpio trailer")
        fields = [int(data[i + 6 + j * 8:i + 14 + j * 8], 16) for j in range(13)]
        filesize = fields[6]
        namesize = fields[11]
        name_start = i + 110
        name_end = name_start + namesize
        name = data[name_start:name_end - 1].decode("utf-8", "replace") if namesize else ""
        i = align4(name_end)
        i = align4(i + filesize)
        if name == "TRAILER!!!":
            return i
    fail("Could not find TRAILER!!! in vendor initrd cpio archive")


def extract_newc_entry_data(data: bytes, wanted_name: str) -> tuple[int, bytes]:
    i = 0
    while i + 110 <= len(data):
        if data[i:i + 6] != b"070701":
            i += 1
            continue
        fields = [int(data[i + 6 + j * 8:i + 14 + j * 8], 16) for j in range(13)]
        mode = fields[1]
        filesize = fields[6]
        namesize = fields[11]
        name_start = i + 110
        name_end = name_start + namesize
        name = data[name_start:name_end - 1].decode("utf-8", "replace") if namesize else ""
        data_start = align4(name_end)
        data_end = data_start + filesize
        if name == wanted_name:
            return mode, data[data_start:data_end]
        i = align4(data_end)
    fail(f"Could not find {wanted_name!r} in vendor initrd archive")


def patch_vendor_init_script(data: bytes) -> bytes:
    if data.startswith(b"#!/bin/sh\n"):
        return b"#!/usr/bin/sh\n" + data[len(b"#!/bin/sh\n"):]
    return data


def write_debug_initrd_overlay(target_root: Path, vendor_initrd: Path) -> None:
    edid_data = bytes.fromhex(VENDOR_HDMI_EDID_HEX)

    archive = bytearray()
    append_newc_entry(archive, "lib", b"", 0o040755)
    append_newc_entry(archive, "lib/firmware", b"", 0o040755)
    append_newc_entry(archive, "lib/firmware/edid", b"", 0o040755)
    append_newc_entry(
        archive,
        "lib/firmware/edid/porta-ls060r1sx01.bin",
        edid_data,
        0o100644,
    )
    append_newc_entry(archive, "TRAILER!!!", b"", 0)

    overlay = target_root / "debug" / "porta-initrd.cpio"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    if overlay.exists():
        os.chmod(overlay, stat.S_IWRITE)
    overlay.write_bytes(archive)


def write_merged_vendor_initrd(vendor_initrd: Path, overlay_initrd: Path, dst: Path) -> None:
    vendor_raw = gzip.decompress(vendor_initrd.read_bytes())
    overlay_raw = overlay_initrd.read_bytes()
    merged = bytearray()
    names_written: set[str] = set()

    for name, mode, payload in iter_newc_entries(vendor_raw):
        if name == "TRAILER!!!":
            break
        if name == "init":
            payload = patch_vendor_init_script(payload)
        append_newc_entry(merged, name, payload, mode)
        names_written.add(name)

    for name, mode, payload in iter_newc_entries(overlay_raw):
        if name == "TRAILER!!!":
            break
        if name in names_written and name != "init":
            continue
        append_newc_entry(merged, name, payload, mode)
        names_written.add(name)

    append_newc_entry(merged, "TRAILER!!!", b"", 0)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    dst.write_bytes(gzip.compress(bytes(merged), compresslevel=6, mtime=0))


def patch_vendor_dtb(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        dts_path = temp_dir / "vendor.dts"
        patched_path = temp_dir / "vendor_patched.dts"
        dtb_out = temp_dir / "vendor_patched.dtb"
        script = (
            f"dtc -I dtb -O dts -o '{to_wsl_path(dts_path)}' '{to_wsl_path(src)}'"
        )
        run_wsl_bash(script)

        text = dts_path.read_text(encoding="utf-8", errors="replace")
        if 'bootargs = "' in text:
            text = re.sub(
                r'bootargs = "[^"]*";',
                'bootargs = "";',
                text,
                count=1,
            )
        chosen_match = re.search(r"chosen\s*\{", text)
        if chosen_match and 'stdout-path = "' not in text[text.find("chosen {"):text.find("};", text.find("chosen {"))]:
            insert_at = chosen_match.end()
            text = (
                text[:insert_at]
                + '\n\t\tstdout-path = "serial0:115200n8";'
                + text[insert_at:]
            )
        # Debug bring-up: force single-core boot and avoid PSCI handoff
        # until the vendor kernel can run cleanly under our EFI path.
        text = re.sub(
            r'(\bcpu@[1-7]\s*\{.*?\n)(\s*)(enable-method = "psci";\n)?',
            lambda m: m.group(1) + m.group(2) + 'status = "disabled";\n',
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r'psci\s*\{.*?\n\s*\};\n',
            '',
            text,
            count=1,
            flags=re.DOTALL,
        )
        text = re.sub(
            r'^\s*enable-method = "psci";\n',
            '',
            text,
            flags=re.MULTILINE,
        )

        def find_block_end(text_in: str, open_brace: int) -> int:
            depth = 0
            for index in range(open_brace, len(text_in)):
                char = text_in[index]
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return index
            fail("Unbalanced DTS braces while patching vendor DTB")

        def set_node_status(text_in: str, node_name: str, new_status: str) -> str:
            search_at = 0
            while True:
                node_at = text_in.find(node_name, search_at)
                if node_at < 0:
                    return text_in
                brace_at = text_in.find("{", node_at)
                if brace_at < 0:
                    return text_in
                semi_at = text_in.find(";", node_at, brace_at)
                if semi_at >= 0:
                    search_at = node_at + len(node_name)
                    continue

                block_end = find_block_end(text_in, brace_at)
                block = text_in[node_at:block_end + 1]
                status_re = re.compile(r'(^\s*status\s*=\s*)"[^"]*";', re.MULTILINE)
                if status_re.search(block):
                    block = status_re.sub(rf'\1"{new_status}";', block, count=1)
                else:
                    block = block[:brace_at - node_at + 1] + f'\n\t\tstatus = "{new_status}";' + block[brace_at - node_at + 1:]
                return text_in[:node_at] + block + text_in[block_end + 1:]

        # Keep the boot SD controller alive, but trim unrelated storage
        # paths that currently spam retries and make bring-up harder to read.
        for node_name in (
            "sdmmc@4021000",
            "sdmmc@4022000",
            "sdmmc@4023000",
            "ufs@04520000",
        ):
            text = set_node_status(text, node_name, "disabled")

        patched_path.write_text(text, encoding="utf-8", newline="\n")
        run_wsl_bash(
            f"dtc -I dts -O dtb -o '{to_wsl_path(dtb_out)}' '{to_wsl_path(patched_path)}'"
        )
        copy_file(dtb_out, dst)


def apply_vendor_psci_overlay(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        dtb_out = temp_dir / "vendor_psci_overlayed.dtb"
        copy_file(src, dtb_out)
        dtb_wsl = to_wsl_path(dtb_out)
        run_wsl_bash(
            "\n".join(
                [
                    "set -e",
                    # Keep the vendor DTB binary shape intact. Patch only the
                    # smallest set of properties needed for EFI bring-up.
                    f"fdtput -t s '{dtb_wsl}' /psci compatible porta,disabled-psci 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /psci method none 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /psci status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/idle-states entry-method disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@0 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@100 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@100 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@200 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@200 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@300 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@300 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@400 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@400 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@500 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@500 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@600 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@600 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /cpus/cpu@700 status disabled 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /cpus/cpu@700 enable-method 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/sdmmc@4021000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/sdmmc@4022000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/sdmmc@4023000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/ufs@04520000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/pcie@6000000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /phy_switcher@10 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/twi@7084000/et7304@4e status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/edp0@5720000 status disabled 2>/dev/null || true",
                    f"fdtput -t s '{dtb_wsl}' /soc@3000000/tcon4@5731000 status disabled 2>/dev/null || true",
                    f"fdtput '{dtb_wsl}' /soc@3000000/sdmmc@4020000 no-1-8-v 2>/dev/null || true",
                    f"fdtput -t i '{dtb_wsl}' /soc@3000000/sdmmc@4020000 max-frequency 50000000 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /soc@3000000/sdmmc@4020000 sd-uhs-sdr50 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /soc@3000000/sdmmc@4020000 sd-uhs-ddr50 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /soc@3000000/sdmmc@4020000 sd-uhs-sdr104 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /soc@3000000/sdmmc@4020000 vqmmc18sw-supply 2>/dev/null || true",
                    f"fdtput -d '{dtb_wsl}' /soc@3000000/sdmmc@4020000 vdmmc18sw-supply 2>/dev/null || true",
                ]
            )
        )
        copy_file(dtb_out, dst)


def write_grub_cfg(target_root: Path, profile: str) -> None:
    if profile not in BOOT_PROFILES:
        fail(f"Unsupported boot profile: {profile}")

    run_id = time.strftime("%Y%m%d-%H%M%S")
    profile_banner = profile
    systemd_target = ""
    if profile == "xorg-direct":
        systemd_target = "systemd.unit=multi-user.target "

    cfg = (
        "set pager=0\n"
        "set debug=\n"
        f"echo [grub] vendor linux {profile_banner} boot runid={run_id}\n"
        "linux /vendor/vmlinuz-5.15.147-7-a733 "
        "root=/dev/mmcblk0p3 rootfstype=ext4 rootdelay=2 "
        "console=ttyAS0,115200n8 "
        "rootwait clk_ignore_unused rw "
        "earlycon earlyprintk=sunxi-uart,0x2500000 "
        "keep_bootcon ignore_loglevel loglevel=8 "
        "initcall_debug "
        "drm.edid_fixup=1 "
        "video=HDMI-A-1:1920x1080@60e "
        "consoleblank=0 coherent_pool=2M "
        "irqchip.gicv3_pseudo_nmi=0 no_console_suspend "
        "maxcpus=1 cpuidle.off=1 "
        "initcall_blacklist=sunxi_drm_heap_create,sun50i_cpufreq_init,addr_mgt_driver_init "
        "systemd.show_status=1 "
        "systemd.journald.forward_to_console=1 "
        "systemd.log_target=console systemd.log_level=debug "
        f"{systemd_target}"
        "plymouth.enable=0 "
        f"porta_runid={run_id} "
        "cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory "
        "swapaccount=1 kasan=off\n"
        "echo [grub] linux command done\n"
        "initrd /vendor/initrd-merged.img\n"
        "echo [grub] initrd command done\n"
        "devicetree /dtb/sun60i-a733-cubie-a7z.dtb\n"
        "echo [grub] devicetree command done\n"
        "boot\n"
    )
    path = target_root / "boot" / "grub" / "grub.cfg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cfg, encoding="ascii", newline="\n")


def write_startup_script(target_root: Path) -> None:
    script = (
        "@echo -off\r\n"
        "if exist fs1:\\EFI\\BOOT\\BOOTAA64.EFI then\r\n"
        "  fs1:\\EFI\\BOOT\\BOOTAA64.EFI\r\n"
        "endif\r\n"
        "echo Vendor Linux BOOTAA64.EFI not found on fs1:.\r\n"
    )
    (target_root / "startup.nsh").write_text(script, encoding="ascii", newline="")


def resolve_grubaa64_source(target_root: Path) -> Path:
    candidates = (
        Path("H:/EFI/boot/grubaa64.efi"),
        target_root / "EFI" / "BOOT" / "grubaa64.efi",
        target_root / "EFI" / "BOOT" / "BOOTAA64.EFI",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    fail("grubaa64.efi source not found. Mount the Ubuntu ISO as H: or provide an existing target copy.")


def install_vendor_boot(vendor_boot: Path, target_root: Path, profile: str) -> None:
    required = [
        vendor_boot / "vmlinuz-5.15.147-7-a733",
        vendor_boot / "initrd.img-5.15.147-7-a733",
        vendor_boot / "sun60i-a733-cubie-a7z.dtb",
    ]
    for path in required:
        if not path.exists():
            fail(f"Missing vendor boot asset: {path}")

    iso_root = SCRIPT_DIR.parent / "roms" / "_work" / "mntinspect" / "p2"
    grub_source = SCRIPT_DIR.parent / "roms" / "_work" / "radxa_vendor_boot" / "extlinux.conf"
    _ = grub_source  # placate lint-like readers; not used directly

    grubaa64_source = resolve_grubaa64_source(target_root)

    copy_file(grubaa64_source, target_root / "EFI" / "BOOT" / "BOOTAA64.EFI")
    copy_file(grubaa64_source, target_root / "EFI" / "BOOT" / "grubaa64.efi")
    copy_file(vendor_boot / "vmlinuz-5.15.147-7-a733", target_root / "vendor" / "vmlinuz-5.15.147-7-a733")
    copy_file(vendor_boot / "initrd.img-5.15.147-7-a733", target_root / "vendor" / "initrd.img-5.15.147-7-a733")
    # Keep the vendor DTB intact, but apply a tiny overlay that removes
    # PSCI-driven SMP/idle wiring. The vendor kernel hangs under our EFI
    # path while probing PSCI from DT; using fdtoverlay avoids the
    # full dtc round-trip that broke pinctrl/display behavior earlier.
    apply_vendor_psci_overlay(
        vendor_boot / "sun60i-a733-cubie-a7z.dtb",
        target_root / "dtb" / "sun60i-a733-cubie-a7z.dtb",
    )
    write_debug_initrd_overlay(target_root, target_root / "vendor" / "initrd.img-5.15.147-7-a733")
    write_merged_vendor_initrd(
        target_root / "vendor" / "initrd.img-5.15.147-7-a733",
        target_root / "debug" / "porta-initrd.cpio",
        target_root / "vendor" / "initrd-merged.img",
    )
    write_grub_cfg(target_root, profile)
    write_startup_script(target_root)


def copy_vendor_rootfs(image_path: Path, chunk_mb: int = 16) -> None:
    partition_offset, partition_size = get_partition3_info()
    if partition_size < VENDOR_ROOT_BYTES:
        fail(f"Disk 3 partition 3 is too small: {partition_size} < {VENDOR_ROOT_BYTES}")

    print(f"Vendor rootfs copy: image offset 0x{VENDOR_ROOT_OFFSET:X}, bytes 0x{VENDOR_ROOT_BYTES:X}")
    print(f"Disk 3 p3 offset: 0x{partition_offset:X}, size: 0x{partition_size:X}")

    volume_handles = lock_disk3_volumes()
    disk_handle = open_handle(DISK_PATH, write=True)
    try:
        set_file_pointer(disk_handle, partition_offset)
        chunk_size = chunk_mb * 1024 * 1024
        written_total = 0
        with image_path.open("rb") as src:
            src.seek(VENDOR_ROOT_OFFSET)
            while written_total < VENDOR_ROOT_BYTES:
                remaining = VENDOR_ROOT_BYTES - written_total
                data = src.read(min(chunk_size, remaining))
                if not data:
                    fail("Unexpected EOF while reading vendor image rootfs")
                buffer = ctypes.create_string_buffer(data)
                bytes_written = ctypes.wintypes.DWORD(0)
                ok = k32.WriteFile(disk_handle, buffer, len(data), ctypes.byref(bytes_written), None)
                if not ok or bytes_written.value != len(data):
                    fail(f"WriteFile failed at +0x{written_total:X} (err={k32.GetLastError()})")
                written_total += bytes_written.value
                if written_total % (256 * 1024 * 1024) == 0 or written_total == VENDOR_ROOT_BYTES:
                    print(f"  copied {written_total // (1024 * 1024)} MiB / {VENDOR_ROOT_BYTES // (1024 * 1024)} MiB")
        if not k32.FlushFileBuffers(disk_handle):
            fail(f"FlushFileBuffers failed (err={k32.GetLastError()})")
    finally:
        ioctl(disk_handle, FSCTL_UNLOCK_VOLUME, "Disk unlock")
        k32.CloseHandle(disk_handle)
        unlock_handles(volume_handles)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Radxa vendor Linux rootfs and boot files onto Disk 3.")
    parser.add_argument("--vendor-boot", default=str(DEFAULT_VENDOR_BOOT), help="Directory containing extracted vendor boot assets.")
    parser.add_argument("--vendor-image", help="Raw Radxa disk image used as rootfs source.")
    parser.add_argument("--target", default="F:\\", help="Mounted FAT32 WINSTALL target. Default: F:\\")
    parser.add_argument(
        "--boot-profile",
        choices=BOOT_PROFILES,
        default="xorg-direct",
        help="Boot flow to configure in grub.cfg.",
    )
    parser.add_argument(
        "--rootfs-dir",
        help="Mounted vendor rootfs directory to patch with matching userspace services.",
    )
    parser.add_argument("--skip-rootfs-copy", action="store_true", help="Only refresh EFI/FAT boot files; do not overwrite partition 3.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vendor_boot = normalize_existing_dir(args.vendor_boot)
    target_root = normalize_existing_dir(args.target)
    image_path = resolve_vendor_image_path(args.vendor_image)

    if not args.skip_rootfs_copy:
        copy_vendor_rootfs(image_path)

    install_vendor_boot(vendor_boot, target_root, args.boot_profile)
    if args.rootfs_dir:
        apply_vendor_rootfs_profile(Path(args.rootfs_dir), args.boot_profile)
    else:
        print("  rootfs profile -> unchanged (pass --rootfs-dir to apply userspace service changes)")

    print(f"Installed vendor Linux boot files to: {target_root}")
    print(f"  boot profile -> {args.boot_profile}")
    print(f"  BOOTAA64.EFI -> {target_root / 'EFI' / 'BOOT' / 'BOOTAA64.EFI'}")
    print(f"  vmlinuz      -> {target_root / 'vendor' / 'vmlinuz-5.15.147-7-a733'}")
    print(f"  initrd       -> {target_root / 'vendor' / 'initrd.img-5.15.147-7-a733'}")
    print(f"  merged initrd-> {target_root / 'vendor' / 'initrd-merged.img'}")
    print(f"  dtb          -> {target_root / 'dtb' / 'sun60i-a733-cubie-a7z.dtb'}")
    print(f"  grub.cfg     -> {target_root / 'boot' / 'grub' / 'grub.cfg'}")


if __name__ == "__main__":
    main()
