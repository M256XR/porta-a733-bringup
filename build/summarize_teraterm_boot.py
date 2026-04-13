#!/usr/bin/env python3
"""Summarize A733 Tera Term boot logs.

Classifies logs into broad boot modes and extracts the main markers that keep
showing up during bring-up work: UEFI entry, Windows Boot Manager, BCD errors,
Linux kernel command line, vendor HDMI/X11 activity, and early exceptions.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


TIMESTAMP_RE = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} [^\]]+)\]")
STATUS_RE = re.compile(r"Status:\s*(0x[0-9A-Fa-f]+)")
FILE_RE = re.compile(r"File:\s*(.+?)(?=Status:|Info:|\[A733-|$)")
KERNEL_CMDLINE_RE = re.compile(r"Kernel command line:\s*(.+)")
RUNID_RE = re.compile(r"porta_runid=([0-9]{8}-[0-9]{6})")
ROOT_RE = re.compile(r"\broot=([^\s]+)")
VIDEO_RE = re.compile(r"\bvideo=([^\s]+)")


@dataclass
class LogSummary:
    path: str
    size_bytes: int
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    boot_mode: str = "unknown"
    used_uefi: bool = False
    saw_boot0: bool = False
    saw_bl31: bool = False
    saw_shell: bool = False
    saw_grub: bool = False
    saw_windows_boot_manager: bool = False
    saw_linux_kernel: bool = False
    saw_vendor_hdmi: bool = False
    saw_xdirect: bool = False
    saw_systemd: bool = False
    saw_exception: bool = False
    no_mapping_count: int = 0
    synchronous_exception_count: int = 0
    elr_count: int = 0
    kernel_cmdline: str | None = None
    kernel_root: str | None = None
    kernel_video: str | None = None
    vendor_runid: str | None = None
    bcd_statuses: list[str] = field(default_factory=list)
    bcd_files: list[str] = field(default_factory=list)
    notable_markers: list[str] = field(default_factory=list)


def iter_lines(path: Path) -> Iterable[tuple[int, str]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for lineno, line in enumerate(handle, start=1):
            yield lineno, line.rstrip("\n")


def unique_append(seq: list[str], value: str, *, limit: int | None = None) -> None:
    if value in seq:
        return
    seq.append(value)
    if limit is not None and len(seq) > limit:
        del seq[limit:]


def classify(summary: LogSummary) -> str:
    cmdline = summary.kernel_cmdline or ""
    cmdline_lower = cmdline.lower()
    if summary.saw_windows_boot_manager or summary.bcd_statuses:
        return "windows_bootmgr"
    if summary.saw_linux_kernel or summary.saw_vendor_hdmi or summary.saw_xdirect:
        if "/vendor/vmlinuz-" in cmdline or summary.saw_vendor_hdmi or summary.saw_xdirect:
            return "vendor_linux_via_uefi" if summary.used_uefi else "vendor_linux"
        if "casper" in cmdline_lower or "subiquity" in cmdline_lower or "ubuntu" in cmdline_lower:
            return "ubuntu_installer_via_uefi" if summary.used_uefi else "ubuntu_installer"
        return "linux_via_uefi" if summary.used_uefi else "linux"
    if summary.saw_exception:
        return "boot_exception"
    if summary.used_uefi and summary.saw_shell:
        return "uefi_shell_only"
    if summary.used_uefi:
        return "uefi_only"
    if summary.saw_boot0 or summary.saw_bl31:
        return "pre_uefi_only"
    return "unknown"


def analyze_log(path: Path) -> LogSummary:
    summary = LogSummary(path=str(path), size_bytes=path.stat().st_size)
    for lineno, line in iter_lines(path):
        if not summary.first_timestamp:
            match = TIMESTAMP_RE.match(line)
            if match:
                summary.first_timestamp = match.group("ts")
        match = TIMESTAMP_RE.match(line)
        if match:
            summary.last_timestamp = match.group("ts")

        if "BOOT0 is starting!" in line:
            summary.saw_boot0 = True
            unique_append(summary.notable_markers, f"L{lineno}: boot0")
        if "BL31" in line:
            summary.saw_bl31 = True
        if "UEFI firmware" in line:
            summary.used_uefi = True
            unique_append(summary.notable_markers, f"L{lineno}: uefi")
        if "UEFI Interactive Shell" in line or line.startswith("Shell>"):
            summary.saw_shell = True
        if "GNU GRUB" in line or "[grub]" in line:
            summary.saw_grub = True
            unique_append(summary.notable_markers, f"L{lineno}: grub")
        if "Windows Boot Manager" in line:
            summary.saw_windows_boot_manager = True
            unique_append(summary.notable_markers, f"L{lineno}: windows boot manager")
        if "No mapping" in line:
            summary.no_mapping_count += 1
        if "Synchronous Exception" in line:
            summary.synchronous_exception_count += 1
            summary.saw_exception = True
            unique_append(summary.notable_markers, f"L{lineno}: synchronous exception")
        if "[A733-EXC]" in line or "ELR=" in line:
            summary.elr_count += 1
            summary.saw_exception = True
        if "Kernel command line:" in line:
            summary.saw_linux_kernel = True
            match = KERNEL_CMDLINE_RE.search(line)
            if match:
                summary.kernel_cmdline = match.group(1).strip()
                root_match = ROOT_RE.search(summary.kernel_cmdline)
                if root_match:
                    summary.kernel_root = root_match.group(1)
                video_match = VIDEO_RE.search(summary.kernel_cmdline)
                if video_match:
                    summary.kernel_video = video_match.group(1)
                runid_match = RUNID_RE.search(summary.kernel_cmdline)
                if runid_match:
                    summary.vendor_runid = runid_match.group(1)
                unique_append(summary.notable_markers, f"L{lineno}: kernel command line")
        if "sunxi-hdmi" in line:
            summary.saw_vendor_hdmi = True
            if "drm hdmi mode set" in line or "drm hdmi detect: connect" in line:
                unique_append(summary.notable_markers, f"L{lineno}: {line.strip()}", limit=8)
        if "[xdirect]" in line or "porta-x11-direct" in line:
            summary.saw_xdirect = True
            unique_append(summary.notable_markers, f"L{lineno}: xdirect", limit=8)
        if "systemd-timesyncd" in line or "systemd-logind" in line:
            summary.saw_systemd = True

        status_match = STATUS_RE.search(line)
        if status_match:
            unique_append(summary.bcd_statuses, status_match.group(1), limit=8)
        file_match = FILE_RE.search(line)
        if file_match:
            file_value = file_match.group(1).strip()
            if "BCD" in file_value.upper():
                unique_append(summary.bcd_files, file_value, limit=8)

    summary.boot_mode = classify(summary)
    return summary


def render_text(summary: LogSummary) -> str:
    lines = [
        f"{summary.path}",
        f"  mode: {summary.boot_mode}",
        f"  time: {summary.first_timestamp or '-'} -> {summary.last_timestamp or '-'}",
        f"  size: {summary.size_bytes} bytes",
        (
            "  flags: "
            f"boot0={int(summary.saw_boot0)} "
            f"bl31={int(summary.saw_bl31)} "
            f"uefi={int(summary.used_uefi)} "
            f"grub={int(summary.saw_grub)} "
            f"windows={int(summary.saw_windows_boot_manager)} "
            f"linux={int(summary.saw_linux_kernel)} "
            f"vendor_hdmi={int(summary.saw_vendor_hdmi)} "
            f"xdirect={int(summary.saw_xdirect)} "
            f"shell={int(summary.saw_shell)} "
            f"exception={int(summary.saw_exception)}"
        ),
        (
            "  counters: "
            f"no_mapping={summary.no_mapping_count} "
            f"sync_exception={summary.synchronous_exception_count} "
            f"elr={summary.elr_count}"
        ),
    ]
    if summary.kernel_cmdline:
        lines.append(f"  kernel_root: {summary.kernel_root or '-'}")
        lines.append(f"  kernel_video: {summary.kernel_video or '-'}")
        lines.append(f"  vendor_runid: {summary.vendor_runid or '-'}")
    if summary.bcd_statuses:
        lines.append(f"  bcd_statuses: {', '.join(summary.bcd_statuses)}")
    if summary.bcd_files:
        lines.append(f"  bcd_files: {', '.join(summary.bcd_files)}")
    if summary.notable_markers:
        lines.append("  notable:")
        for marker in summary.notable_markers[:8]:
            lines.append(f"    - {marker}")
    return "\n".join(lines)


def render_markdown(summaries: list[LogSummary]) -> str:
    lines = [
        "# Tera Term Log Inventory",
        "",
        "| File | Mode | First timestamp | Last timestamp | Key points |",
        "| --- | --- | --- | --- | --- |",
    ]
    for summary in summaries:
        points: list[str] = []
        if summary.kernel_root:
            points.append(f"root={summary.kernel_root}")
        if summary.kernel_video:
            points.append(f"video={summary.kernel_video}")
        if summary.vendor_runid:
            points.append(f"runid={summary.vendor_runid}")
        if summary.bcd_statuses:
            points.append("BCD " + ",".join(summary.bcd_statuses))
        if summary.no_mapping_count:
            points.append(f"No mapping x{summary.no_mapping_count}")
        if summary.synchronous_exception_count:
            points.append(f"SyncEx x{summary.synchronous_exception_count}")
        if summary.saw_vendor_hdmi:
            points.append("sunxi-hdmi")
        if summary.saw_xdirect:
            points.append("porta-x11-direct")
        if not points:
            points.append("-")
        lines.append(
            "| "
            + " | ".join(
                [
                    summary.path.replace("\\", "/"),
                    summary.boot_mode,
                    summary.first_timestamp or "-",
                    summary.last_timestamp or "-",
                    "; ".join(points),
                ]
            )
            + " |"
        )

    for summary in summaries:
        lines.extend(
            [
                "",
                f"## {summary.path.replace(chr(92), '/')}",
                "",
                f"- mode: `{summary.boot_mode}`",
                f"- size_bytes: `{summary.size_bytes}`",
                f"- timestamps: `{summary.first_timestamp or '-'}` -> `{summary.last_timestamp or '-'}`",
                f"- flags: `boot0={int(summary.saw_boot0)} bl31={int(summary.saw_bl31)} uefi={int(summary.used_uefi)} grub={int(summary.saw_grub)} windows={int(summary.saw_windows_boot_manager)} linux={int(summary.saw_linux_kernel)} vendor_hdmi={int(summary.saw_vendor_hdmi)} xdirect={int(summary.saw_xdirect)} shell={int(summary.saw_shell)} exception={int(summary.saw_exception)}`",
                f"- counters: `no_mapping={summary.no_mapping_count} sync_exception={summary.synchronous_exception_count} elr={summary.elr_count}`",
            ]
        )
        if summary.kernel_cmdline:
            lines.append(f"- kernel_root: `{summary.kernel_root or '-'}`")
            lines.append(f"- kernel_video: `{summary.kernel_video or '-'}`")
            lines.append(f"- vendor_runid: `{summary.vendor_runid or '-'}`")
        if summary.bcd_statuses:
            lines.append(f"- bcd_statuses: `{', '.join(summary.bcd_statuses)}`")
        if summary.bcd_files:
            lines.append(f"- bcd_files: `{', '.join(summary.bcd_files)}`")
        if summary.notable_markers:
            lines.append("- notable_markers:")
            for marker in summary.notable_markers[:8]:
                lines.append(f"  - `{marker}`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize A733 Tera Term boot logs.")
    parser.add_argument("paths", nargs="+", help="Log files or directories to analyze.")
    parser.add_argument("--markdown", action="store_true", help="Render Markdown instead of plain text.")
    parser.add_argument("--json", action="store_true", help="Render JSON instead of plain text.")
    parser.add_argument("--output", help="Write output to a file.")
    return parser.parse_args()


def expand_paths(values: list[str]) -> list[Path]:
    results: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            results.extend(sorted(child for child in path.iterdir() if child.is_file() and child.suffix.lower() == ".log"))
        elif path.is_file():
            results.append(path)
        else:
            raise SystemExit(f"Path not found: {path}")
    return results


def main() -> None:
    args = parse_args()
    paths = expand_paths(args.paths)
    summaries = [analyze_log(path) for path in paths]

    if args.json:
        content = json.dumps([asdict(summary) for summary in summaries], ensure_ascii=False, indent=2)
    elif args.markdown:
        content = render_markdown(summaries)
    else:
        content = "\n\n".join(render_text(summary) for summary in summaries)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8", newline="\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
