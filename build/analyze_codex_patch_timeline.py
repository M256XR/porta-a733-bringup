#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


MARKER_RE = re.compile(r"BOOTAA64_PATCH=([^\s`]+)")
SHA_RE = re.compile(r"BOOTAA64_SHA256=([0-9A-Fa-f]+)")
VAS_RE = re.compile(r"PATCH_VAS=([0-9A-Fa-fx,]+)")
TS_RE = re.compile(r"\[(20\d\d-\d\d-\d\d \d\d:\d\d:\d\d(?:\.\d+)?)\]")

EVENT_PATTERNS = [
    ("no_mapping", "No mapping"),
    ("bcd_0098", "0xc0000098"),
    ("bcd_000d", "0xc000000d"),
    ("regression", "regression"),
    ("restored", "戻せました"),
    ("safer", "safer 版"),
    ("double_start", "startup.nsh"),
    ("live_sync", "live の F:/EFI/BOOT/BOOTAA64.EFI と F:/EFI/Microsoft/Boot/bootmgfw.efi"),
]


@dataclass(frozen=True)
class Marker:
    line_no: int
    patch_name: str
    sha256: str | None
    patch_vas: str | None

    def short_name(self) -> str:
        if len(self.patch_name) <= 96:
            return self.patch_name
        return self.patch_name[:93] + "..."


@dataclass(frozen=True)
class Event:
    line_no: int
    kind: str
    snippet: str
    timestamp: str | None
    marker: Marker | None


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def extract_markers(lines: list[str]) -> list[Marker]:
    markers: list[Marker] = []
    seen: set[tuple[int, str, str | None, str | None]] = set()
    for idx, line in enumerate(lines):
        marker_match = MARKER_RE.search(line)
        if marker_match is None:
            continue

        patch_name = marker_match.group(1)
        sha256 = None
        patch_vas = None
        for look_ahead in range(idx, min(idx + 6, len(lines))):
            if sha256 is None:
                sha_match = SHA_RE.search(lines[look_ahead])
                if sha_match is not None:
                    sha256 = sha_match.group(1)
            if patch_vas is None:
                vas_match = VAS_RE.search(lines[look_ahead])
                if vas_match is not None:
                    patch_vas = vas_match.group(1)

        key = (idx + 1, patch_name, sha256, patch_vas)
        if key in seen:
            continue
        seen.add(key)
        markers.append(Marker(idx + 1, patch_name, sha256, patch_vas))
    return markers


def marker_for_line(markers: list[Marker], line_no: int) -> Marker | None:
    current: Marker | None = None
    for marker in markers:
        if marker.line_no > line_no:
            break
        current = marker
    return current


def find_timestamp(lines: list[str], idx: int) -> str | None:
    for probe in range(max(0, idx - 2), min(len(lines), idx + 3)):
        match = TS_RE.search(lines[probe])
        if match is not None:
            return match.group(1)
    return None


def extract_events(lines: list[str], markers: list[Marker]) -> list[Event]:
    events: list[Event] = []
    for idx, line in enumerate(lines):
        for kind, token in EVENT_PATTERNS:
            if token not in line:
                continue
            snippet = line.strip()
            if len(snippet) > 180:
                snippet = snippet[:177] + "..."
            events.append(
                Event(
                    line_no=idx + 1,
                    kind=kind,
                    snippet=snippet,
                    timestamp=find_timestamp(lines, idx),
                    marker=marker_for_line(markers, idx + 1),
                )
            )
    return events


def unique_markers(markers: list[Marker]) -> list[Marker]:
    result: list[Marker] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for marker in markers:
        key = (marker.patch_name, marker.sha256, marker.patch_vas)
        if key in seen:
            continue
        seen.add(key)
        result.append(marker)
    return result


