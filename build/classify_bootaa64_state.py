#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import re
import struct
from pathlib import Path

BASE_VA = 0x10000000
MARKER_PATCH_RE = re.compile(r"^BOOTAA64_PATCH=(.+)$", re.MULTILINE)
MARKER_HASH_RE = re.compile(r"^BOOTAA64_SHA256=([0-9A-Fa-f]{64})$", re.MULTILINE)
MARKER_VAS_RE = re.compile(r"^PATCH_VAS=([0-9A-Fa-fx,]+)$", re.MULTILINE)


def sha256_hex(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_bytes(path: Path) -> bytes:
    return path.read_bytes()


def parse_sections(pe_bytes: bytes) -> list[dict[str, int | str]]:
    peoff = struct.unpack_from("<I", pe_bytes, 0x3C)[0]
    num_sections = struct.unpack_from("<H", pe_bytes, peoff + 6)[0]
    opt_size = struct.unpack_from("<H", pe_bytes, peoff + 20)[0]
    sec_off = peoff + 24 + opt_size
    sections: list[dict[str, int | str]] = []
    for idx in range(num_sections):
        off = sec_off + 40 * idx
        name = pe_bytes[off : off + 8].rstrip(b"\0").decode("ascii", "replace")
        vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", pe_bytes, off + 8)
        sections.append(
            {
                "name": name,
                "vaddr": vaddr,
                "vsize": vsize,
                "rptr": rptr,
                "rsize": rsize,
            }
        )
    return sections


def file_off_to_va(file_off: int, sections: list[dict[str, int | str]]) -> tuple[int | None, str | None]:
    for sec in sections:
        rptr = int(sec["rptr"])
        span = max(int(sec["vsize"]), int(sec["rsize"]))
        if rptr <= file_off < rptr + span:
            rva = int(sec["vaddr"]) + (file_off - rptr)
            return BASE_VA + rva, str(sec["name"])
    return None, None


def va_to_file_off(va: int, sections: list[dict[str, int | str]]) -> int:
    rva = va - BASE_VA
    for sec in sections:
        vaddr = int(sec["vaddr"])
        span = max(int(sec["vsize"]), int(sec["rsize"]))
        if vaddr <= rva < vaddr + span:
            return int(sec["rptr"]) + (rva - vaddr)
    raise ValueError(f"VA 0x{va:08X} is outside PE sections")


def diff_runs(left: bytes, right: bytes) -> list[tuple[int, int]]:
    if len(left) != len(right):
        raise ValueError(f"length mismatch: {len(left)} != {len(right)}")
    runs: list[tuple[int, int]] = []
    idx = 0
    while idx < len(left):
        if left[idx] != right[idx]:
            start = idx
            while idx < len(left) and left[idx] != right[idx]:
                idx += 1
            runs.append((start, idx))
        else:
            idx += 1
    return runs


def parse_marker(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    patch_name = None
    claimed_hash = None
    patch_vas: list[int] = []

    match = MARKER_PATCH_RE.search(text)
    if match:
        patch_name = match.group(1).strip()
    match = MARKER_HASH_RE.search(text)
    if match:
        claimed_hash = match.group(1).upper()
    match = MARKER_VAS_RE.search(text)
    if match:
        patch_vas = [int(part, 0) for part in match.group(1).split(",") if part]
    return {
        "patch_name": patch_name,
        "claimed_hash": claimed_hash,
        "patch_vas": patch_vas,
    }


def load_patch_catalog(path: Path | None):
    if path is None or not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("patch_bootaa64_mod", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load patch catalog: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "PATCHES", None)


def known_changed_sites(
    target: bytes,
    original: bytes,
    sections: list[dict[str, int | str]],
    patches: dict[str, object] | None,
) -> dict[int, str]:
    if not patches:
        return {}
    changed: dict[int, str] = {}
    for patch in patches.values():
        for site in patch["sites"]:
            va = int(site["va"])
            replacement = bytes(site["replacement"])
            off = va_to_file_off(va, sections)
            size = len(replacement)
            orig_chunk = original[off : off + size]
            target_chunk = target[off : off + size]
            if target_chunk != orig_chunk:
                changed[va] = target_chunk.hex()
    return dict(sorted(changed.items()))


def largest_subset_recipes(
    actual_sites: dict[int, str],
    patches: dict[str, object] | None,
) -> list[tuple[int, str]]:
    if not patches:
        return []
    matches: list[tuple[int, str]] = []
    for name, patch in patches.items():
        ok = True
        for site in patch["sites"]:
            va = int(site["va"])
            replacement = bytes(site["replacement"]).hex()
            if actual_sites.get(va) != replacement:
                ok = False
                break
        if ok:
            matches.append((len(patch["sites"]), name))
    matches.sort(reverse=True)
    return matches


def format_run_lines(
    title: str,
    left: bytes,
    right: bytes,
    sections: list[dict[str, int | str]],
    limit: int = 64,
) -> list[str]:
    runs = diff_runs(left, right)
    lines = [title, f"- diff_runs: {len(runs)}"]
    for start, end in runs[:limit]:
        va, sec_name = file_off_to_va(start, sections)
        if va is None:
            lines.append(f"- file 0x{start:06X}-0x{end - 1:06X} len={end - start} va=<unmapped>")
        else:
            lines.append(
                f"- file 0x{start:06X}-0x{end - 1:06X} len={end - start} va=0x{va:08X} sec={sec_name}"
            )
    if len(runs) > limit:
        lines.append(f"- ... truncated after {limit} runs")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a BOOTAA64/bootmgfw binary against local reference variants")
    parser.add_argument("target", type=Path, help="Target EFI binary to analyze")
    parser.add_argument("--original", type=Path, default=Path(r"D:\Projects\porta-a733-bringup\build\BOOTAA64.original.EFI"))
    parser.add_argument("--fixed", type=Path, default=Path(r"D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI"))
    parser.add_argument("--patch-script", type=Path, default=Path(r"D:\Projects\porta-a733-bringup\build\patch_bootaa64.py"))
    parser.add_argument("--marker", type=Path, help="Optional BOOTAA64.PATCH.txt to compare against")
    args = parser.parse_args()

    target_bytes = load_bytes(args.target)
    target_hash = sha256_hex(args.target)

    print("# BOOTAA64 State")
    print()
    print(f"- target: {args.target}")
    print(f"- sha256: {target_hash}")
    print(f"- length: {len(target_bytes)}")

    original_bytes = None
    fixed_bytes = None
    sections = None

    if args.original.exists():
        original_bytes = load_bytes(args.original)
        sections = parse_sections(original_bytes)
        print(f"- original: {args.original}")
        print(f"- original_sha256: {sha256_hex(args.original)}")
        print(f"- matches_original: {'yes' if target_bytes == original_bytes else 'no'}")
    else:
        print(f"- original: missing ({args.original})")

    if args.fixed.exists():
        fixed_bytes = load_bytes(args.fixed)
        print(f"- fixed: {args.fixed}")
        print(f"- fixed_sha256: {sha256_hex(args.fixed)}")
        print(f"- matches_fixed: {'yes' if target_bytes == fixed_bytes else 'no'}")
    else:
        print(f"- fixed: missing ({args.fixed})")

    if args.marker and args.marker.exists():
        marker = parse_marker(args.marker)
        print(f"- marker: {args.marker}")
        if marker["patch_name"]:
            print(f"- marker_patch: {marker['patch_name']}")
        if marker["claimed_hash"]:
            print(f"- marker_claimed_hash: {marker['claimed_hash']}")
            print(f"- marker_hash_matches_target: {'yes' if marker['claimed_hash'] == target_hash else 'no'}")
        if marker["patch_vas"]:
            joined = ",".join(f"0x{va:08X}" for va in marker["patch_vas"])
            print(f"- marker_patch_vas: {joined}")

    if original_bytes is None or sections is None:
        return 0

    print()
    for line in format_run_lines("## Diff vs Original", original_bytes, target_bytes, sections):
        print(line)

    if fixed_bytes is not None:
        print()
        for line in format_run_lines("## Diff vs Fixed", fixed_bytes, target_bytes, sections):
            print(line)

    patches = load_patch_catalog(args.patch_script if args.patch_script.exists() else None)
    actual_sites = known_changed_sites(target_bytes, original_bytes, sections, patches)
    if actual_sites:
        print()
        print("## Known Patch Sites Changed")
        print(f"- count: {len(actual_sites)}")
        for va, chunk in actual_sites.items():
            print(f"- 0x{va:08X}={chunk}")

        subset = largest_subset_recipes(actual_sites, patches)
        print()
        print("## Largest Matching Recipe Subsets")
        if subset:
            for count, name in subset[:12]:
                print(f"- {count} sites: {name}")
        else:
            print("- none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
