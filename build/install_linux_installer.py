#!/usr/bin/env python3
"""Install a minimal Ubuntu ARM64 EFI boot set onto Disk 3 WINSTALL FAT32."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

from pyfdt.pyfdt import (
    Fdt,
    FdtBlobParse,
    FdtNode,
    FdtProperty,
    FdtPropertyStrings,
    FdtPropertyWords,
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


def normalize_existing_dir(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"Path does not exist: {path}")
    if not path.is_dir():
        fail(f"Path is not a directory: {path}")
    return path


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


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    shutil.copy2(src, dst)


def copy_tree_files(src_root: Path, dst_root: Path) -> None:
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        relative = src.relative_to(src_root)
        copy_file(src, dst_root / relative)


def align4(value: int) -> int:
    return (value + 3) & ~3


def append_newc_entry(archive: bytearray, name: str, data: bytes, mode: int) -> None:
    name_bytes = name.encode("ascii") + b"\0"
    header = (
        "070701"
        f"{0:08x}"  # ino
        f"{mode:08x}"
        f"{0:08x}"  # uid
        f"{0:08x}"  # gid
        f"{1:08x}"  # nlink
        f"{int(time.time()):08x}"
        f"{len(data):08x}"
        f"{0:08x}"  # devmajor
        f"{0:08x}"  # devminor
        f"{0:08x}"  # rdevmajor
        f"{0:08x}"  # rdevminor
        f"{len(name_bytes):08x}"
        f"{0:08x}"  # check
    ).encode("ascii")
    archive.extend(header)
    archive.extend(name_bytes)
    archive.extend(b"\0" * (align4(len(archive)) - len(archive)))
    archive.extend(data)
    archive.extend(b"\0" * (align4(len(archive)) - len(archive)))


def write_debug_initrd_overlay(target_root: Path) -> None:
    script = (
        "#!/bin/sh\n"
        "PATH=/usr/sbin:/usr/bin:/sbin:/bin\n"
        "export PATH\n"
        "exec >/dev/console 2>&1\n"
        "log(){ echo \"[porta-init] $*\"; echo \"[porta-init] $*\" >/dev/kmsg 2>/dev/null || true; }\n"
        "log_cmd(){\n"
        "  \"$@\" 2>&1 | while IFS= read -r line; do log \"$line\"; done\n"
        "}\n"
        "log_console(){\n"
        "  echo \"[porta-init] $*\"\n"
        "}\n"
        "log_cmd_console(){\n"
        "  \"$@\" 2>&1 | while IFS= read -r line; do log_console \"$line\"; done\n"
        "}\n"
        "tune_mmc_queue(){\n"
        "  tries=0\n"
        "  while [ \"$tries\" -lt 180 ]; do\n"
        "    if [ -d /sys/block/mmcblk0/queue ]; then\n"
        "      for attr in discard_max_bytes write_zeroes_max_bytes write_same_max_bytes max_write_zeroes_sectors max_discard_sectors; do\n"
        "        if [ -e \"/sys/block/mmcblk0/queue/$attr\" ]; then\n"
        "          before=$(cat \"/sys/block/mmcblk0/queue/$attr\")\n"
        "          log \"queue-$attr-before=$before\"\n"
        "          echo 0 > \"/sys/block/mmcblk0/queue/$attr\" || true\n"
        "          after=$(cat \"/sys/block/mmcblk0/queue/$attr\")\n"
        "          log \"queue-$attr-after=$after\"\n"
        "        fi\n"
        "      done\n"
        "      for comm in /proc/[0-9]*/comm; do\n"
        "        [ -r \"$comm\" ] || continue\n"
        "        pid=${comm#/proc/}\n"
        "        pid=${pid%/comm}\n"
        "        name=$(cat \"$comm\")\n"
        "        if [ \"$name\" = \"mkfs.ext4\" ] && [ ! -e \"/tmp/porta-mkfs-$pid\" ]; then\n"
        "          : > \"/tmp/porta-mkfs-$pid\"\n"
        "          log \"mkfs-found pid=$pid\"\n"
        "          [ -r \"/proc/$pid/cmdline\" ] && tr '\\000' ' ' < \"/proc/$pid/cmdline\" | while IFS= read -r line; do log \"mkfs-cmdline $line\"; done\n"
        "        fi\n"
        "      done\n"
        "      return 0\n"
        "    fi\n"
        "    tries=$((tries + 1))\n"
        "    sleep 1\n"
        "  done\n"
        "  log 'mmc queue not found before timeout'\n"
        "}\n"
        "watch_display_state(){\n"
        "  tries=0\n"
        "  while [ \"$tries\" -lt 80 ]; do\n"
        "    if [ -d /sys/class/drm ]; then\n"
        "      have_cards=0\n"
        "      for node in /sys/class/drm/card*; do\n"
        "        [ -e \"$node\" ] || continue\n"
        "        have_cards=1\n"
        "        break\n"
        "      done\n"
        "      if [ \"$have_cards\" -eq 1 ]; then\n"
        "        log_console drm-class-begin\n"
        "        for entry in /sys/class/drm/*; do\n"
        "          [ -e \"$entry\" ] || continue\n"
        "          log_console \"drm-entry $entry\"\n"
        "        done\n"
        "        for item in /sys/class/drm/*/status /sys/class/drm/*/enabled /sys/class/drm/*/modes; do\n"
        "          [ -r \"$item\" ] || continue\n"
        "          log_console \"drm-node $item\"\n"
        "          while IFS= read -r line; do log_console \"$line\"; done < \"$item\"\n"
        "        done\n"
        "        log_console drm-dmesg-begin\n"
        "        if command -v dmesg >/dev/null 2>&1 && command -v grep >/dev/null 2>&1 && command -v tail >/dev/null 2>&1; then\n"
        "          dmesg | grep -Ei 'drm|hdmi|tcon|mixer|sun4i|dw-hdmi|simpledrm|fbcon' | tail -n 160 | while IFS= read -r line; do log_console \"$line\"; done\n"
        "        else\n"
        "          log_console drm-dmesg-tools-missing\n"
        "        fi\n"
        "        log_console drm-dmesg-end\n"
        "        return 0\n"
        "      fi\n"
        "      if [ $((tries % 10)) -eq 0 ]; then\n"
        "        log_console drm-wait-cards\n"
        "        for entry in /sys/class/drm/*; do\n"
        "          [ -e \"$entry\" ] || continue\n"
        "          log_console \"drm-wait-entry $entry\"\n"
        "        done\n"
        "      fi\n"
        "    fi\n"
        "    tries=$((tries + 1))\n"
        "    sleep 3\n"
        "  done\n"
        "  log_console drm-class-timeout\n"
        "  if [ -d /sys/class/drm ]; then\n"
        "    log_console drm-timeout-class-begin\n"
        "    for entry in /sys/class/drm/*; do\n"
        "      [ -e \"$entry\" ] || continue\n"
        "      log_console \"drm-timeout-entry $entry\"\n"
        "    done\n"
        "    log_console drm-timeout-class-end\n"
        "  fi\n"
        "  if [ -d /sys/class/graphics ]; then\n"
        "    log_console graphics-class-begin\n"
        "    for entry in /sys/class/graphics/*; do\n"
        "      [ -e \"$entry\" ] || continue\n"
        "      log_console \"graphics-entry $entry\"\n"
        "    done\n"
        "    log_console graphics-class-end\n"
        "  fi\n"
        "  if [ -r /proc/fb ]; then\n"
        "    log_console proc-fb-begin\n"
        "    while IFS= read -r line; do log_console \"$line\"; done < /proc/fb\n"
        "    log_console proc-fb-end\n"
        "  fi\n"
        "  log_console dev-fb-begin\n"
        "  for entry in /dev/dri /dev/dri/* /dev/fb*; do\n"
        "    [ -e \"$entry\" ] || continue\n"
        "    log_console \"dev-entry $entry\"\n"
        "  done\n"
        "  log_console dev-fb-end\n"
        "  log_console platform-drivers-begin\n"
        "  for drv in /sys/bus/platform/drivers/*; do\n"
        "    [ -d \"$drv\" ] || continue\n"
        "    case \"$drv\" in\n"
        "      *drm*|*hdmi*|*tcon*|*mixer*) ;;\n"
        "      *) continue ;;\n"
        "    esac\n"
        "    log_console \"platform-driver $drv\"\n"
        "    for entry in \"$drv\"/*; do\n"
        "      [ -e \"$entry\" ] || continue\n"
        "      log_console \"platform-entry $entry\"\n"
        "    done\n"
        "  done\n"
        "  log_console platform-drivers-end\n"
        "  log_console modules-begin\n"
        "  for mod in /sys/module/*; do\n"
        "    [ -d \"$mod\" ] || continue\n"
        "    case \"$mod\" in\n"
        "      *drm*|*hdmi*|*tcon*|*mixer*) log_console \"module-entry $mod\" ;;\n"
        "    esac\n"
        "  done\n"
        "  log_console modules-end\n"
        "  log_console platform-devices-begin\n"
        "  for dev in /sys/bus/platform/devices/*drm* /sys/bus/platform/devices/*hdmi* /sys/bus/platform/devices/*tcon* /sys/bus/platform/devices/*mixer*; do\n"
        "    [ -e \"$dev\" ] || continue\n"
        "    log_console \"platform-device $dev\"\n"
        "    [ -L \"$dev/driver\" ] && log_console \"platform-driver-link $(readlink \"$dev/driver\")\"\n"
        "  done\n"
        "  log_console platform-devices-end\n"
        "  log_console drm-timeout-dmesg-begin\n"
        "  if [ -x /bin/dmesg ] && [ -x /bin/grep ] && [ -x /usr/bin/tail ]; then\n"
        "    /bin/dmesg | /bin/grep -Ei 'drm|hdmi|tcon|mixer|sun4i|dw-hdmi|simpledrm|fbcon|framebuffer' | /usr/bin/tail -n 200 | while IFS= read -r line; do log_console \"$line\"; done\n"
        "  elif [ -x /bin/dmesg ]; then\n"
        "    /bin/dmesg | while IFS= read -r line; do case \"$line\" in *drm*|*DRM*|*hdmi*|*tcon*|*mixer*|*sun4i*|*fbcon*|*framebuffer*) log_console \"$line\";; esac; done\n"
        "  else\n"
        "    log_console drm-dmesg-tools-missing\n"
        "  fi\n"
        "  log_console drm-timeout-dmesg-end\n"
        "}\n"
        "log entered\n"
        "mkdir -p /dev /proc /sys\n"
        "log mount-dev-begin\n"
        "log_cmd mount -t devtmpfs devtmpfs /dev\n"
        "log mount-proc-begin\n"
        "log_cmd mount -t proc proc /proc\n"
        "log mount-sys-begin\n"
        "log_cmd mount -t sysfs sysfs /sys\n"
        "log cmdline-begin\n"
        "log_cmd cat /proc/cmdline\n"
        "log partitions-begin\n"
        "log_cmd cat /proc/partitions\n"
        "tune_mmc_queue &\n"
        "watch_display_state &\n"
        "log handoff-to-init\n"
        "exec /init \"$@\"\n"
    ).encode("ascii")

    archive = bytearray()
    append_newc_entry(archive, "debug", b"", 0o040755)
    append_newc_entry(archive, "debug/porta-preinit", script, 0o100755)
    append_newc_entry(archive, "TRAILER!!!", b"", 0)

    overlay = target_root / "debug" / "porta-initrd.cpio"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    if overlay.exists():
        os.chmod(overlay, stat.S_IWRITE)
    overlay.write_bytes(archive)


def copy_dtb_with_memreserve(src: Path, dst: Path, address: int, size: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as infile:
        fdt = FdtBlobParse(infile).to_fdt()

    entries = list(fdt.reserve_entries or [])
    if not any(entry.get("address") == address and entry.get("size") == size for entry in entries):
        entries.append({"address": address, "size": size})
        fdt.add_reserve_entries(entries)

    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    dst.write_bytes(fdt.to_dtb())


def build_minimal_linux_dtb(address: int, size: int) -> bytes:
    gic_phandle = 1
    osc24m_phandle = 2
    osc32k_phandle = 3
    apbclk_phandle = 4
    mmc0_pins_phandle = 5
    reg_vcc_3v3_phandle = 6
    disp_bus_clk_phandle = 7
    disp_mod_clk_phandle = 8
    mixer_bus_clk_phandle = 9
    mixer_mod_clk_phandle = 10
    tcon_bus_clk_phandle = 11
    tcon_tv_mod_clk_phandle = 12
    hdmi_bus_clk_phandle = 13
    hdmi_slow_clk_phandle = 14
    hdmi_tmds_clk_phandle = 15
    hdmi_phy_phandle = 16
    mixer0_phandle = 17
    tcon_top_phandle = 18
    hdmi_con_in_phandle = 19
    mixer0_out_ep_phandle = 20
    tcon_top_mixer0_in_ep_phandle = 21
    tcon_top_mixer0_out_tcon_tv_ep_phandle = 22
    tcon_tv_in_ep_phandle = 23
    tcon_tv_out_ep_phandle = 24
    tcon_top_hdmi_in_tcon_tv_ep_phandle = 25
    tcon_top_hdmi_out_hdmi_ep_phandle = 26
    hdmi_in_tcon_top_ep_phandle = 27
    hdmi_out_con_ep_phandle = 28
    iosc_phandle = 29
    ccu_phandle = 30
    hdmi_pins_phandle = 31
    display_clocks_phandle = 32

    root = FdtNode("/")
    root.append(FdtPropertyStrings("model", ["Radxa Cubie A7Z"]))
    root.append(FdtPropertyStrings("compatible", ["radxa,cubie-a7z", "allwinner,sun60i-a733"]))
    root.append(FdtPropertyWords("interrupt-parent", [gic_phandle]))
    root.append(FdtPropertyWords("#address-cells", [2]))
    root.append(FdtPropertyWords("#size-cells", [2]))

    aliases = FdtNode("aliases")
    aliases.append(FdtPropertyStrings("serial0", ["/soc@0/serial@2500000"]))
    aliases.append(FdtPropertyStrings("mmc0", ["/soc@0/mmc@4020000"]))
    root.append(aliases)

    connector = FdtNode("connector")
    connector.append(FdtPropertyStrings("compatible", ["hdmi-connector"]))
    connector.append(FdtPropertyStrings("type", ["a"]))
    connector_port = FdtNode("port")
    hdmi_con_in = FdtNode("endpoint")
    hdmi_con_in.append(FdtPropertyWords("phandle", [hdmi_con_in_phandle]))
    hdmi_con_in.append(FdtPropertyWords("linux,phandle", [hdmi_con_in_phandle]))
    hdmi_con_in.append(FdtPropertyWords("remote-endpoint", [hdmi_out_con_ep_phandle]))
    connector_port.append(hdmi_con_in)
    connector.append(connector_port)
    root.append(connector)

    de = FdtNode("display-engine")
    de.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-display-engine"]))
    de.append(FdtPropertyWords("allwinner,pipelines", [mixer0_phandle]))
    de.append(FdtPropertyStrings("status", ["okay"]))
    root.append(de)

    chosen = FdtNode("chosen")
    chosen.append(FdtPropertyStrings("stdout-path", ["/soc@0/serial@2500000:115200n8"]))
    root.append(chosen)

    memory = FdtNode("memory@40000000")
    memory.append(FdtPropertyStrings("device_type", ["memory"]))
    memory.append(FdtPropertyWords("reg", [0x0, 0x40000000, 0x0, 0x40000000]))
    root.append(memory)

    osc24m = FdtNode("osc24M-clk")
    osc24m.append(FdtPropertyWords("#clock-cells", [0]))
    osc24m.append(FdtPropertyWords("phandle", [osc24m_phandle]))
    osc24m.append(FdtPropertyWords("linux,phandle", [osc24m_phandle]))
    osc24m.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    osc24m.append(FdtPropertyWords("clock-frequency", [24000000]))
    osc24m.append(FdtPropertyStrings("clock-output-names", ["osc24M"]))
    root.append(osc24m)

    osc32k = FdtNode("osc32k-clk")
    osc32k.append(FdtPropertyWords("#clock-cells", [0]))
    osc32k.append(FdtPropertyWords("phandle", [osc32k_phandle]))
    osc32k.append(FdtPropertyWords("linux,phandle", [osc32k_phandle]))
    osc32k.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    osc32k.append(FdtPropertyWords("clock-frequency", [32768]))
    osc32k.append(FdtPropertyStrings("clock-output-names", ["osc32k"]))
    root.append(osc32k)

    iosc = FdtNode("iosc-clk")
    iosc.append(FdtPropertyWords("#clock-cells", [0]))
    iosc.append(FdtPropertyWords("phandle", [iosc_phandle]))
    iosc.append(FdtPropertyWords("linux,phandle", [iosc_phandle]))
    iosc.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    iosc.append(FdtPropertyWords("clock-frequency", [16000000]))
    iosc.append(FdtPropertyStrings("clock-output-names", ["iosc"]))
    root.append(iosc)

    apbclk = FdtNode("apb-clk")
    apbclk.append(FdtPropertyWords("#clock-cells", [0]))
    apbclk.append(FdtPropertyWords("phandle", [apbclk_phandle]))
    apbclk.append(FdtPropertyWords("linux,phandle", [apbclk_phandle]))
    apbclk.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    apbclk.append(FdtPropertyWords("clock-frequency", [100000000]))
    apbclk.append(FdtPropertyStrings("clock-output-names", ["apbclk"]))
    root.append(apbclk)

    reg_vcc_3v3 = FdtNode("reg_vcc_3v3")
    reg_vcc_3v3.append(FdtPropertyWords("phandle", [reg_vcc_3v3_phandle]))
    reg_vcc_3v3.append(FdtPropertyWords("linux,phandle", [reg_vcc_3v3_phandle]))
    reg_vcc_3v3.append(FdtPropertyStrings("compatible", ["regulator-fixed"]))
    reg_vcc_3v3.append(FdtPropertyStrings("regulator-name", ["vcc-3v3"]))
    reg_vcc_3v3.append(FdtPropertyWords("regulator-min-microvolt", [3300000]))
    reg_vcc_3v3.append(FdtPropertyWords("regulator-max-microvolt", [3300000]))
    reg_vcc_3v3.append(FdtProperty("regulator-always-on"))
    reg_vcc_3v3.append(FdtProperty("regulator-boot-on"))
    root.append(reg_vcc_3v3)

    disp_bus_clk = FdtNode("disp-bus-clk")
    disp_bus_clk.append(FdtPropertyWords("#clock-cells", [0]))
    disp_bus_clk.append(FdtPropertyWords("phandle", [disp_bus_clk_phandle]))
    disp_bus_clk.append(FdtPropertyWords("linux,phandle", [disp_bus_clk_phandle]))
    disp_bus_clk.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    disp_bus_clk.append(FdtPropertyWords("clock-frequency", [300000000]))
    disp_bus_clk.append(FdtPropertyStrings("clock-output-names", ["disp-bus"]))
    root.append(disp_bus_clk)

    disp_mod_clk = FdtNode("disp-mod-clk")
    disp_mod_clk.append(FdtPropertyWords("#clock-cells", [0]))
    disp_mod_clk.append(FdtPropertyWords("phandle", [disp_mod_clk_phandle]))
    disp_mod_clk.append(FdtPropertyWords("linux,phandle", [disp_mod_clk_phandle]))
    disp_mod_clk.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    disp_mod_clk.append(FdtPropertyWords("clock-frequency", [600000000]))
    disp_mod_clk.append(FdtPropertyStrings("clock-output-names", ["disp-mod"]))
    root.append(disp_mod_clk)

    mixer_bus_clk = FdtNode("mixer-bus-clk")
    mixer_bus_clk.append(FdtPropertyWords("#clock-cells", [0]))
    mixer_bus_clk.append(FdtPropertyWords("phandle", [mixer_bus_clk_phandle]))
    mixer_bus_clk.append(FdtPropertyWords("linux,phandle", [mixer_bus_clk_phandle]))
    mixer_bus_clk.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    mixer_bus_clk.append(FdtPropertyWords("clock-frequency", [300000000]))
    mixer_bus_clk.append(FdtPropertyStrings("clock-output-names", ["mixer-bus"]))
    root.append(mixer_bus_clk)

    mixer_mod_clk = FdtNode("mixer-mod-clk")
    mixer_mod_clk.append(FdtPropertyWords("#clock-cells", [0]))
    mixer_mod_clk.append(FdtPropertyWords("phandle", [mixer_mod_clk_phandle]))
    mixer_mod_clk.append(FdtPropertyWords("linux,phandle", [mixer_mod_clk_phandle]))
    mixer_mod_clk.append(FdtPropertyStrings("compatible", ["fixed-clock"]))
    mixer_mod_clk.append(FdtPropertyWords("clock-frequency", [600000000]))
    mixer_mod_clk.append(FdtPropertyStrings("clock-output-names", ["mixer-mod"]))
    root.append(mixer_mod_clk)

    cpus = FdtNode("cpus")
    cpus.append(FdtPropertyWords("#address-cells", [1]))
    cpus.append(FdtPropertyWords("#size-cells", [0]))
    cpu0 = FdtNode("cpu@0")
    cpu0.append(FdtPropertyStrings("compatible", ["arm,cortex-a55"]))
    cpu0.append(FdtPropertyStrings("device_type", ["cpu"]))
    cpu0.append(FdtPropertyWords("reg", [0x000]))
    cpus.append(cpu0)
    root.append(cpus)

    timer = FdtNode("timer")
    timer.append(FdtPropertyStrings("compatible", ["arm,armv8-timer"]))
    timer.append(FdtProperty("arm,no-tick-in-suspend"))
    timer.append(FdtPropertyWords("interrupts", [1, 13, 4, 1, 14, 4, 1, 11, 4, 1, 10, 4]))
    root.append(timer)

    soc = FdtNode("soc@0")
    soc.append(FdtPropertyStrings("compatible", ["simple-bus"]))
    soc.append(FdtPropertyWords("#address-cells", [1]))
    soc.append(FdtPropertyWords("#size-cells", [1]))
    soc.append(FdtPropertyWords("ranges", [0x0, 0x0, 0x0, 0x40000000]))

    uart0 = FdtNode("serial@2500000")
    uart0.append(FdtPropertyStrings("compatible", ["snps,dw-apb-uart"]))
    uart0.append(FdtPropertyWords("reg", [0x02500000, 0x1000]))
    uart0.append(FdtPropertyWords("interrupts", [0, 2, 4]))
    uart0.append(FdtPropertyWords("reg-shift", [2]))
    uart0.append(FdtPropertyWords("reg-io-width", [4]))
    uart0.append(FdtPropertyWords("clock-frequency", [24000000]))
    uart0.append(FdtPropertyWords("current-speed", [115200]))
    uart0.append(FdtPropertyStrings("status", ["okay"]))
    soc.append(uart0)

    pio = FdtNode("pinctrl@2000000")
    pio.append(FdtPropertyStrings("compatible", ["allwinner,sun60i-a733-pinctrl", "allwinner,sun20i-d1-pinctrl"]))
    pio.append(FdtPropertyStrings("status", ["okay"]))
    pio.append(FdtPropertyWords("reg", [0x02000000, 0x2000]))
    pio.append(FdtPropertyWords("interrupts", [0, 69, 4, 0, 71, 4, 0, 73, 4, 0, 75, 4, 0, 77, 4, 0, 79, 4, 0, 81, 4, 0, 83, 4, 0, 85, 4, 0, 87, 4]))
    pio.append(FdtPropertyWords("clocks", [apbclk_phandle, osc24m_phandle, osc32k_phandle]))
    pio.append(FdtPropertyStrings("clock-names", ["apb", "hosc", "losc"]))
    pio.append(FdtProperty("gpio-controller"))
    pio.append(FdtPropertyWords("#gpio-cells", [3]))
    pio.append(FdtProperty("interrupt-controller"))
    pio.append(FdtPropertyWords("#interrupt-cells", [3]))

    mmc0_pins = FdtNode("mmc0-pins")
    mmc0_pins.append(FdtPropertyWords("phandle", [mmc0_pins_phandle]))
    mmc0_pins.append(FdtPropertyWords("linux,phandle", [mmc0_pins_phandle]))
    mmc0_pins.append(FdtPropertyStrings("pins", ["PF0", "PF1", "PF2", "PF3", "PF4", "PF5"]))
    mmc0_pins.append(FdtPropertyWords("allwinner,pinmux", [2]))
    mmc0_pins.append(FdtPropertyStrings("function", ["mmc0"]))
    mmc0_pins.append(FdtPropertyWords("drive-strength", [30]))
    mmc0_pins.append(FdtProperty("bias-pull-up"))
    pio.append(mmc0_pins)
    soc.append(pio)

    gic = FdtNode("interrupt-controller@3400000")
    gic.append(FdtPropertyStrings("compatible", ["arm,gic-v3"]))
    gic.append(FdtPropertyWords("phandle", [gic_phandle]))
    gic.append(FdtPropertyWords("linux,phandle", [gic_phandle]))
    gic.append(FdtPropertyWords("#address-cells", [2]))
    gic.append(FdtPropertyWords("#interrupt-cells", [3]))
    gic.append(FdtPropertyWords("#size-cells", [2]))
    gic.append(FdtProperty("ranges"))
    gic.append(FdtProperty("interrupt-controller"))
    gic.append(FdtPropertyWords("reg", [0x03400000, 0x10000, 0x03460000, 0x100000]))
    gic.append(FdtPropertyWords("interrupts", [1, 9, 4]))
    gic.append(FdtProperty("dma-noncoherent"))
    soc.append(gic)

    ccu = FdtNode("clock@3001000")
    ccu.append(FdtPropertyWords("phandle", [ccu_phandle]))
    ccu.append(FdtPropertyWords("linux,phandle", [ccu_phandle]))
    ccu.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-ccu"]))
    ccu.append(FdtPropertyStrings("status", ["okay"]))
    ccu.append(FdtPropertyWords("reg", [0x03001000, 0x1000]))
    ccu.append(FdtPropertyWords("clocks", [osc24m_phandle, osc32k_phandle, iosc_phandle]))
    ccu.append(FdtPropertyStrings("clock-names", ["hosc", "losc", "iosc"]))
    ccu.append(FdtPropertyWords("#clock-cells", [1]))
    ccu.append(FdtPropertyWords("#reset-cells", [1]))
    soc.append(ccu)

    de_bus = FdtNode("bus@5000000")
    de_bus.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-de3", "allwinner,sun50i-a64-de2"]))
    de_bus.append(FdtPropertyStrings("status", ["okay"]))
    de_bus.append(FdtPropertyWords("reg", [0x05000000, 0x400000]))
    de_bus.append(FdtPropertyWords("#address-cells", [1]))
    de_bus.append(FdtPropertyWords("#size-cells", [1]))
    de_bus.append(FdtPropertyWords("ranges", [0x0, 0x05000000, 0x400000]))

    display_clocks = FdtNode("clock@0")
    display_clocks.append(FdtPropertyWords("phandle", [display_clocks_phandle]))
    display_clocks.append(FdtPropertyWords("linux,phandle", [display_clocks_phandle]))
    display_clocks.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-de3-clk"]))
    display_clocks.append(FdtPropertyStrings("status", ["okay"]))
    display_clocks.append(FdtPropertyWords("reg", [0x0, 0x10000]))
    display_clocks.append(FdtPropertyWords("clocks", [ccu_phandle, 29, ccu_phandle, 30]))
    display_clocks.append(FdtPropertyStrings("clock-names", ["mod", "bus"]))
    display_clocks.append(FdtPropertyWords("resets", [ccu_phandle, 1]))
    display_clocks.append(FdtPropertyWords("#clock-cells", [1]))
    display_clocks.append(FdtPropertyWords("#reset-cells", [1]))
    de_bus.append(display_clocks)

    mmc0 = FdtNode("mmc@4020000")
    mmc0.append(FdtPropertyStrings("compatible", ["allwinner,sun20i-d1-mmc", "allwinner,sun60i-a733-mmc"]))
    mmc0.append(FdtPropertyStrings("status", ["okay"]))
    mmc0.append(FdtPropertyWords("reg", [0x04020000, 0x1000]))
    mmc0.append(FdtPropertyWords("interrupts", [0, 161, 4]))
    mmc0.append(FdtPropertyWords("clocks", [apbclk_phandle, osc24m_phandle]))
    mmc0.append(FdtPropertyStrings("clock-names", ["ahb", "mmc"]))
    mmc0.append(FdtPropertyStrings("pinctrl-names", ["default"]))
    mmc0.append(FdtPropertyWords("pinctrl-0", [mmc0_pins_phandle]))
    mmc0.append(FdtPropertyWords("vmmc-supply", [reg_vcc_3v3_phandle]))
    mmc0.append(FdtPropertyWords("voltage-ranges", [3300, 3300]))
    mmc0.append(FdtPropertyWords("bus-width", [4]))
    mmc0.append(FdtProperty("broken-cd"))
    mmc0.append(FdtProperty("disable-wp"))
    mmc0.append(FdtPropertyWords("max-frequency", [50000000]))
    mmc0.append(FdtPropertyWords("#address-cells", [1]))
    mmc0.append(FdtPropertyWords("#size-cells", [0]))
    mmc0.append(FdtProperty("cap-sd-highspeed"))
    soc.append(mmc0)

    mixer0 = FdtNode("mixer@100000")
    mixer0.append(FdtPropertyWords("phandle", [mixer0_phandle]))
    mixer0.append(FdtPropertyWords("linux,phandle", [mixer0_phandle]))
    mixer0.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-de3-mixer-0"]))
    mixer0.append(FdtPropertyStrings("status", ["okay"]))
    mixer0.append(FdtPropertyWords("reg", [0x100000, 0x100000]))
    mixer0.append(FdtPropertyWords("clocks", [display_clocks_phandle, 0, display_clocks_phandle, 6]))
    mixer0.append(FdtPropertyStrings("clock-names", ["bus", "mod"]))
    mixer0.append(FdtPropertyWords("resets", [display_clocks_phandle, 0]))
    mixer_ports = FdtNode("ports")
    mixer_ports.append(FdtPropertyWords("#address-cells", [1]))
    mixer_ports.append(FdtPropertyWords("#size-cells", [0]))
    mixer0_out = FdtNode("port@1")
    mixer0_out.append(FdtPropertyWords("reg", [1]))
    mixer0_out_ep = FdtNode("endpoint")
    mixer0_out_ep.append(FdtPropertyWords("phandle", [mixer0_out_ep_phandle]))
    mixer0_out_ep.append(FdtPropertyWords("linux,phandle", [mixer0_out_ep_phandle]))
    mixer0_out_ep.append(FdtPropertyWords("remote-endpoint", [tcon_top_mixer0_in_ep_phandle]))
    mixer0_out.append(mixer0_out_ep)
    mixer_ports.append(mixer0_out)
    mixer0.append(mixer_ports)
    de_bus.append(mixer0)
    soc.append(de_bus)

    tcon_top = FdtNode("tcon-top@5501000")
    tcon_top.append(FdtPropertyWords("phandle", [tcon_top_phandle]))
    tcon_top.append(FdtPropertyWords("linux,phandle", [tcon_top_phandle]))
    tcon_top.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-tcon-top", "allwinner,sun20i-d1-tcon-top"]))
    tcon_top.append(FdtPropertyStrings("status", ["okay"]))
    tcon_top.append(FdtPropertyWords("reg", [0x05501000, 0x1000]))
    tcon_top.append(FdtPropertyWords("clocks", [ccu_phandle, 126, ccu_phandle, 129]))
    tcon_top.append(FdtPropertyStrings("clock-names", ["bus", "tcon-tv0"]))
    tcon_top.append(FdtPropertyStrings("clock-output-names", ["tcon-top-tv0"]))
    tcon_top.append(FdtPropertyWords("#clock-cells", [1]))
    tcon_top.append(FdtPropertyWords("resets", [ccu_phandle, 58]))
    tcon_top.append(FdtPropertyStrings("reset-names", ["rst"]))
    tcon_top_ports = FdtNode("ports")
    tcon_top_ports.append(FdtPropertyWords("#address-cells", [1]))
    tcon_top_ports.append(FdtPropertyWords("#size-cells", [0]))
    tcon_top_mixer0_in = FdtNode("port@0")
    tcon_top_mixer0_in.append(FdtPropertyWords("#address-cells", [1]))
    tcon_top_mixer0_in.append(FdtPropertyWords("#size-cells", [0]))
    tcon_top_mixer0_in.append(FdtPropertyWords("reg", [0]))
    tcon_top_mixer0_in_ep = FdtNode("endpoint@0")
    tcon_top_mixer0_in_ep.append(FdtPropertyWords("reg", [0]))
    tcon_top_mixer0_in_ep.append(FdtPropertyWords("phandle", [tcon_top_mixer0_in_ep_phandle]))
    tcon_top_mixer0_in_ep.append(FdtPropertyWords("linux,phandle", [tcon_top_mixer0_in_ep_phandle]))
    tcon_top_mixer0_in_ep.append(FdtPropertyWords("remote-endpoint", [mixer0_out_ep_phandle]))
    tcon_top_mixer0_in.append(tcon_top_mixer0_in_ep)
    tcon_top_ports.append(tcon_top_mixer0_in)
    tcon_top_mixer0_out = FdtNode("port@1")
    tcon_top_mixer0_out.append(FdtPropertyWords("#address-cells", [1]))
    tcon_top_mixer0_out.append(FdtPropertyWords("#size-cells", [0]))
    tcon_top_mixer0_out.append(FdtPropertyWords("reg", [1]))
    tcon_top_mixer0_out_ep = FdtNode("endpoint@2")
    tcon_top_mixer0_out_ep.append(FdtPropertyWords("reg", [2]))
    tcon_top_mixer0_out_ep.append(FdtPropertyWords("phandle", [tcon_top_mixer0_out_tcon_tv_ep_phandle]))
    tcon_top_mixer0_out_ep.append(FdtPropertyWords("linux,phandle", [tcon_top_mixer0_out_tcon_tv_ep_phandle]))
    tcon_top_mixer0_out_ep.append(FdtPropertyWords("remote-endpoint", [tcon_tv_in_ep_phandle]))
    tcon_top_mixer0_out.append(tcon_top_mixer0_out_ep)
    tcon_top_ports.append(tcon_top_mixer0_out)
    tcon_top_hdmi_in = FdtNode("port@4")
    tcon_top_hdmi_in.append(FdtPropertyWords("#address-cells", [1]))
    tcon_top_hdmi_in.append(FdtPropertyWords("#size-cells", [0]))
    tcon_top_hdmi_in.append(FdtPropertyWords("reg", [4]))
    tcon_top_hdmi_in_ep = FdtNode("endpoint@0")
    tcon_top_hdmi_in_ep.append(FdtPropertyWords("reg", [0]))
    tcon_top_hdmi_in_ep.append(FdtPropertyWords("phandle", [tcon_top_hdmi_in_tcon_tv_ep_phandle]))
    tcon_top_hdmi_in_ep.append(FdtPropertyWords("linux,phandle", [tcon_top_hdmi_in_tcon_tv_ep_phandle]))
    tcon_top_hdmi_in_ep.append(FdtPropertyWords("remote-endpoint", [tcon_tv_out_ep_phandle]))
    tcon_top_hdmi_in.append(tcon_top_hdmi_in_ep)
    tcon_top_ports.append(tcon_top_hdmi_in)
    tcon_top_hdmi_out = FdtNode("port@5")
    tcon_top_hdmi_out.append(FdtPropertyWords("reg", [5]))
    tcon_top_hdmi_out_ep = FdtNode("endpoint")
    tcon_top_hdmi_out_ep.append(FdtPropertyWords("phandle", [tcon_top_hdmi_out_hdmi_ep_phandle]))
    tcon_top_hdmi_out_ep.append(FdtPropertyWords("linux,phandle", [tcon_top_hdmi_out_hdmi_ep_phandle]))
    tcon_top_hdmi_out_ep.append(FdtPropertyWords("remote-endpoint", [hdmi_in_tcon_top_ep_phandle]))
    tcon_top_hdmi_out.append(tcon_top_hdmi_out_ep)
    tcon_top_ports.append(tcon_top_hdmi_out)
    tcon_top.append(tcon_top_ports)
    soc.append(tcon_top)

    tcon_tv = FdtNode("lcd-controller@5503000")
    tcon_tv.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-tcon-tv", "allwinner,sun20i-d1-tcon-tv", "allwinner,sun8i-r40-tcon-tv"]))
    tcon_tv.append(FdtPropertyStrings("status", ["okay"]))
    tcon_tv.append(FdtPropertyWords("reg", [0x05503000, 0x1000]))
    tcon_tv.append(FdtPropertyWords("interrupts", [0, 66, 4]))
    tcon_tv.append(FdtPropertyWords("clocks", [ccu_phandle, 130, tcon_top_phandle, 0]))
    tcon_tv.append(FdtPropertyStrings("clock-names", ["ahb", "tcon-ch1"]))
    tcon_tv.append(FdtPropertyWords("resets", [ccu_phandle, 60]))
    tcon_tv.append(FdtPropertyStrings("reset-names", ["lcd"]))
    tcon_tv_ports = FdtNode("ports")
    tcon_tv_ports.append(FdtPropertyWords("#address-cells", [1]))
    tcon_tv_ports.append(FdtPropertyWords("#size-cells", [0]))
    tcon_tv_in = FdtNode("port@0")
    tcon_tv_in.append(FdtPropertyWords("reg", [0]))
    tcon_tv_in_ep = FdtNode("endpoint")
    tcon_tv_in_ep.append(FdtPropertyWords("phandle", [tcon_tv_in_ep_phandle]))
    tcon_tv_in_ep.append(FdtPropertyWords("linux,phandle", [tcon_tv_in_ep_phandle]))
    tcon_tv_in_ep.append(FdtPropertyWords("remote-endpoint", [tcon_top_mixer0_out_tcon_tv_ep_phandle]))
    tcon_tv_in.append(tcon_tv_in_ep)
    tcon_tv_ports.append(tcon_tv_in)
    tcon_tv_out = FdtNode("port@1")
    tcon_tv_out.append(FdtPropertyWords("#address-cells", [1]))
    tcon_tv_out.append(FdtPropertyWords("#size-cells", [0]))
    tcon_tv_out.append(FdtPropertyWords("reg", [1]))
    tcon_tv_out_ep = FdtNode("endpoint@1")
    tcon_tv_out_ep.append(FdtPropertyWords("reg", [1]))
    tcon_tv_out_ep.append(FdtPropertyWords("phandle", [tcon_tv_out_ep_phandle]))
    tcon_tv_out_ep.append(FdtPropertyWords("linux,phandle", [tcon_tv_out_ep_phandle]))
    tcon_tv_out_ep.append(FdtPropertyWords("remote-endpoint", [tcon_top_hdmi_in_tcon_tv_ep_phandle]))
    tcon_tv_out.append(tcon_tv_out_ep)
    tcon_tv_ports.append(tcon_tv_out)
    tcon_tv.append(tcon_tv_ports)
    soc.append(tcon_tv)

    hdmi_phy = FdtNode("hdmi-phy@5530000")
    hdmi_phy.append(FdtPropertyWords("phandle", [hdmi_phy_phandle]))
    hdmi_phy.append(FdtPropertyWords("linux,phandle", [hdmi_phy_phandle]))
    hdmi_phy.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-hdmi-phy"]))
    hdmi_phy.append(FdtPropertyStrings("status", ["okay"]))
    hdmi_phy.append(FdtPropertyWords("reg", [0x05530000, 0x10000]))
    hdmi_phy.append(FdtPropertyWords("clocks", [ccu_phandle, 125, ccu_phandle, 137]))
    hdmi_phy.append(FdtPropertyStrings("clock-names", ["bus", "mod"]))
    hdmi_phy.append(FdtPropertyWords("resets", [ccu_phandle, 56]))
    hdmi_phy.append(FdtPropertyStrings("reset-names", ["phy"]))
    hdmi_phy.append(FdtPropertyWords("#phy-cells", [0]))
    soc.append(hdmi_phy)

    hdmi = FdtNode("hdmi@5520000")
    hdmi.append(FdtPropertyStrings("compatible", ["allwinner,sun50i-h6-dw-hdmi"]))
    hdmi.append(FdtPropertyStrings("status", ["okay"]))
    hdmi.append(FdtPropertyWords("reg", [0x05520000, 0x10000]))
    hdmi.append(FdtPropertyWords("reg-io-width", [1]))
    hdmi.append(FdtPropertyWords("interrupts", [0, 64, 4]))
    hdmi.append(
        FdtPropertyWords(
            "clocks",
            [
                ccu_phandle,
                125,
                ccu_phandle,
                137,
                ccu_phandle,
                123,
                ccu_phandle,
                124,
                ccu_phandle,
                135,
                ccu_phandle,
                136,
            ],
        )
    )
    hdmi.append(FdtPropertyStrings("clock-names", ["iahb", "isfr", "tmds", "cec", "hdcp", "hdcp-bus"]))
    hdmi.append(FdtPropertyWords("resets", [ccu_phandle, 57, ccu_phandle, 62]))
    hdmi.append(FdtPropertyStrings("reset-names", ["ctrl", "hdcp"]))
    hdmi.append(FdtPropertyWords("phys", [hdmi_phy_phandle]))
    hdmi.append(FdtPropertyStrings("phy-names", ["phy"]))
    hdmi.append(FdtPropertyWords("hvcc-supply", [reg_vcc_3v3_phandle]))
    hdmi_ports = FdtNode("ports")
    hdmi_ports.append(FdtPropertyWords("#address-cells", [1]))
    hdmi_ports.append(FdtPropertyWords("#size-cells", [0]))
    hdmi_in = FdtNode("port@0")
    hdmi_in.append(FdtPropertyWords("reg", [0]))
    hdmi_in_ep = FdtNode("endpoint")
    hdmi_in_ep.append(FdtPropertyWords("phandle", [hdmi_in_tcon_top_ep_phandle]))
    hdmi_in_ep.append(FdtPropertyWords("linux,phandle", [hdmi_in_tcon_top_ep_phandle]))
    hdmi_in_ep.append(FdtPropertyWords("remote-endpoint", [tcon_top_hdmi_out_hdmi_ep_phandle]))
    hdmi_in.append(hdmi_in_ep)
    hdmi_ports.append(hdmi_in)
    hdmi_out = FdtNode("port@1")
    hdmi_out.append(FdtPropertyWords("reg", [1]))
    hdmi_out_ep = FdtNode("endpoint")
    hdmi_out_ep.append(FdtPropertyWords("phandle", [hdmi_out_con_ep_phandle]))
    hdmi_out_ep.append(FdtPropertyWords("linux,phandle", [hdmi_out_con_ep_phandle]))
    hdmi_out_ep.append(FdtPropertyWords("remote-endpoint", [hdmi_con_in_phandle]))
    hdmi_out.append(hdmi_out_ep)
    hdmi_ports.append(hdmi_out)
    hdmi.append(hdmi_ports)
    soc.append(hdmi)

    root.append(soc)

    fdt = Fdt()
    fdt.add_reserve_entries([{"address": address, "size": size}])
    fdt.add_rootnode(root)
    return fdt.to_dtb()


def write_minimal_linux_dtb(dst: Path, address: int, size: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        os.chmod(dst, stat.S_IWRITE)
    dst.write_bytes(build_minimal_linux_dtb(address, size))


def write_grub_cfg(target_root: Path) -> None:
    cfg = (
        "set pager=0\n"
        "set debug=\n"
        "echo [grub] direct linux boot\n"
        "linux /casper/vmlinuz console=ttyS0,115200n8 earlycon=uart8250,mmio32,0x02500000 keep_bootcon ignore_loglevel loglevel=8 drm.debug=0x1e video=HDMI-A-1:e nokaslr fw_devlink=off clk_ignore_unused rdinit=/debug/porta-preinit ---\n"
        "echo [grub] linux command done\n"
        "initrd /casper/initrd /debug/porta-initrd.cpio\n"
        "echo [grub] initrd command done\n"
        "devicetree /dtb/a733.dtb\n"
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
        "echo Linux installer BOOTAA64.EFI not found on fs1:.\r\n"
    )
    (target_root / "startup.nsh").write_text(script, encoding="ascii", newline="")


def install_linux_installer(iso_root: Path, target_root: Path, boot_file: str) -> None:
    boot_source = Path(boot_file)
    if not boot_source.is_absolute():
        boot_source = iso_root / "EFI" / "boot" / boot_file

    required = [
        boot_source,
        iso_root / "EFI" / "boot" / "grubaa64.efi",
        iso_root / "casper" / "vmlinuz",
        iso_root / "casper" / "initrd",
    ]
    for path in required:
        if not path.exists():
            fail(f"Required installer file not found: {path}")

    copy_file(boot_source, target_root / "EFI" / "BOOT" / "BOOTAA64.EFI")
    copy_file(iso_root / "EFI" / "boot" / "grubaa64.efi", target_root / "EFI" / "BOOT" / "grubaa64.efi")
    if (iso_root / ".disk").is_dir():
        copy_tree_files(iso_root / ".disk", target_root / ".disk")
    if (iso_root / "md5sum.txt").is_file():
        copy_file(iso_root / "md5sum.txt", target_root / "md5sum.txt")
    copy_tree_files(iso_root / "casper", target_root / "casper")
    write_minimal_linux_dtb(target_root / "dtb" / "a733.dtb", 0x00102000, 0x1000)
    write_debug_initrd_overlay(target_root)
    write_grub_cfg(target_root)
    write_startup_script(target_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Ubuntu ARM64 EFI boot files to Disk 3 WINSTALL.")
    parser.add_argument("--iso-root", required=True, help="Mounted Ubuntu ISO root, for example H:\\")
    parser.add_argument("--target", help="Mounted target FAT32 root. If omitted, create/use Disk 3 WINSTALL partition.")
    parser.add_argument(
        "--boot-file",
        default="grubaa64.efi",
        help="EFI boot file name under the ISO, or an explicit path, to place as EFI\\\\BOOT\\\\BOOTAA64.EFI. Default: grubaa64.efi",
    )
    parser.add_argument(
        "--installer-partition-mb",
        type=int,
        default=2048,
        help="Create/use a Disk 3 FAT32 installer partition of this size in MB. Default: 2048",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    iso_root = normalize_existing_dir(args.iso_root)
    target_root = normalize_existing_dir(args.target) if args.target else create_disk3_installer_partition(args.installer_partition_mb)
    install_linux_installer(iso_root, target_root, args.boot_file)

    print(f"Installed Linux installer files to: {target_root}")
    print(f"  BOOTAA64.EFI -> {target_root / 'EFI' / 'BOOT' / 'BOOTAA64.EFI'}")
    print(f"  grubaa64.efi -> {target_root / 'EFI' / 'BOOT' / 'grubaa64.efi'}")
    print(f"  vmlinuz      -> {target_root / 'casper' / 'vmlinuz'}")
    print(f"  initrd       -> {target_root / 'casper' / 'initrd'}")
    print(f"  a733.dtb     -> {target_root / 'dtb' / 'a733.dtb'}")
    print(f"  grub.cfg     -> {target_root / 'boot' / 'grub' / 'grub.cfg'}")
    print(f"  startup.nsh  -> {target_root / 'startup.nsh'}")


if __name__ == "__main__":
    main()
