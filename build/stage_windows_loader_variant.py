#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import stat
import shutil
import subprocess
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}")
    raise SystemExit(1)


def normalize_existing_dir(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"Path does not exist: {path}")
    if not path.is_dir():
        fail(f"Path is not a directory: {path}")
    return path


def normalize_existing_file(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"File does not exist: {path}")
    if not path.is_file():
        fail(f"Path is not a file: {path}")
    return path


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def ensure_writable(path: Path) -> None:
    if not path.exists():
        return
    current_mode = path.stat().st_mode
    os.chmod(path, current_mode | stat.S_IWRITE)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    ensure_writable(dst)
    shutil.copy2(src, dst)


def remove_if_exists(path: Path) -> None:
    if path.exists():
        ensure_writable(path)
        path.unlink()


def write_marker(target_root: Path, patch_name: str, sha256: str, patch_vas: list[str], source_efi: Path) -> Path:
    marker_path = target_root / "EFI" / "BOOT" / "BOOTAA64.PATCH.txt"
    lines = [
        f"BOOTAA64_PATCH={patch_name}",
        f"BOOTAA64_SHA256={sha256}",
        f"PATCH_VAS={','.join(patch_vas)}" if patch_vas else "PATCH_VAS=",
        f"SOURCE_EFI={source_efi}",
    ]
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("\r\n".join(lines) + "\r\n", encoding="ascii", newline="")
    return marker_path


def normalize_patch_vas(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        number = int(str(value), 0)
        normalized.append(f"0x{number:08X}")
    return normalized


def build_startup_script(mode: str) -> str:
    if mode == "keep":
        return ""

    lines = [
        "@echo -off",
        "map -r",
        r"if exist \EFI\Microsoft\Boot\bootmgfw.efi then",
        r"  \EFI\Microsoft\Boot\bootmgfw.efi",
        "endif",
    ]

    if mode == "bootmgfw_then_bootaa64":
        lines.extend(
            [
                r"if exist \EFI\BOOT\BOOTAA64.EFI then",
                r"  \EFI\BOOT\BOOTAA64.EFI",
                "endif",
            ]
        )
    else:
        lines.extend(
            [
                r"if exist \EFI\BOOT\BOOTAA64.EFI then",
                r"  echo BOOTAA64.EFI exists on the current volume but startup.nsh is not auto-launching it",
                "endif",
            ]
        )

    for fs_index in range(10):
        lines.extend(
            [
                rf"if exist fs{fs_index}:\EFI\Microsoft\Boot\bootmgfw.efi then",
                rf"  fs{fs_index}:\EFI\Microsoft\Boot\bootmgfw.efi",
                "endif",
            ]
        )

    if mode == "bootmgfw_then_bootaa64":
        for fs_index in range(10):
            lines.extend(
                [
                    rf"if exist fs{fs_index}:\EFI\BOOT\BOOTAA64.EFI then",
                    rf"  fs{fs_index}:\EFI\BOOT\BOOTAA64.EFI",
                    "endif",
                ]
            )

    lines.append("echo Windows loader not found on current volume or fs0:fs9:.")
    return "\r\n".join(lines) + "\r\n"


def run_snapshot(target_root: Path) -> str | None:
    script = Path(r"D:\Projects\porta-a733-bringup\build\snapshot_windows_media.ps1")
    if not script.exists():
        return None
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Root",
            str(target_root),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage a specific Windows loader variant onto live media and keep marker/startup in sync.")
    parser.add_argument("--target-root", default=r"F:\\", help=r"Mounted media root. Default: F:\\")
    parser.add_argument("--source-efi", required=True, help="Local EFI binary to stage")
    parser.add_argument("--patch-name", help="Marker label to write. Default: source file stem")
    parser.add_argument("--patch-vas", nargs="*", default=[], help="Patch virtual addresses to write into BOOTAA64.PATCH.txt")
    parser.add_argument(
        "--startup-mode",
        choices=("keep", "bootmgfw_only", "bootmgfw_then_bootaa64"),
        default="bootmgfw_only",
        help="How to regenerate startup.nsh. Default: bootmgfw_only",
    )
    parser.add_argument("--skip-bootmgfw-copy", action="store_true", help="Do not copy source EFI to EFI\\Microsoft\\Boot\\bootmgfw.efi")
    parser.add_argument("--skip-bootaa64-copy", action="store_true", help="Do not copy source EFI to EFI\\BOOT\\BOOTAA64.EFI")
    parser.add_argument("--remove-bootaa64", action="store_true", help="Delete EFI\\BOOT\\BOOTAA64.EFI after staging")
    parser.add_argument("--snapshot-after", action="store_true", help="Run snapshot_windows_media.ps1 after staging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_root = normalize_existing_dir(args.target_root)
    source_efi = normalize_existing_file(args.source_efi)
    patch_vas = normalize_patch_vas(args.patch_vas)

    bootaa64_path = target_root / "EFI" / "BOOT" / "BOOTAA64.EFI"
    bootmgfw_path = target_root / "EFI" / "Microsoft" / "Boot" / "bootmgfw.efi"
    startup_path = target_root / "startup.nsh"

    if not args.skip_bootaa64_copy:
        copy_file(source_efi, bootaa64_path)
    if not args.skip_bootmgfw_copy:
        copy_file(source_efi, bootmgfw_path)
    if args.remove_bootaa64:
        remove_if_exists(bootaa64_path)

    script = build_startup_script(args.startup_mode)
    if script:
        startup_path.write_text(script, encoding="ascii", newline="")

    actual_hash = sha256_hex(source_efi)
    patch_name = args.patch_name or source_efi.stem
    marker_path = write_marker(
        target_root=target_root,
        patch_name=patch_name,
        sha256=actual_hash,
        patch_vas=patch_vas,
        source_efi=source_efi,
    )

    print(f"Staged loader variant to: {target_root}")
    print(f"  source_efi   : {source_efi}")
    print(f"  sha256       : {actual_hash}")
    print(f"  patch_name   : {patch_name}")
    print(f"  patch_vas    : {','.join(patch_vas) if patch_vas else '(none)'}")
    print(f"  marker       : {marker_path}")
    print(f"  startup_mode : {args.startup_mode}")
    print(f"  bootaa64     : {'skipped' if args.skip_bootaa64_copy else bootaa64_path}")
    print(f"  bootmgfw     : {'skipped' if args.skip_bootmgfw_copy else bootmgfw_path}")
    if args.remove_bootaa64:
        print("  bootaa64 removed after staging")

    if args.snapshot_after:
        snapshot_output = run_snapshot(target_root)
        if snapshot_output:
            print(snapshot_output)


if __name__ == "__main__":
    main()
