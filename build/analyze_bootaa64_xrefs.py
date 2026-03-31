#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import struct
from typing import Iterable

import pefile
from capstone import Cs, CS_ARCH_ARM64
from capstone.arm64_const import (
    ARM64_INS_ADD,
    ARM64_INS_ADR,
    ARM64_INS_ADRP,
    ARM64_INS_LDR,
    ARM64_INS_LDRSW,
    ARM64_INS_MOV,
    ARM64_OP_IMM,
    ARM64_OP_MEM,
    ARM64_OP_REG,
)


@dataclass
class SectionView:
    name: str
    va: int
    size: int
    data: bytes
    executable: bool

    @property
    def end(self) -> int:
        return self.va + self.size


@dataclass
class StringRef:
    text: str
    va: int
    section: str


@dataclass
class Xref:
    target: StringRef
    function_start: int
    function_end: int
    insn_va: int
    insn_text: str
    context: list[str]


def iter_sections(pe: pefile.PE) -> Iterable[SectionView]:
    image_base = pe.OPTIONAL_HEADER.ImageBase
    for section in pe.sections:
        name = section.Name.rstrip(b"\x00").decode("ascii", errors="ignore")
        va = image_base + section.VirtualAddress
        size = max(section.SizeOfRawData, section.Misc_VirtualSize)
        data = section.get_data()
        executable = bool(section.Characteristics & 0x20000000)
        yield SectionView(name=name, va=va, size=size, data=data, executable=executable)


def get_section(sections: list[SectionView], name: str) -> SectionView:
    for section in sections:
        if section.name == name:
            return section
    raise RuntimeError(f"Section {name!r} not found")


def iter_arm64_function_ranges(pe: pefile.PE, text: SectionView, pdata: SectionView) -> Iterable[tuple[int, int]]:
    starts: list[int] = []
    data = pdata.data
    # ARM64 PE/COFF .pdata uses 8-byte RUNTIME_FUNCTION entries:
    #   BeginAddress (RVA), UnwindData (RVA)
    for offset in range(0, len(data), 8):
        if offset + 8 > len(data):
            break
        begin_rva, _unwind_rva = struct.unpack_from("<II", data, offset)
        begin_va = pe.OPTIONAL_HEADER.ImageBase + begin_rva
        if text.va <= begin_va < text.end:
            starts.append(begin_va)

    starts = sorted(set(starts))
    if not starts:
        return

    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else text.end
        yield (start, end)


def extract_utf16_strings(section: SectionView, min_chars: int = 4) -> list[StringRef]:
    refs: list[StringRef] = []
    data = section.data
    i = 0
    while i + 1 < len(data):
        start = i
        chars: list[str] = []
        while i + 1 < len(data):
            lo = data[i]
            hi = data[i + 1]
            if hi != 0 or lo < 0x20 or lo > 0x7E:
                break
            chars.append(chr(lo))
            i += 2
        if len(chars) >= min_chars:
            refs.append(StringRef(text="".join(chars), va=section.va + start, section=section.name))
        i = max(i + 2, start + 2)
    return refs


def disasm_bytes(data: bytes, va: int) -> list:
    md = Cs(CS_ARCH_ARM64, 0)
    md.detail = True
    return list(md.disasm(data, va))


def collect_xrefs(
    insns: list,
    function_start: int,
    function_end: int,
    targets_by_va: dict[int, list[StringRef]],
) -> list[Xref]:
    xrefs: list[Xref] = []
    reg_values: dict[int, int] = {}

    for idx, insn in enumerate(insns):
        ops = insn.operands

        if insn.id in (ARM64_INS_ADR, ARM64_INS_ADRP) and len(ops) >= 2:
            if ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_IMM:
                reg_values[ops[0].reg] = ops[1].imm
                if ops[1].imm in targets_by_va:
                    xrefs.extend(make_xrefs(insns, idx, function_start, function_end, ops[1].imm, targets_by_va))
            continue

        if insn.id == ARM64_INS_MOV and len(ops) >= 2:
            if ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_REG and ops[1].reg in reg_values:
                reg_values[ops[0].reg] = reg_values[ops[1].reg]
            continue

        if insn.mnemonic == "movz" and len(ops) >= 2:
            if ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_IMM:
                shift = 0
                if hasattr(ops[1], "shift") and ops[1].shift is not None:
                    shift = getattr(ops[1].shift, "value", 0) or 0
                reg_values[ops[0].reg] = ops[1].imm << shift
            continue

        if insn.mnemonic == "movk" and len(ops) >= 2:
            if ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_IMM:
                shift = 0
                if hasattr(ops[1], "shift") and ops[1].shift is not None:
                    shift = getattr(ops[1].shift, "value", 0) or 0
                cur = reg_values.get(ops[0].reg, 0)
                mask = 0xFFFF << shift
                reg_values[ops[0].reg] = (cur & ~mask) | (ops[1].imm << shift)
                if reg_values[ops[0].reg] in targets_by_va:
                    xrefs.extend(
                        make_xrefs(
                            insns,
                            idx,
                            function_start,
                            function_end,
                            reg_values[ops[0].reg],
                            targets_by_va,
                        )
                    )
            continue

        if insn.id == ARM64_INS_ADD and len(ops) >= 3:
            if (
                ops[0].type == ARM64_OP_REG
                and ops[1].type == ARM64_OP_REG
                and ops[2].type == ARM64_OP_IMM
                and ops[1].reg in reg_values
            ):
                reg_values[ops[0].reg] = reg_values[ops[1].reg] + ops[2].imm
                if reg_values[ops[0].reg] in targets_by_va:
                    xrefs.extend(
                        make_xrefs(
                            insns,
                            idx,
                            function_start,
                            function_end,
                            reg_values[ops[0].reg],
                            targets_by_va,
                        )
                    )
            continue

        if insn.id in (ARM64_INS_LDR, ARM64_INS_LDRSW) and len(ops) >= 2:
            if ops[0].type == ARM64_OP_REG and ops[1].type == ARM64_OP_IMM:
                reg_values[ops[0].reg] = ops[1].imm
                if ops[1].imm in targets_by_va:
                    xrefs.extend(make_xrefs(insns, idx, function_start, function_end, ops[1].imm, targets_by_va))
            continue

        for op in ops:
            if op.type == ARM64_OP_MEM and op.mem.base in reg_values:
                addr = reg_values[op.mem.base] + op.mem.disp
                if addr in targets_by_va:
                    xrefs.extend(make_xrefs(insns, idx, function_start, function_end, addr, targets_by_va))

    return xrefs


