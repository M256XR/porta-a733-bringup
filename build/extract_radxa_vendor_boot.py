#!/usr/bin/env python3
"""Extract Radxa vendor Linux boot assets from a raw disk image via WSL."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def windows_to_wsl(path: Path) -> str:
    path = path.resolve()
    drive = path.drive.rstrip(":").lower()
    tail = path.as_posix().split(":", 1)[1]
    return f"/mnt/{drive}{tail}"


def run_wsl_bash(script: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, newline="\n", encoding="utf-8") as handle:
        handle.write(script.replace("\r\n", "\n").replace("\r", ""))
        temp_path = Path(handle.name)
    try:
        subprocess.run(
            [
                "wsl",
                "-u",
                "root",
                "-d",
                "Ubuntu-22.04",
                "--",
                "bash",
                windows_to_wsl(temp_path),
            ],
            check=True,
        )
    finally:
        temp_path.unlink(missing_ok=True)


def extract_vendor_boot(image: Path, out_dir: Path) -> None:
    if not image.is_file():
        fail(f"Image does not exist: {image}")
    out_dir.mkdir(parents=True, exist_ok=True)

    image_wsl = shlex.quote(windows_to_wsl(image))
    out_wsl = shlex.quote(windows_to_wsl(out_dir))

    script = f"""
set -euo pipefail
img={image_wsl}
out={out_wsl}
mkdir -p "$out"
work=$(mktemp -d)
loop=$(losetup --find --show --partscan "$img")
cleanup(){{
  umount "$work/p3" 2>/dev/null || true
  losetup -d "$loop" 2>/dev/null || true
  rm -rf "$work"
}}
trap cleanup EXIT
mkdir -p "$work/p3"
mount -o ro "${{loop}}p3" "$work/p3"

cp -f "$work/p3/boot/vmlinuz-5.15.147-7-a733" "$out/"
cp -f "$work/p3/boot/initrd.img-5.15.147-7-a733" "$out/"
cp -f "$work/p3/usr/lib/linux-image-5.15.147-7-a733/allwinner/sun60i-a733-cubie-a7z.dtb" "$out/"
cp -f "$work/p3/boot/extlinux/extlinux.conf" "$out/extlinux.conf"
cp -f "$work/p3/boot/config-5.15.147-7-a733" "$out/" || true
cp -f "$work/p3/boot/System.map-5.15.147-7-a733" "$out/" || true

find "$work/p3/lib/modules/5.15.147-7-a733/kernel/drivers" -maxdepth 8 \\
  \\( -path '*/clk/*' -o -path '*/reset/*' -o -path '*/pinctrl/*' -o -path '*/mmc/*' -o -path '*/gpu/drm/*' -o -path '*/phy/*' \\) \\
  -type f | sort > "$out/modules-interesting.txt"

find "$work/p3/usr/lib/linux-image-5.15.147-7-a733" -maxdepth 2 -type f | sort > "$out/linux-image-files.txt"

printf 'Extracted vendor boot assets to %s\\n' "$out"
ls -lh "$out"
"""
    run_wsl_bash(script)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract Radxa vendor kernel/initrd/dtb from a raw disk image.")
    parser.add_argument("--image", required=True, help="Path to the raw Radxa disk image.")
    parser.add_argument("--out", required=True, help="Output directory for extracted boot assets.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    extract_vendor_boot(Path(args.image), Path(args.out))


if __name__ == "__main__":
    main()
