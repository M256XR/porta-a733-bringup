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


def install_windows_installer(iso_root: Path, target_root: Path, boot_file: str) -> None:
    bootaa64_src = iso_root / boot_file

    required = [
        bootaa64_src,
        iso_root / "EFI" / "Microsoft" / "Boot" / "BCD",
        iso_root / "boot" / "boot.sdi",
        iso_root / "sources" / "boot.wim",
    ]
    for path in required:
        if not path.exists():
            fail(f"Required installer file not found: {path}")

    copy_tree(iso_root / "EFI" / "Microsoft" / "Boot", target_root / "EFI" / "Microsoft" / "Boot")
    copy_file(bootaa64_src, target_root / "EFI" / "BOOT" / "BOOTAA64.EFI")
    copy_file(iso_root / "boot" / "boot.sdi", target_root / "boot" / "boot.sdi")
    copy_file(iso_root / "sources" / "boot.wim", target_root / "sources" / "boot.wim")


def write_startup_script(target_root: Path) -> None:
    script = (
        "@echo -off\r\n"
        "if exist fs0:\\EFI\\BOOT\\BOOTAA64.EFI then\r\n"
        "  fs0:\\EFI\\BOOT\\BOOTAA64.EFI\r\n"
        "endif\r\n"
        "echo Windows installer BOOTAA64.EFI not found on fs0:.\r\n"
    )
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    iso_root = normalize_existing_dir(args.iso_root)

    target_root = normalize_existing_dir(args.target) if args.target else create_disk3_installer_partition(args.installer_partition_mb)
    install_windows_installer(iso_root, target_root, args.boot_file)
    write_startup_script(target_root)

    print(f"Installed Windows installer files to: {target_root}")
    print(f"  BOOTAA64.EFI <- {args.boot_file}")
    print(f"  BOOTAA64.EFI -> {target_root / 'EFI' / 'BOOT' / 'BOOTAA64.EFI'}")
    print(f"  boot.sdi     -> {target_root / 'boot' / 'boot.sdi'}")
    print(f"  boot.wim     -> {target_root / 'sources' / 'boot.wim'}")
    print(f"  startup.nsh  -> {target_root / 'startup.nsh'}")


if __name__ == "__main__":
    main()