def make_xrefs(
    insns: list,
    idx: int,
    function_start: int,
    function_end: int,
    target_va: int,
    targets_by_va: dict[int, list[StringRef]],
) -> list[Xref]:
    start = max(0, idx - 2)
    end = min(len(insns), idx + 4)
    context = [f"{i.address:016X}: {i.mnemonic} {i.op_str}".rstrip() for i in insns[start:end]]
    cur = insns[idx]
    text = f"{cur.mnemonic} {cur.op_str}".rstrip()
    return [
        Xref(
            target=target,
            function_start=function_start,
            function_end=function_end,
            insn_va=cur.address,
            insn_text=text,
            context=context,
        )
        for target in targets_by_va[target_va]
    ]


def dump_function(text: SectionView, function_start: int, function_end: int) -> list[str]:
    off = function_start - text.va
    chunk = text.data[off : off + (function_end - function_start)]
    return [f"{insn.address:016X}: {insn.mnemonic} {insn.op_str}".rstrip() for insn in disasm_bytes(chunk, function_start)]


def find_function(function_ranges: list[tuple[int, int]], address: int) -> tuple[int, int] | None:
    for function_start, function_end in function_ranges:
        if function_start <= address < function_end:
            return (function_start, function_end)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Find simple ARM64 string xrefs in BOOTAA64.EFI")
    ap.add_argument("image", type=Path)
    ap.add_argument("patterns", nargs="+", help="Substring patterns to match in UTF-16 strings")
    ap.add_argument(
        "--address",
        action="append",
        default=[],
        help="Hex VA to map back to a containing ARM64 function and dump that function",
    )
    args = ap.parse_args()

    pe = pefile.PE(str(args.image), fast_load=True)
    sections = list(iter_sections(pe))
    text = get_section(sections, ".text")
    pdata = get_section(sections, ".pdata")
    function_ranges = list(iter_arm64_function_ranges(pe, text, pdata))

    string_refs: list[StringRef] = []
    for section in sections:
        string_refs.extend(extract_utf16_strings(section))

    matched: list[StringRef] = []
    lowered = [p.lower() for p in args.patterns]
    for ref in string_refs:
        text_lower = ref.text.lower()
        if any(p in text_lower for p in lowered):
            matched.append(ref)

    if not matched:
        print("No matching strings.")
        return

    print("Matched strings:")
    for ref in sorted(matched, key=lambda r: r.va):
        print(f"  {ref.va:016X} [{ref.section}] {ref.text}")

    targets_by_va: dict[int, list[StringRef]] = defaultdict(list)
    for ref in matched:
        targets_by_va[ref.va].append(ref)

    xrefs: list[Xref] = []
    for function_start, function_end in function_ranges:
        off = function_start - text.va
        chunk = text.data[off : off + (function_end - function_start)]
        xrefs.extend(
            collect_xrefs(
                disasm_bytes(chunk, function_start),
                function_start,
                function_end,
                targets_by_va,
            )
        )

    if not xrefs:
        print("\nNo simple ADR/ADRP/ADD xrefs found.")
    else:
        print("\nXrefs:")
        for xref in sorted(xrefs, key=lambda x: (x.target.va, x.function_start, x.insn_va)):
            print(
                f"\n[{xref.target.text}] target={xref.target.va:016X} "
                f"func={xref.function_start:016X}-{xref.function_end:016X} "
                f"xref={xref.insn_va:016X} {xref.insn_text}"
            )
            for line in xref.context:
                print(f"    {line}")

    for raw in args.address:
        address = int(raw, 16)
        func = find_function(function_ranges, address)
        print(f"\nAddress {address:016X}:")
        if func is None:
            print("  not inside a .pdata-described ARM64 function")
            continue
        function_start, function_end = func
        print(f"  containing function {function_start:016X}-{function_end:016X}")
        for line in dump_function(text, function_start, function_end):
            print(f"    {line}")


if __name__ == "__main__":
    main()