def render_marker(marker: Marker | None) -> str:
    if marker is None:
        return "none"
    parts = [marker.short_name()]
    if marker.patch_vas:
        parts.append(f"vas={marker.patch_vas}")
    if marker.sha256:
        parts.append(f"sha={marker.sha256[:12]}")
    return ", ".join(parts)


def write_report(output_path: Path, source_path: Path, markers: list[Marker], events: list[Event]) -> None:
    distinct_markers = unique_markers(markers)
    key_events: list[Event] = []
    interesting_kinds = {"bcd_000d", "bcd_0098", "no_mapping", "regression", "restored", "safer", "live_sync"}
    for event in events:
        if event.kind not in interesting_kinds:
            continue
        if key_events and key_events[-1].kind == event.kind and key_events[-1].snippet == event.snippet:
            continue
        key_events.append(event)

    lines: list[str] = []
    lines.append(f"# Codex Patch Timeline Extract ({source_path.name})")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Source: `{source_path}`")
    lines.append(f"- Marker observations: {len(markers)}")
    lines.append(f"- Distinct marker states: {len(distinct_markers)}")
    lines.append(f"- Interesting event observations: {len(key_events)}")
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    lines.append("- `codex.txt` contains repeated live-media rewrites of both `F:\\EFI\\BOOT\\BOOTAA64.EFI` and `F:\\EFI\\Microsoft\\Boot\\bootmgfw.efi`.")
    lines.append("- `No mapping` and `BCD` results must therefore be interpreted together with the active patch marker, not as pure UEFI behavior.")
    lines.append("- The transcript explicitly identifies `0x1003BA6C` as a `No mapping` regression candidate and later switches to a safer variant that NOPs the cleanup helper.")
    lines.append("")
    lines.append("## Distinct Marker States")
    lines.append("")
    for marker in distinct_markers[:40]:
        lines.append(
            f"- line {marker.line_no}: `{marker.short_name()}`"
            + (f" | `PATCH_VAS={marker.patch_vas}`" if marker.patch_vas else "")
            + (f" | `SHA256={marker.sha256}`" if marker.sha256 else "")
        )
    if len(distinct_markers) > 40:
        lines.append(f"- ... {len(distinct_markers) - 40} more marker states omitted")
    lines.append("")
    lines.append("## Key Event Timeline")
    lines.append("")
    for event in key_events[:120]:
        ts = event.timestamp or "timestamp-unknown"
        lines.append(
            f"- line {event.line_no} | `{event.kind}` | `{ts}` | marker: `{render_marker(event.marker)}`"
        )
        lines.append(f"  {event.snippet}")
    if len(key_events) > 120:
        lines.append(f"- ... {len(key_events) - 120} more events omitted")
    lines.append("")
    lines.append("## Regression-Focused Notes")
    lines.append("")
    regression_events = [
        event for event in key_events if event.kind in {"regression", "no_mapping", "restored", "safer"}
    ]
    if not regression_events:
        lines.append("- none")
    else:
        for event in regression_events[:40]:
            ts = event.timestamp or "timestamp-unknown"
            lines.append(
                f"- line {event.line_no} | `{event.kind}` | `{ts}` | marker: `{render_marker(event.marker)}`"
            )
            lines.append(f"  {event.snippet}")
    lines.append("")
    lines.append("## BCD-Focused Notes")
    lines.append("")
    bcd_events = [event for event in key_events if event.kind in {"bcd_000d", "bcd_0098"}]
    if not bcd_events:
        lines.append("- none")
    else:
        for event in bcd_events[:40]:
            ts = event.timestamp or "timestamp-unknown"
            lines.append(
                f"- line {event.line_no} | `{event.kind}` | `{ts}` | marker: `{render_marker(event.marker)}`"
            )
            lines.append(f"  {event.snippet}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract patch markers and key outcomes from codex.txt")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lines = load_lines(args.input)
    markers = extract_markers(lines)
    events = extract_events(lines, markers)
    write_report(args.output, args.input, markers, events)


if __name__ == "__main__":
    main()
