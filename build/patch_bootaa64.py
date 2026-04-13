#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import pefile

NOP = bytes.fromhex("1f2003d5")
MOV_W0_0 = bytes.fromhex("00008052")
B_TO_RETURN_AFTER_SETVAR = bytes.fromhex("6b000014")
UDF = bytes.fromhex("00000000")

PATCHES = {
    "nop_post_setvar_trace": {
        "description": "NOP the helper call immediately after WindowsBootChainSvnCheckStatus SetVariable()",
        "sites": [
            {
                "va": 0x101B6A78,
                "expected": bytes.fromhex("b2390094"),
                "replacement": NOP,
            },
        ],
    },
    "skip_post_setvar_registrations": {
        "description": "Bypass the post-SetVariable registration block by forcing each registration call to return EFI_SUCCESS",
        "sites": [
            {
                "va": 0x101B6A78,
                "expected": bytes.fromhex("b2390094"),
                "replacement": NOP,
            },
            {
                "va": 0x101B6AB0,
                "expected": bytes.fromhex("8af3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6ACC,
                "expected": bytes.fromhex("83f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6AE8,
                "expected": bytes.fromhex("7cf3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B04,
                "expected": bytes.fromhex("75f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B20,
                "expected": bytes.fromhex("6ef3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B3C,
                "expected": bytes.fromhex("67f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B58,
                "expected": bytes.fromhex("60f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B74,
                "expected": bytes.fromhex("59f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6B90,
                "expected": bytes.fromhex("52f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6BAC,
                "expected": bytes.fromhex("4bf3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6BC8,
                "expected": bytes.fromhex("44f3ff97"),
                "replacement": MOV_W0_0,
            },
            {
                "va": 0x101B6BE4,
                "expected": bytes.fromhex("3df3ff97"),
                "replacement": MOV_W0_0,
            },
        ],
    },
    "return_after_setvar": {
        "description": "Return from the surrounding function immediately after WindowsBootChainSvnCheckStatus SetVariable()",
        "sites": [
            {
                "va": 0x101B6A78,
                "expected": bytes.fromhex("b2390094"),
                "replacement": NOP,
            },
            {
                "va": 0x101B6A7C,
                "expected": bytes.fromhex("f5007836"),
                "replacement": B_TO_RETURN_AFTER_SETVAR,
            },
        ],
    },
    "skip_setvar_gate_caller": {
        "description": "Bypass the boot path caller that invokes the WindowsBootChainSvnCheckStatus handler",
        "sites": [
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
        ],
    },
    "skip_setvar_all_callers": {
        "description": "Bypass both known callers that reach the WindowsBootChainSvnCheckStatus handler",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
        ],
    },
    "skip_setvar_all_callers_and_gettime_postcall": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and return from the GetTime wrapper immediately after gRT->GetTime() returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F80,
                "expected": bytes.fromhex("e003142a"),
                "replacement": bytes.fromhex("04000014"),
            },
        ],
    },
    "skip_setvar_all_callers_and_gettime_helper": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and skip only the GetTime post-processing helper while preserving RestoreTPL",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F8C,
                "expected": bytes.fromhex("d7f9ff97"),
                "replacement": NOP,
            },
        ],
    },
    "skip_setvar_all_callers_and_break_after_gettime_helper": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, preserve the GetTime helper, and fault at the wrapper epilogue to capture the higher-level caller stack",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F90,
                "expected": bytes.fromhex("fd7bc2a8"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_gettime_helper_break_at_epilogue": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the GetTime helper, and fault at the epilogue to distinguish RestoreTPL from later caller-side hangs",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F8C,
                "expected": bytes.fromhex("d7f9ff97"),
                "replacement": NOP,
            },
            {
                "va": 0x10054F90,
                "expected": bytes.fromhex("fd7bc2a8"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_restoretpl_break_before_helper": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the GetTime RestoreTPL call, and fault immediately before the helper to confirm the hang sits inside RestoreTPL",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F84,
                "expected": bytes.fromhex("73e20894"),
                "replacement": NOP,
            },
            {
                "va": 0x10054F8C,
                "expected": bytes.fromhex("d7f9ff97"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_gettime_restoretpl": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and bypass only the GetTime RestoreTPL call so execution can continue past the identified hang point",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F84,
                "expected": bytes.fromhex("73e20894"),
                "replacement": NOP,
            },
        ],
    },
    "skip_setvar_all_callers_break_on_gettime_return": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault immediately after gRT->GetTime() returns to prove whether control leaves firmware cleanly",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F7C,
                "expected": bytes.fromhex("f30300aa"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_before_helper": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, preserve RestoreTPL, and fault immediately before the GetTime status helper to test whether RestoreTPL returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x10054F8C,
                "expected": bytes.fromhex("d7f9ff97"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_before_ttbr_switch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault inside the runtime-service restore path immediately before TTBR/MAIR/TCR switching",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DD50,
                "expected": bytes.fromhex("a81e40f9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_at_restore_ctx_entry": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault in the restore-context routine before interrupts and translation-state probing",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DCC0,
                "expected": bytes.fromhex("df4203d5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_on_restore_ctx_branch_targets": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault on whichever restore-context branch target is selected after CurrentEL comparison",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DD1C,
                "expected": bytes.fromhex("e8030090"),
                "replacement": UDF,
            },
            {
                "va": 0x1028DD40,
                "expected": bytes.fromhex("08113cd5"),
                "replacement": UDF,
            },
            {
                "va": 0x1028DDC8,
                "expected": bytes.fromhex("1f050071"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_after_restore_ctx_el1_switch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault immediately after the EL1 TTBR/MAIR/TCR/TLBI restore branch completes",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DE10,
                "expected": bytes.fromhex("e1630091"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_after_restore_ctx_postswitch_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault immediately after the post-switch restore-context helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DE1C,
                "expected": bytes.fromhex("484238d5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_after_restore_ctx_sctlr_vbar_restore": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault immediately after the TPIDR/SCTLR/VBAR restore helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DE60,
                "expected": bytes.fromhex("88fa47b9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_inside_restore_ctx_sctlr_vbar_after_tpidr": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault inside the TPIDR/SCTLR/VBAR restore helper immediately after TPIDR_EL1 + DSB complete",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC44,
                "expected": bytes.fromhex("080040f9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_inside_restore_ctx_sctlr_vbar_after_sctlr": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault inside the TPIDR/SCTLR/VBAR restore helper immediately after SCTLR_EL1 + DSB + ISB complete",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC54,
                "expected": bytes.fromhex("080440f9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_inside_restore_ctx_sctlr_vbar_after_vbar": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault inside the TPIDR/SCTLR/VBAR restore helper immediately after VBAR_EL1 is restored",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC5C,
                "expected": bytes.fromhex("09000014"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_break_inside_restore_ctx_before_vbar_write": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled and fault immediately before msr vbar_el1 so the exact VBAR value is visible in X8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_helper_return": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the restore helper returns to test whether the loss of visibility starts at the vector switch",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x1028DE60,
                "expected": bytes.fromhex("88fa47b9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_at_restore_ctx_return": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault at the restore-context routine return to see whether the remaining epilogue completes",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x1028DE94,
                "expected": bytes.fromhex("c0035fd6"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_restore_ctx_caller_helper": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault immediately after the caller-side helper that runs after restore-context returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x1028E6BC,
                "expected": bytes.fromhex("e81340b9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_perfmon_setup": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the PMU/CPACR setup block completes",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x1028E740,
                "expected": bytes.fromhex("29fb4db9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_at_runtime_resume_return": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault at the caller return after runtime-resume bookkeeping completes",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x1028E784,
                "expected": bytes.fromhex("c0035fd6"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_at_runtime_resume_caller_return": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault when the next higher-level bootmgfw caller resumes after the runtime-resume helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF0F8,
                "expected": bytes.fromhex("f303002a"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_runtime_resume_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault immediately before the higher-level caller branches on the runtime-resume status so W19 captures the returned status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF0FC,
                "expected": bytes.fromhex("539af837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_resume_global_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault just before the first success-path global flag branch after runtime-resume returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF10C,
                "expected": bytes.fromhex("89010034"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_resume_selector_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault immediately before the next success-path selector branch after loading w9 from the context block",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF164,
                "expected": bytes.fromhex("02270054"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_post_resume_helpers": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the first pair of success-path helper calls return",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF194,
                "expected": bytes.fromhex("091040f9"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_post_resume_list_init_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the next success-path initialization call returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF2A4,
                "expected": bytes.fromhex("4006f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_descriptor_process_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the first descriptor-processing call returns in the post-resume loop",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF2E0,
                "expected": bytes.fromhex("e004f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_descriptor_allocate_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the next descriptor allocation call returns in the post-resume loop",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF334,
                "expected": bytes.fromhex("000200b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_descriptor_commit_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the descriptor commit/update call returns in the post-resume loop",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF348,
                "expected": bytes.fromhex("2001f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_post_loop_finalize_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the post-loop finalize call returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF368,
                "expected": bytes.fromhex("e000f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_post_loop_stage_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the next post-loop stage call returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF394,
                "expected": bytes.fromhex("a8080090"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_on_post_loop_global_paths": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault on either side of the post-loop global-state branch so the taken path is unambiguous",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF3AC,
                "expected": bytes.fromhex("f75e00a9"),
                "replacement": UDF,
            },
            {
                "va": 0x101AF504,
                "expected": bytes.fromhex("20008052"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_stage2_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the stage-2 post-loop call returns so W19 captures its status before branching",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF510,
                "expected": bytes.fromhex("3306f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_stage3_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the stage-3 post-loop call returns so W19 captures its status before branching",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF550,
                "expected": bytes.fromhex("2004f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_pool_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the pool-allocation helper returns so X0 captures the null/non-null branch input",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF588,
                "expected": bytes.fromhex("800000b5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_after_post_loop_object_lookup_call": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the post-loop object lookup call returns so X0 captures the object pointer before dereference",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF6A0,
                "expected": bytes.fromhex("e2430091"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_metadata_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the metadata query call returns so W0 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF6B0,
                "expected": bytes.fromhex("8000f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_secondary_lookup_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the secondary lookup call returns so W0 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF6D0,
                "expected": bytes.fromhex("c06af837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_binding_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the binding call returns so W0 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF72C,
                "expected": bytes.fromhex("6000f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_dispatch_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the dispatch call returns so W19 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF76C,
                "expected": bytes.fromhex("9364f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_timer_gate_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the timer-gate metadata query returns so W0 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF788,
                "expected": bytes.fromhex("6000f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_timer_source_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the timer-source helper returns so W8 captures the branch input",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF7A8,
                "expected": bytes.fromhex("68003036"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_hyperv_context_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault before the Hyper-V context branch so X8 captures whether the pointer is null",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF8A0,
                "expected": bytes.fromhex("680000b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_runtime_stage_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the runtime-stage call returns so W19 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF948,
                "expected": bytes.fromhex("b352f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_runtime_finalize_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the runtime finalize chain returns so W19 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF95C,
                "expected": bytes.fromhex("1352f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_break_before_post_loop_runtime_report_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and fault after the runtime report chain returns so W19 captures the branch status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101AF9A4,
                "expected": bytes.fromhex("b301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, and treat the null callback dispatch at 0x101CC428 as success",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_loop_runtime_report_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault before the post-loop runtime report status branch so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AF9A4,
                "expected": bytes.fromhex("b301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_101bbd00_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the 0x101BBD00 call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AF9E0,
                "expected": bytes.fromhex("b300f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_101b0b60_compare": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault before the post-0x101B0B60 compare so X0 and X8 capture the path inputs",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA14,
                "expected": bytes.fromhex("1f000071"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_lookup_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x101BBDF0 lookup returns so W20 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFABC,
                "expected": bytes.fromhex("1420f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_query_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x10055790 query returns so X0 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFF1C,
                "expected": bytes.fromhex("201af837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_cleanup_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x101C5510 cleanup returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B0280,
                "expected": bytes.fromhex("7300f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_resume_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x101D1CA0 call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B0294,
                "expected": bytes.fromhex("7300f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_object_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x10268CC0 call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B02B4,
                "expected": bytes.fromhex("5301f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_object_update_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the error-path 0x10269060 call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B02D0,
                "expected": bytes.fromhex("7300f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_flag_set_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the post-error 0x101B5708(1) call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B0320,
                "expected": bytes.fromhex("d300f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_followup_status_branch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault after the post-error 0x101C3FB0 call returns so W19 captures the status",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B0340,
                "expected": bytes.fromhex("3306f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_break_before_post_error_parent_status_dispatch": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and fault when the parent caller at 0x1003A970 receives the aggregate status from 0x1003AD38",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1003A970,
                "expected": bytes.fromhex("48130018"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_error_path": {
        "description": "Keep both WindowsBootChainSvnCheckStatus callers disabled, skip the VBAR_EL1 write, treat the null callback dispatch at 0x101CC428 as success, and force the ConfigAccessPolicy missing-path flag clear so bootmgfw skips the 0x15000047 error branch",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_at_post_followup_success_path": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x101B0404 to confirm the post-followup success path is taken",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x101B0404,
                "expected": bytes.fromhex("a90a0090"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_at_parent_status_dispatch": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x1003A970 so the parent caller reveals the aggregate status returned by 0x1003AD38",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003A970,
                "expected": bytes.fromhex("48130018"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_at_bootmgr_parent_status": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x1003AEE4 so the broader boot manager parent reveals the status returned by 0x101AEDB8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AEE4,
                "expected": bytes.fromhex("f303002a"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_after_bootmgr_followup_status": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x1003AF44 so the status returned by 0x10053E48 is visible",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AF44,
                "expected": bytes.fromhex("f303002a"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_before_bootmgr_followup_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x1003AF38 to capture the flag driving the cbnz branch around 0x10053E48",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AF38,
                "expected": bytes.fromhex("28030035"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_break_after_bootmgr_path_query_status": {
        "description": "Keep the ConfigAccessPolicy bypass in place and fault at 0x1003AFEC to capture the status returned by 0x101B3D48 on the alternate bootmgr path",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_path_flag_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, and fault before the following bitfield branch to inspect the path flags",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003AFF4,
                "expected": bytes.fromhex("c8010036"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_on_bootmgr_path_flag_taken_target": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, and fault on the taken target of the following bitfield branch",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B02C,
                "expected": bytes.fromhex("67ce0594"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_taken_path_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the taken path, and fault on the status branch after 0x101B0A20",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B040,
                "expected": bytes.fromhex("6001f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_taken_path_followup_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the taken path, and fault on the next status branch after 0x101B1530",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B098,
                "expected": bytes.fromhex("c004f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_taken_path_merge_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the taken path, and fault on the status branch after 0x1003E290",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B0B8,
                "expected": bytes.fromhex("a003f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_merge_query_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the taken path, and fault on the merge-path status branch after 0x101B11E8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B158,
                "expected": bytes.fromhex("6000f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_final_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the taken path, and fault on the final status branch after 0x1004C1F0",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B178,
                "expected": bytes.fromhex("d302f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_success_stage1_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, and fault on the first success-path status branch after 0x10264838",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B1F0,
                "expected": bytes.fromhex("9302f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_success_stage2_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, and fault on the next success-path status branch after 0x102615B8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B1FC,
                "expected": bytes.fromhex("6003f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_success_stage2_flag_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, and fault on the success-path flag branch after 0x102615B8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B204,
                "expected": bytes.fromhex("28030034"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_break_before_bootmgr_success_stage3_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, follow the cbz path, and fault on the w20 status branch after 0x101AEDB8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B2B4,
                "expected": bytes.fromhex("9404f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_break_after_100c2ae0": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, force the later w20 error branch to the success side, and fault after 0x100C2AE0",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B420,
                "expected": bytes.fromhex("08020035"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_break_before_bootmgr_bgrt_flag_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, force the later w20 error branch to the success side, and fault before the BGRT/global flag branch",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B448,
                "expected": bytes.fromhex("a8000036"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_break_after_bootmgr_bgrt_fallback_call": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, force the later w20 error branch to the success side, take the BGRT fallback path, and fault after 0x100C22C0 returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B460,
                "expected": bytes.fromhex("680000d0"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_break_before_bootmgr_post_bgrt_query_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, force the later w20 error branch to the success side, and fault after the post-BGRT query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B49C,
                "expected": bytes.fromhex("1f000071"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_break_before_bootmgr_post_bgrt_fallback_status_branch": {
        "description": "Keep the ConfigAccessPolicy bypass in place, bypass the 0x101B3D48 error branch once, force the later w20 error branch to the success side, and fault after the post-BGRT fallback helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_after_bootmgr_policy_call": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the follow-up policy helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B4EC,
                "expected": bytes.fromhex("5301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_policy_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the next bootmgr policy query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B528,
                "expected": bytes.fromhex("6000f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_policy_cleanup_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the policy-cleanup helper chain returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B544,
                "expected": bytes.fromhex("d301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_flag32_compare": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the 0x26000032 bootmgr query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B598,
                "expected": bytes.fromhex("1f000071"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_flag31_compare": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the 0x26000031 bootmgr query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B5B8,
                "expected": bytes.fromhex("1f000071"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_flag28_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the 0x26000028 bootmgr query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B5DC,
                "expected": bytes.fromhex("a001f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_selector_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the first selector branch after the 0x26000028 not-found path",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B6A0,
                "expected": bytes.fromhex("b71100b5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_lookup_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the first alt-path lookup helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B6C4,
                "expected": bytes.fromhex("6000f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_selector2_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the second alt-path selector branch",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B720,
                "expected": bytes.fromhex("88010035"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_query2_status_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the second alt-path query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B744,
                "expected": bytes.fromhex("a006f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_common_helper_status_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the common alt-path helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B770,
                "expected": bytes.fromhex("b312f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_error_global_gate_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the error-path global gate before optional reporting",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA14,
                "expected": bytes.fromhex("e80000b5"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_error_post_helpers_global_gate_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the error-path global gate after the helper pair",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA40,
                "expected": bytes.fromhex("e80000b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_error_stackflag39_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the stack flag branch after the error helper pair",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA48,
                "expected": bytes.fromhex("a8000034"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_after_bootmgr_altpath_error_followup_query_status": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the error-path follow-up query returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BB08,
                "expected": bytes.fromhex("fbcb4039"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_error_w19_sign_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the w19 sign branch before the error-path follow-up query",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BAEC,
                "expected": bytes.fromhex("1301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_error_loopback_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the error-path loopback branch before the fallback returns to the alt-path walker",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003B9F0,
                "expected": bytes.fromhex("99e2ff35"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_postloop_stackflag38_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the stack flag 0x38 branch after the alt-path loopback decision",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA04,
                "expected": bytes.fromhex("c8020035"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_after_bootmgr_altpath_reporting_helpers": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault after the post-loop reporting helper pair returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA5C,
                "expected": bytes.fromhex("760000b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_screen_call": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault immediately before the screen/error helper call",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_reporting_sign_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault at the w19 sign branch before reporting-vs-cleanup split",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA08,
                "expected": bytes.fromhex("5301f836"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_break_before_bootmgr_altpath_reporting_helper1_call": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, and fault immediately before the first reporting helper call",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_break_before_bootmgr_altpath_screen_call": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, skip the first reporting helper, and fault immediately before the screen/error helper call",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_altpath_reporting_helpers": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, skip both reporting helpers, and fault immediately after them",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA5C,
                "expected": bytes.fromhex("760000b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_after_bootmgr_altpath_cleanup_call": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, skip both reporting helpers, and fault immediately after the x22 cleanup helper returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA6C,
                "expected": bytes.fromhex("9a010034"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cleanup_call_break_before_bootmgr_altpath_cleanup_postcall_branch": {
        "description": "Keep the current bypasses, force the post-BGRT fallback branch to its success side once, skip both reporting helpers, NOP the x22 cleanup helper, and fault on the first branch after that call site",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA64,
                "expected": bytes.fromhex("2d8b0694"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA68,
                "expected": bytes.fromhex("f70100b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cleanup_call_nop_bootmgr_altpath_global_cleanup_call_break_before_bootmgr_altpath_x28_cleanup_branch": {
        "description": "Keep the current bypasses, skip both reporting helpers, NOP the x22 and global cleanup helpers, and fault on the first x28 cleanup branch that follows",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA64,
                "expected": bytes.fromhex("2d8b0694"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BAB0,
                "expected": bytes.fromhex("1a8b0694"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BAB4,
                "expected": bytes.fromhex("7c0000b4"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_nop_bootmgr_altpath_cleanup_call_nop_bootmgr_altpath_global_cleanup_call_break_before_bootmgr_altpath_global_flag_branch": {
        "description": "Keep the current bypasses, skip both reporting helpers, NOP the x22 and global cleanup helpers, and fault on the global flag branch after the x21 cleanup gate",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA64,
                "expected": bytes.fromhex("2d8b0694"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BAB0,
                "expected": bytes.fromhex("1a8b0694"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BAD8,
                "expected": bytes.fromhex("88000036"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_before_bootmgr_policy_stage1": {
        "description": "Keep the current bypasses but move the stop point back to the first post-policy runtime stage so the current divergence can be re-located",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B1F0,
                "expected": bytes.fromhex("9302f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_before_bootmgr_policy_stage2_status": {
        "description": "Keep the current bypasses and fault on the next post-policy runtime status branch after 0x102615B8 so W19 captures the branch input",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B1FC,
                "expected": bytes.fromhex("6003f837"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_before_bootmgr_policy_stage2_flag": {
        "description": "Keep the current bypasses and fault on the post-policy flag branch after the stage-2 runtime call returns",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B204,
                "expected": bytes.fromhex("28030034"),
                "replacement": UDF,
            },
        ],
    },
    "skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_nop_bootmgr_path_query_error_branch_force_stage3_success_force_post_bgrt_fallback_success_nop_bootmgr_altpath_reporting_helper1_nop_bootmgr_altpath_screen_call_break_before_bootmgr_policy_stage3_status": {
        "description": "Keep the current bypasses, follow the cbz path, and fault on the taken-path w20 status branch after 0x101AEDB8",
        "sites": [
            {
                "va": 0x101B572C,
                "expected": bytes.fromhex("4f040094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101B67F4,
                "expected": bytes.fromhex("1d000094"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x1028DC58,
                "expected": bytes.fromhex("08c018d5"),
                "replacement": NOP,
            },
            {
                "va": 0x101CC428,
                "expected": bytes.fromhex("e0013fd6"),
                "replacement": bytes.fromhex("e0031f2a"),
            },
            {
                "va": 0x101AFA2C,
                "expected": bytes.fromhex("f5079f1a"),
                "replacement": bytes.fromhex("f5031f2a"),
            },
            {
                "va": 0x1003AFEC,
                "expected": bytes.fromhex("0002f837"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B3EC,
                "expected": bytes.fromhex("7401f836"),
                "replacement": bytes.fromhex("0b000014"),
            },
            {
                "va": 0x1003B4B0,
                "expected": bytes.fromhex("5301f836"),
                "replacement": bytes.fromhex("0a000014"),
            },
            {
                "va": 0x1003BA54,
                "expected": bytes.fromhex("cf130094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003BA58,
                "expected": bytes.fromhex("e0250094"),
                "replacement": NOP,
            },
            {
                "va": 0x1003B2B4,
                "expected": bytes.fromhex("9404f837"),
                "replacement": UDF,
            },
        ],
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_patch(input_path: Path, output_path: Path, patch_name: str) -> None:
    patch = PATCHES[patch_name]
    pe = pefile.PE(str(input_path), fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase

    data = bytearray(input_path.read_bytes())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Patch: {patch_name}")
    print(f"  Description: {patch['description']}")
    print(f"  Input : {input_path}")
    print(f"  Output: {output_path}")

    for site in patch["sites"]:
        rva = site["va"] - image_base
        file_offset = pe.get_offset_from_rva(rva)
        current = bytes(data[file_offset:file_offset + 4])
        if current != site["expected"]:
            raise SystemExit(
                f"{input_path}: unexpected bytes at 0x{site['va']:X} "
                f"(offset 0x{file_offset:X}): got {current.hex()} expected {site['expected'].hex()}"
            )

        data[file_offset:file_offset + 4] = site["replacement"]
        print(
            f"  VA=0x{site['va']:X} RVA=0x{rva:X} FileOffset=0x{file_offset:X} "
            f"Before={current.hex()} After={site['replacement'].hex()}"
        )

    output_path.write_bytes(data)

    print(f"  SHA256(input )={sha256(input_path)}")
    print(f"  SHA256(output)={sha256(output_path)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Patch Windows BOOTAA64.EFI for A733 bring-up A/B tests.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--patch",
        choices=sorted(PATCHES),
        default="nop_post_setvar_trace",
        help="Patch recipe to apply.",
    )
    parser.add_argument(
        "--backup",
        type=Path,
        help="Optional backup path. If provided and the file exists, it is copied before patching output in place.",
    )
    args = parser.parse_args()

    if args.backup is not None and args.input.resolve() == args.output.resolve():
        args.backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.input, args.backup)
        print(f"Backup: {args.input} -> {args.backup}")

    apply_patch(args.input, args.output, args.patch)


if __name__ == "__main__":
    main()
