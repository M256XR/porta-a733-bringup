#!/usr/bin/env python3
"""Install Windows ARM installer boot files onto a Disk 3 FAT32 partition."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_powershell(command: str) -> str:
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def normalize_existing_dir(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"Path does not exist: {path}")
    if not path.is_dir():
        fail(f"Path is not a directory: {path}")
    return path


def autodetect_disk3_esp_root() -> Path:
    command = (
        "Get-Partition -DiskNumber 3 | "
        "Where-Object { $_.GptType -eq '{C12A7328-F81F-11D2-BA4B-00A0C93EC93B}' } | "
        "Get-Volume | Select-Object -ExpandProperty Path"
    )
    path_text = run_powershell(command)
    if not path_text:
        fail("Could not auto-detect Disk 3 ESP")
    return normalize_existing_dir(path_text)


def create_disk3_installer_partition(size_mb: int) -> Path:
    size_bytes = size_mb * 1024 * 1024
    command = (
        "$existing = Get-Partition -DiskNumber 3 | Get-Volume | "
        "Where-Object { $_.FileSystemLabel -eq 'WINSTALL' } | "
        "Select-Object -First 1 -ExpandProperty Path; "
        "if ($existing) { Write-Output $existing; exit 0 }; "
        f"$p = New-Partition -DiskNumber 3 -Size {size_bytes} -AssignDriveLetter; "
        "$v = $p | Format-Volume -FileSystem FAT32 -NewFileSystemLabel 'WINSTALL' "
        "-Confirm:$false -Force; "
        "Write-Output $v.Path"
    )
    path_text = run_powershell(command)
    if not path_text:
        fail("Failed to create or locate Disk 3 WINSTALL partition")
    return normalize_existing_dir(path_text)


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            copy_tree(item, target)
        else:
            copy_file(item, target)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    shutil.copy2(src, dst)


def install_windows_installer(iso_root: Path, target_root: Path, boot_file: str, copy_bootaa64: bool) -> None:
    bootaa64_src = iso_root / boot_file

    required = [
        iso_root / "EFI" / "Microsoft" / "Boot" / "BCD",
        iso_root / "boot" / "boot.sdi",
        iso_root / "sources" / "boot.wim",
    ]
    if copy_bootaa64:
        required.insert(0, bootaa64_src)

    for path in required:
        if not path.exists():
            fail(f"Required installer file not found: {path}")

    copy_tree(iso_root / "EFI" / "Microsoft" / "Boot", target_root / "EFI" / "Microsoft" / "Boot")
    if copy_bootaa64:
        copy_file(bootaa64_src, target_root / "EFI" / "BOOT" / "BOOTAA64.EFI")
    copy_file(iso_root / "boot" / "boot.sdi", target_root / "boot" / "boot.sdi")
    copy_file(iso_root / "sources" / "boot.wim", target_root / "sources" / "boot.wim")


def write_startup_script(target_root: Path, auto_launch_bootaa64: bool) -> None:
    script = (
        "@echo -off\r\n"
        "map -r\r\n"
        "if exist \\EFI\\Microsoft\\Boot\\bootmgfw.efi then\r\n"
        "  \\EFI\\Microsoft\\Boot\\bootmgfw.efi\r\n"
        "endif\r\n"
    )
    if auto_launch_bootaa64:
        script += (
            "if exist \\EFI\\BOOT\\BOOTAA64.EFI then\r\n"
            "  \\EFI\\BOOT\\BOOTAA64.EFI\r\n"
            "endif\r\n"
        )
    else:
        script += (
            "if exist \\EFI\\BOOT\\BOOTAA64.EFI then\r\n"
            "  echo BOOTAA64.EFI exists on the current volume but startup.nsh is not auto-launching it\r\n"
            "endif\r\n"
        )

    for fs_index in range(10):
        script += (
            f"if exist fs{fs_index}:\\EFI\\Microsoft\\Boot\\bootmgfw.efi then\r\n"
            f"  fs{fs_index}:\\EFI\\Microsoft\\Boot\\bootmgfw.efi\r\n"
            "endif\r\n"
        )
    if auto_launch_bootaa64:
        for fs_index in range(10):
            script += (
                f"if exist fs{fs_index}:\\EFI\\BOOT\\BOOTAA64.EFI then\r\n"
                f"  fs{fs_index}:\\EFI\\BOOT\\BOOTAA64.EFI\r\n"
                "endif\r\n"
            )
    script += "echo Windows installer loader not found on current volume or fs0:fs9:.\r\n"
    (target_root / "startup.nsh").write_text(script, encoding="ascii", newline="")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Windows ARM installer files to a Disk 3 FAT32 partition.")
    parser.add_argument("--iso-root", required=True, help="Mounted Windows ISO root, for example F:\\")
    parser.add_argument("--target", help="Mounted target FAT32 root. If omitted, create/use Disk 3 WINSTALL partition.")
    parser.add_argument(
        "--installer-partition-mb",
        type=int,
        default=2048,
        help="Create/use a Disk 3 FAT32 installer partition of this size in MB. Default: 2048",
    )
    parser.add_argument(
        "--boot-file",
        default=r"EFI\BOOT\BOOTAA64.EFI",
        help=r"EFI file inside the mounted ISO to copy as EFI\BOOT\BOOTAA64.EFI. Default: EFI\BOOT\BOOTAA64.EFI",
    )
    parser.add_argument(
        "--skip-bootaa64",
        action="store_true",
        help=(
            r"Do not install EFI\BOOT\BOOTAA64.EFI. Useful for Shell-driven bring-up, "
            r"where the firmware would otherwise auto-run the removable-media path before startup.nsh."
        ),
    )
    parser.add_argument(
        "--with-bootaa64-fallback",
        action="store_true",
        help=r"Let startup.nsh auto-launch EFI\BOOT\BOOTAA64.EFI after bootmgfw. Default keeps BOOTAA64 present but does not invoke it from startup.nsh.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    iso_root = normalize_existing_dir(args.iso_root)

    target_root = normalize_existing_dir(args.target) if args.target else create_disk3_installer_partition(args.installer_partition_mb)
    install_windows_installer(iso_root, target_root, args.boot_file, copy_bootaa64=not args.skip_bootaa64)
    write_startup_script(target_root, auto_launch_bootaa64=args.with_bootaa64_fallback)

    print(f"Installed Windows installer files to: {target_root}")
    if args.skip_bootaa64:
        print("  BOOTAA64.EFI skipped (--skip-bootaa64)")
    else:
        print(f"  BOOTAA64.EFI <- {args.boot_file}")
        print(f"  BOOTAA64.EFI -> {target_root / 'EFI' / 'BOOT' / 'BOOTAA64.EFI'}")
    print(f"  boot.sdi     -> {target_root / 'boot' / 'boot.sdi'}")
    print(f"  boot.wim     -> {target_root / 'sources' / 'boot.wim'}")
    print(f"  startup.nsh  -> {target_root / 'startup.nsh'}")
    if not args.skip_bootaa64:
        print("  Note: firmware may still auto-run EFI\\BOOT\\BOOTAA64.EFI before Shell. Use --skip-bootaa64 when debugging the 0x102000 AllocateAddress path.")


if __name__ == "__main__":
    main()
