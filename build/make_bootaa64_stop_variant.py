#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import pefile

NOP = bytes.fromhex("1f2003d5")
UDF = bytes.fromhex("00000000")

ACTION_BYTES = {
    "nop": NOP,
    "udf": UDF,
}


@dataclass(frozen=True)
class PatchSite:
    va: int
    action: str
    replacement: bytes
    expected: bytes | None


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def existing_file(path_text: str) -> Path:
    path = Path(path_text)
    if not path.exists():
        fail(f"File does not exist: {path}")
    if not path.is_file():
        fail(f"Path is not a file: {path}")
    return path


def normalize_output(path_text: str) -> Path:
    path = Path(path_text)
    if path.exists() and not path.is_file():
        fail(f"Output path exists and is not a file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def parse_expected_hex(hex_text: str) -> bytes:
    value = hex_text.strip().replace(" ", "").replace("_", "")
    if value.startswith("0x") or value.startswith("0X"):
        value = value[2:]
    try:
        data = bytes.fromhex(value)
    except ValueError as exc:
        fail(f"Invalid expected hex '{hex_text}': {exc}")
    if len(data) != 4:
        fail(f"Expected hex must be exactly 4 bytes, got {len(data)} from '{hex_text}'")
    return data


def parse_patch_site(text: str) -> PatchSite:
    parts = text.split(":")
    if len(parts) not in (2, 3):
        fail(f"Invalid --site '{text}'. Use VA:ACTION[:EXPECTED_HEX]")

    try:
        va = int(parts[0], 0)
    except ValueError:
        fail(f"Invalid VA in --site '{text}'")

    action = parts[1].strip().lower()
    if action in ACTION_BYTES:
        replacement = ACTION_BYTES[action]
    elif action.startswith("hex="):
        replacement = parse_expected_hex(action[4:])
    else:
        fail(
            f"Unsupported action '{action}' in --site '{text}'. "
            f"Supported: {', '.join(sorted(ACTION_BYTES))}, hex=<8 hex digits>"
        )

    expected = parse_expected_hex(parts[2]) if len(parts) == 3 else None
    return PatchSite(va=va, action=action, replacement=replacement, expected=expected)


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a minimal BOOTAA64.EFI stop-point variant from an existing image.")
    parser.add_argument("--input", required=True, help="Input EFI image")
    parser.add_argument("--output", required=True, help="Output EFI image")
    parser.add_argument(
        "--site",
        action="append",
        required=True,
        help="Patch site in the form VA:ACTION[:EXPECTED_HEX], for example 0x1003B49C:udf:1f000071",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = existing_file(args.input)
    output_path = normalize_output(args.output)
    sites = [parse_patch_site(text) for text in args.site]

    seen_vas: set[int] = set()
    for site in sites:
        if site.va in seen_vas:
            fail(f"Duplicate VA requested: 0x{site.va:08X}")
        seen_vas.add(site.va)

    pe = pefile.PE(str(input_path))
    image_base = pe.OPTIONAL_HEADER.ImageBase
    image_bytes = bytearray(input_path.read_bytes())

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print(f"ImageBase: 0x{image_base:016X}")

    for site in sites:
        rva = site.va - image_base
        if rva < 0:
            fail(f"VA 0x{site.va:08X} is below image base 0x{image_base:08X}")
        try:
            file_offset = pe.get_offset_from_rva(rva)
        except pefile.PEFormatError as exc:
            fail(f"Failed to map VA 0x{site.va:08X} to file offset: {exc}")

        current = bytes(image_bytes[file_offset:file_offset + 4])
        if len(current) != 4:
            fail(f"Short read at VA 0x{site.va:08X} (file offset 0x{file_offset:X})")
        if site.expected is not None and current != site.expected:
            fail(
                f"Expected bytes mismatch at VA 0x{site.va:08X}: "
                f"have {current.hex()} expected {site.expected.hex()}"
            )

        replacement = site.replacement
        image_bytes[file_offset:file_offset + 4] = replacement
        print(
            f"Patched 0x{site.va:08X} (RVA 0x{rva:08X}, file 0x{file_offset:08X}) "
            f"{current.hex()} -> {replacement.hex()} [{site.action}]"
        )

    output_path.write_bytes(image_bytes)
    print(f"SHA256: {sha256_hex(output_path)}")


if __name__ == "__main__":
    main()
