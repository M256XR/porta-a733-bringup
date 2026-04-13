# Windows direct BOOTAA64 status (2026-04-08)

Latest clean direct boot run:
- Log: D:/Projects/porta-a733-bringup/log/teraterm_2026-04-08_195908.log
- Firmware banner: Apr 8 2026 build
- Loader path: \EFI\BOOT\BOOTAA64.EFI direct, original hash
- startup.nsh: stub/no-op (no retry path)

What is now confirmed:
- The previous `No mapping` / `ConvertPages` blocker is gone.
- `BOOTAA64.EFI` loads as `ORIGINAL_OK` and enters StartImage cleanly.
- The low fixed-page request at `0x102000` succeeds.
- Later fixed allocations at `0x40000000` and `0x40080000` (0x80 pages each) also succeed.
- `WindowsBootChainSvnCheckStatus` is set successfully.
- There is still no visible `ExitBootServices` trace in this run.

Interpretation:
- The project is no longer stuck at bootmgr entry or the old low-page allocator failure.
- The current stop point is later, after bootmgr policy/setup work has started.
- UART goes silent after that stage, which currently suggests either:
  1. control moved to a graphics-only path, or
  2. a later hang that is not yet instrumented on serial.
- The installed GOP is still the synthetic headless implementation, not real HDMI
  scanout. Even if Windows starts using GOP, nothing is expected on the panel.
- In the quiet-heartbeat run (`teraterm_2026-04-08_201222.log`), there are still
  no visible `A733-EBS` or `A733-GOP` calls after direct `BOOTAA64.EFI` start.
  That makes the current blocker look like the long-standing preexisting silent
  stop, not the recent `No mapping` regression.

Current media state:
- F:/EFI/BOOT/BOOTAA64.EFI = original
- F:/EFI/Microsoft/Boot/bootmgfw.efi = original
- F:/startup.nsh = no-op stub

Post-log action already taken:
- Rebuilt firmware with quieter heartbeat/tick diagnostics.
- Rewrote SD raw firmware with the new build.
- Next log should preserve AllocatePages/GetMemoryMap lines better.

Current staged diagnostic run:
- `teraterm_2026-04-08_205245.log` showed the same silence after `WindowsBootChainSvnCheckStatus -> Success`.
- The staged `0x1003B49C -> UDF` variant did not raise an exception.
- Therefore the remaining blocker is earlier than `0x1003B49C`.

Latest staged-result finding:
- `teraterm_2026-04-08_205949.log` hit the staged `0x10054A50 -> UDF` stop-point exactly.
- The exception PC decoded as:
  - `0x23CCE8A50 = bootmgfw + 0x00054A50`
- The captured call stack also shows the immediate higher-level caller:
  - `0x23CE4AA6C = bootmgfw + 0x001B6A6C`
- This proves BOOTAA64 returns from firmware's `SetVariable` implementation back into the caller-side wrapper.
- Therefore the remaining blocker is later than the runtime-service return path itself.
- `teraterm_2026-04-08_211331.log` did not hit the staged `0x101B6A78 -> UDF` stop-point.
- The media marker confirms that `0x101B6A78` variant was actually installed.
- Therefore the remaining blocker is between `0x10054A50` and the higher-level helper call at `0x101B6A78`.
- `teraterm_2026-04-08_214828.log` also did not hit the staged `0x10054A68 -> UDF` stop-point.
- The media marker confirms that `0x10054A68` variant was actually installed.
- Therefore the remaining blocker is between `0x10054A50` and `0x10054A68`, which strongly points at the intervening `0x1028D950` call.
- A direct `0x1028D950 -> UDF` function-entry probe caused the run to stop much earlier than the stable `WindowsBootChainSvnCheckStatus` point.
- That makes the function-entry probe ambiguous, because `0x1028D950` may also be used from other paths.
- The cleaner probe is the call-site itself at `0x10054A60`.
- `teraterm_2026-04-08_220700.log` hit the staged `0x10054A60 -> UDF` stop-point exactly.
- That proves execution reaches the call-site of the suspected follow-up function.
- Combined with the earlier miss at `0x10054A68`, the best current hypothesis is:
  - the call at `0x10054A60` does not return cleanly.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the skip-and-stop variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_stop_10054A68.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x10054A68 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_220831.md`

How to read the next run:
- If the UART log shows an exception with `ELR=...10054A68`, skipping the suspected follow-up call allows execution to reach the next wrapper boundary.
- That would strongly implicate the original `0x10054A60` call as the blocker.
- If the log still goes silent without hitting `0x10054A68`, the blocker is not just the call body itself and the model needs to be revised.

Latest staged-result finding:
- `teraterm_2026-04-08_222707.log` hit the staged `0x10054A68` stop-point exactly while `0x10054A60` was NOPed out.
- This proves that skipping the call at `0x10054A60` allows BOOTAA64 to return to the next wrapper boundary.
- Therefore the current best hypothesis is now stronger:
  - the original follow-up call at `0x10054A60` is the blocker, or the blocker sits immediately inside that callee path.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next skip-and-stop variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_stop_10054A6C.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x10054A6C -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_222843.md`

How to read the next run:
- If the UART log shows an exception with `ELR=...10054A6C`, then the wrapper also gets past the next post-call step after skipping `0x10054A60`.
- If the log still goes silent before `0x10054A6C`, then the remaining issue is between `0x10054A68` and `0x10054A6C`, and the model needs to be tightened again.

Latest staged-result finding:
- `teraterm_2026-04-08_223117.log` hit the staged `0x10054A6C` stop-point exactly while `0x10054A60` was NOPed out.
- This proves that, once the `0x10054A60` follow-up call is skipped, BOOTAA64 also gets through the subsequent `0x10054A68 -> 0x100536E8` call and reaches the wrapper epilogue.
- Therefore the blocker is not the later `0x100536E8` call or the wrapper epilogue itself.
- The strongest current hypothesis remains:
  - the original follow-up call at `0x10054A60` is the blocker, or the blocker sits immediately inside that callee path.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the higher-level skip-and-stop variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_stop_101B6A78.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101B6A78 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_223808.md`

How to read the next run:
- If the UART log shows an exception with `ELR=...101B6A78`, skipping the `0x10054A60` follow-up call lets execution return through the wrapper and reach the next higher-level post-call boundary.
- That would make the original `0x10054A60` callee path the dominant blocker.
- If the log still goes silent before `0x101B6A78`, then the wrapper returns but some later step between `0x10054A6C` and `0x101B6A78` still needs to be isolated.

Latest staged-result finding:
- `teraterm_2026-04-08_224003.log` hit the staged `0x101B6A78` stop-point exactly while `0x10054A60` was NOPed out.
- This proves that skipping the `0x10054A60` follow-up call lets execution return through the wrapper and reach the next higher-level caller's next call boundary.
- That makes the original `0x10054A60` callee path the dominant current blocker.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the free-run bypass variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_only.EFI`
  - patches:
    - `0x10054A60 -> NOP`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_224153.md`

How to read the next run:
- If the UART log advances to `BCD` or another later Windows stage, then bypassing the `0x10054A60` callee meaningfully unblocks the boot path.
- If the log still dies silently, then `0x10054A60` is only the first blocker and the next one needs to be isolated from the new later position.

Latest staged-result finding:
- `teraterm_2026-04-08_224422.log` did not stop silently.
- Instead, after the `0x10054A60` bypass, bootmgfw advanced to a new exception with:
  - `ELR=0x0000000000000000`
  - caller frames including `bootmgfw + 0x001CC42C` and `bootmgfw + 0x00057210`
- Disassembly shows that `bootmgfw + 0x001CC428` is `blr x15`, and the null `ELR` strongly indicates a null callback dispatch on that instruction.
- This matches older patch archaeology that already referred to `skip_null_callback_101cc428`.
- Therefore the current path is:
  - bypassing `0x10054A60` exposes the next blocker, a null callback call at `0x101CC428`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the combined free-run bypass variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_224854.md`

How to read the next run:
- If the UART log now advances to `BCD` or another later Windows stage, then the dominant blockers on the current path were:
  - the `0x10054A60` follow-up callee
  - the null callback dispatch at `0x101CC428`
- If a different later exception appears, that new site becomes the next natural blocker to isolate.

Latest staged-result finding:
- `teraterm_2026-04-08_230053.log` reached the real Windows Boot Manager error screen again:
  - `File: \EFI\Microsoft\Boot\BCD`
  - `Status: 0xc000000d`
- That means the current combined bypasses are sufficient to recover the old "bootmgr reached BCD" milestone on the cleaner Apr 8 firmware path.
- Therefore the dominant early blockers on the current path were:
  - the `0x10054A60` follow-up callee
  - the null callback dispatch at `0x101CC428`
- The remaining problem is no longer the early boot path.
- The remaining problem is now at the BCD / Windows-media semantics layer.

Current media observation:
- `F:\EFI\Microsoft\Boot\BCD` exists and `bcdedit /store ... /enum all` can enumerate it successfully.
- That suggests the store is not grossly unreadable on Windows itself.
- However, the inspection command rewrote the on-media store timestamp/hash while preserving the same logical entries, so the current mounted `BCD` is now a Windows-normalized variant of the same store.

Latest staged-result finding:
- `teraterm_2026-04-08_232201.log` reproduced the same `\EFI\Microsoft\Boot\BCD / 0xc000000d` result after the on-host `bcdedit` inspection/normalization step.
- Therefore the normalization itself did not change the observed Windows Boot Manager outcome.
- The remaining open question is whether the logical BCD variant matters, especially the older store that includes:
  - `configaccesspolicy Default`
  - `custom:2600002a Yes`

Current staged BCD experiment:
- Backed up the normalized current store as:
  - `F:\EFI\Microsoft\Boot\BCD.pre_enum_normalized.20260408-232334.bak`
- Replaced `F:\EFI\Microsoft\Boot\BCD` with `BCD.pre_restore_test.bak`.
- The active BCD is now the variant that explicitly carries `configaccesspolicy Default` and `custom:2600002a Yes`.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_232342.md`

How to read the next run:
- If the result changes away from `0xc000000d`, then the BCD logical variant matters and `configaccesspolicy`-related entries are part of the remaining issue.
- If the result stays at `0xc000000d`, then BCD logical contents are less likely to be the main discriminator and the next step should move back to later bootmgr path instrumentation.

Latest staged-result finding:
- `teraterm_2026-04-08_232906.log` still reached the same Windows Boot Manager screen:
  - `File: \EFI\Microsoft\Boot\BCD`
  - `Status: 0xc000000d`
- That means swapping the active BCD to the older `pre_restore_test` logical variant did not change the observed outcome.
- Therefore the remaining discriminator is less likely to be the BCD store contents themselves and more likely to be a later bootmgr branch that sits after BCD access succeeds far enough to reach the same error screen.
- Older patch archaeology already points at a `ConfigAccessPolicy`-related missing-path flag clear at `0x101AFA2C`.
- The current next step is to reintroduce only that one later-path bypass on top of the two already-proven early-path bypasses.

Current staged diagnostic run:
- Restored the active `F:\EFI\Microsoft\Boot\BCD` from:
  - `F:\EFI\Microsoft\Boot\BCD.pre_enum_normalized.20260408-232334.bak`
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_233337.md`

How to read the next run:
- If the result changes from `0xc000000d` to a later/different Windows error, the `0x101AFA2C` ConfigAccessPolicy-related branch was still active on the current clean path and mattered.
- If the result stays at `0xc000000d`, then the next discriminator is deeper than `0x101AFA2C` and the next step should move forward to the older post-`0x1003AFEC` / `0x1003B3EC` ladder.

Latest staged-result finding:
- `teraterm_2026-04-08_233844.log` still produced the same Windows Boot Manager screen:
  - `File: \EFI\Microsoft\Boot\BCD`
  - `Status: 0xc000000d`
- That means reintroducing the older ConfigAccessPolicy-related bypass at `0x101AFA2C` did not change the outcome on the current clean path.
- Therefore the current divergence is deeper than the `0x101AFA2C` gate.
- The next useful question is whether the current path reaches the older post-query checkpoint at `0x1003AFEC` at all.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_stop_1003AFEC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_234009.md`

How to read the next run:
- If the next log faults at `ELR=...1003AFEC`, then the current clean path has rejoined the older post-query ladder and the next discriminator moves to the `0x1003B3EC` / `0x1003B4B0` area.
- If the next log still falls straight into `\EFI\Microsoft\Boot\BCD / 0xc000000d`, then the current path diverges before `0x1003AFEC` and the next breakpoint should move back to `0x1003AF38`.

Latest staged-result finding:
- `teraterm_2026-04-08_234500.log` did fault at `ELR=...1003AFEC`.
- That confirms the current clean path has rejoined the older post-query ladder.
- The trapped register state also showed:
  - `X0 = 0xC000000D`
- Disassembly around the trap point is:
  - `0x1003AFE8: bl #0x101B3D48`
  - `0x1003AFEC: tbnz w0, #0x1f, #0x1003B02C`
  - `0x1003AFF0: ldr w8, [sp, #0x60]`
  - `0x1003AFF4: tbz w8, #0, #0x1003B02C`
- Therefore the current `0xc000000d` is the status returned by `0x101B3D48`, not a separate later screen-only artifact.
- The next useful question is not "does the path reach the old ladder?" anymore.
- The next useful question is: if that immediate error branch at `0x1003AFEC` is bypassed once, what does the flag test at `0x1003AFF4` do?

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003AFF4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003AFF4 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260408_235117.md`

How to read the next run:
- If the next log faults at `ELR=...1003AFF4`, then bypassing the immediate `0xc000000d` error branch exposes the following bit-flag gate as the next discriminator.
- If the next run still lands on the same visible `BCD / 0xc000000d` result without reaching `0x1003AFF4`, then the model is wrong and the branch did not behave as expected on the live path.

Latest staged-result finding:
- `teraterm_2026-04-08_235719.log` did fault at `ELR=...1003AFF4`.
- The trapped register state showed:
  - `X0 = 0xC000000D`
  - `X8 = 0x0000000000000000`
- That means the immediate `0x1003AFEC` error branch can be bypassed, but the following bitfield gate still naturally takes the branch target because bit 0 in `[sp+0x60]` is clear.
- In plain terms, the current path is now:
  - helper returns `0xc000000d`
  - ignore that one error branch once
  - next flag still says "go to the alternate path"

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B02C_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B02C -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_000109.md`

Prepared next-step variants:
- `...stop_1003B040_udf.EFI`
- `...stop_1003B098_udf.EFI`
- `...stop_1003B0B8_udf.EFI`
- These are already generated locally so the next turn can move quickly without rebuilding variants from scratch.

How to read the next run:
- If the next log faults at `ELR=...1003B02C`, the current path naturally reaches the alternate branch target after the cleared-bit flag test.
- If it does not, then the current understanding of the `0x1003AFF4` gate is incomplete and the branch behavior needs to be rechecked.

Latest staged-result finding:
- `teraterm_2026-04-09_002818.log` did fault at `ELR=...1003B02C`.
- That confirms the path now naturally follows the alternate branch target after the `0x1003AFF4` bit-0 flag test.
- The trap-state values at that point were still:
  - `X0 = 0xC000000D`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- In plain terms:
  - ignore the immediate `0xc000000d` branch once
  - next flag is still clear
  - execution naturally turns into the alternate post-query path at `0x1003B02C`

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B040_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B040 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_003057.md`

How to read the next run:
- `0x1003B02C` is the call into the next query block.
- If the next log faults at `ELR=...1003B040`, then the current live path reaches the status branch immediately after the `0x2600002A` property query.
- That will tell whether this alternate path is failing because the query status itself is negative, or because the returned flag byte is clear.

Latest staged-result finding:
- `teraterm_2026-04-09_003351.log` did fault at `ELR=...1003B040`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
- That means the `0x2600002A` property query itself is returning a negative status on the current live path.
- So one half of the question is answered:
  - this alternate path is not merely failing because some later byte flag is clear
  - it is already seeing a direct query failure first

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_nop_1003B040_stop_1003B048_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B040 -> NOP`
    - `0x1003B048 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` remains the no-op stub to avoid retry contamination.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_003823.md`

How to read the next run:
- This run ignores the immediate negative status from the `0x2600002A` query once.
- If the next log faults at `ELR=...1003B048`, the register state will show the actual byte loaded from `[sp+0x31]`.
- That tells whether the query also failed to populate the flag byte, or whether the byte was set despite the failing status code.

Latest staged-result finding:
- `teraterm_2026-04-09_004123.log` did fault at `ELR=...1003B048`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means both gates on this alternate path currently fail:
  - the `0x2600002A` query itself returns a negative status
  - the byte loaded from `[sp+0x31]` is also zero
- So the natural live path is not the forced-success body at `0x1003B04C`.
- The natural next branch target is `0x1003B06C`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B06C_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B06C -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_004604.md`

How to read the next run:
- This run does not force the `0x2600002A` query or the `[sp+0x31]` byte flag to succeed.
- It simply stops at the natural branch target that both current failure conditions point to.
- If the next log faults at `ELR=...1003B06C`, then the live path is cleanly rejoined at the next alternate-path gate.

Latest staged-result finding:
- `teraterm_2026-04-09_005046.log` did fault at `ELR=...1003B06C`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means the natural alternate path now does exactly what the static branch structure suggests:
  - the `0x2600002A` query returns a negative status
  - the returned byte is still clear
  - `w20` is also zero
- So the path does not take the `w20!=0` side-path through `0x10043C38`.
- The natural next work is the query/status pair at `0x1003B088-0x1003B098`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B098_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B098 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_005220.md`

How to read the next run:
- If the next log faults at `ELR=...1003B098`, the path has reached the status branch immediately after the next alternate-path query at `0x101B1530`.
- That will show whether the next discriminator is another negative status, or whether this branch family finally gets a non-negative return.

Latest staged-result finding:
- `teraterm_2026-04-09_005434.log` did fault at `ELR=...1003B098`.
- The trapped register state showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X24 = 0x23CF984C4`
- That means the next alternate-path helper/query pair reaches its return-status gate and returns success.
- So this branch family is no longer failing at `0x1003B098`.
- The natural next work is the following call:
  - `0x1003B0B4: bl #0x1003E290`
  - `0x1003B0B8: tbz w0, #0x1f, #0x1003B12C`

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B0B8_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B0B8 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_005537.md`

How to read the next run:
- If the next log faults at `ELR=...1003B0B8`, then the remaining discriminator on this path is the return status of `0x1003E290`.
- A non-negative `X0` there means the code naturally falls through into the `0x1003B12C` success side of this local branch family.

Latest staged-result finding:
- `teraterm_2026-04-09_005744.log` did fault at `ELR=...1003B0B8`.
- The trapped register state showed:
  - `X0 = 0xC000000D`
  - `X19 = 0`
  - `X20 = 0`
- That means the next local discriminator on this path is another direct negative return, this time from `0x1003E290`.
- So the branch family now looks like:
  - `0x2600002A` query fails
  - next helper/query pair succeeds
  - `0x1003E290` then returns `0xc000000d`

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B0C0_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B0C0 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_005903.md`

How to read the next run:
- This run stops immediately after `ldrb w8, [sp, #0x30]`.
- If the next log faults at `ELR=...1003B0C0`, then `X8` will tell whether this negative `0x1003E290` status is followed by a clear byte that sends control straight to `0x1003B12C`, or by a set byte that keeps the deeper side-path alive.

Latest staged-result finding:
- `teraterm_2026-04-09_010124.log` did fault at `ELR=...1003B0C0`.
- The trapped register state showed:
  - `X0 = 0xC000000D`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means the negative return from `0x1003E290` is paired with a clear `[sp+0x30]` byte.
- So the natural live path does not take the deeper side-path through `0x1003B0C8`.
- It falls directly to `0x1003B12C`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B12C_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B12C -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_010220.md`

How to read the next run:
- If the next log faults at `ELR=...1003B12C`, then the current natural path has collapsed all the way through this local branch family to the shared join point.
- That would mean the next useful question is no longer which local side-branch is taken, but what state the code brings into the shared continuation at `0x1003B12C`.

Latest staged-result finding:
- `teraterm_2026-04-09_010449.log` did fault at `ELR=...1003B12C`.
- The trapped register state showed:
  - `X0 = 0xC000000D`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That confirms the current natural path really does collapse into the shared join point carrying the negative `0x1003E290` return forward in `w20`.
- The next useful discriminator is no longer the local branch family itself.
- The next useful discriminator is the first shared-continuation query at:
  - `0x1003B150: bl #0x101B11E8`
  - followed by the status check at `0x1003B154`

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B154_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B154 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_010729.md`

How to read the next run:
- If the next log faults at `ELR=...1003B154`, then `X0` will show the return status of the `0x11000084` query/helper pair and `X19` will show whether a result pointer was produced into `[sp+0x68]`.

Latest staged-result finding:
- `teraterm_2026-04-09_010952.log` did fault at `ELR=...1003B154`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x11000084`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X22 = 0x400010A0`
- That means the first shared-continuation query/helper pair also fails on the live path.
- It returns `0xC0000225`, and it does not populate a result pointer into `[sp+0x68]`.
- So the natural path skips the `0x101B0808` cleanup helper and falls through to `0x1004C1F0`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B178_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B178 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_011115.md`

How to read the next run:
- This run stops immediately after `bl #0x1004C1F0`.
- If the next log faults at `ELR=...1003B178`, then `X0` and `X19` will show whether that shared-continuation helper also fails, or whether the path finally flips back into a non-negative state before `0x1003B1D0`.

Latest staged-result finding:
- `teraterm_2026-04-09_011331.log` did fault at `ELR=...1003B178`.
- The trapped register state showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means `0x1004C1F0` returns success on the live path.
- So the shared continuation flips back to a non-negative state here and naturally takes the branch to `0x1003B1D0`.
- The next useful discriminator is the return from `0x10264838`, checked at `0x1003B1F0`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B1F0_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B1F0 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_011522.md`

How to read the next run:
- If the next log faults at `ELR=...1003B1F0`, then `X0`/`X19` will show whether `0x10264838` is the next failure point or whether the path keeps flowing into the subsequent `0x102615B8` query.

Latest staged-result finding:
- `teraterm_2026-04-09_011832.log` did fault at `ELR=...1003B1F0`.
- The trapped register state showed:
  - `X0 = 0`
  - `X8 = 2`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means `0x10264838` returns success on the live path.
- So the path continues into the next query/helper call at `0x102615B8`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B1FC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B1FC -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_011955.md`

How to read the next run:
- If the next log faults at `ELR=...1003B1FC`, then `X0` will show the return status from `0x102615B8`.
- A negative `X0` means this new helper/query is the next live-path blocker.
- A non-negative `X0` means the next discriminator becomes the byte loaded from `[sp+0x31]` at `0x1003B200`.

Latest staged-result finding:
- `teraterm_2026-04-09_012351.log` did fault at `ELR=...1003B1FC`.
- The trapped register state showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means `0x102615B8` returns success on the live path.
- So the next discriminator is no longer the status return; it is the byte loaded from `[sp+0x31]` at `0x1003B200`, with the next branch at `0x1003B204`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B204_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B204 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_012503.md`

How to read the next run:
- If the next log faults at `ELR=...1003B204`, then `X8` will show the byte loaded from `[sp+0x31]`.
- `X8 = 0` means the natural path takes `cbz w8, #0x1003B268`.
- `X8 != 0` means the path enters the deeper side-path at `0x1003B208`.

Latest staged-result finding:
- `teraterm_2026-04-09_012849.log` did fault at `ELR=...1003B204`.
- The trapped register state showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means the byte loaded from `[sp+0x31]` is clear on the live path.
- So the natural path takes the `cbz w8, #0x1003B268` branch into the shared continuation block.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B268_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B268 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_013046.md`

How to read the next run:
- If the next log faults at `ELR=...1003B268`, then the live path has entered the shared continuation after the stage-3 selector.
- The next useful question becomes whether `0x101AED08` / `0x101AEDB8` preserve the prior `w20=0xC000000D` state or overwrite it with a new status.

Latest staged-result finding:
- `teraterm_2026-04-09_013257.log` did fault at `ELR=...1003B268`.
- The trapped register state showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means the live path has fully entered the shared continuation after the stage-3 selector.
- At this exact stop we have not yet executed the `0x101AED08` / `0x101AEDB8` pair, so the carried `w20=0xC000000D` is still just the incoming status from the earlier shared tail.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B298_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B298 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_013455.md`

How to read the next run:
- If the next log faults at `ELR=...1003B298`, then `X0` will show the return status from `0x101AEDB8`.
- A non-negative `X0` means the helper pair succeeded and the next effective gate becomes whether `w20` stays negative enough to force `0x1003B344`.
- A negative `X0` means this helper pair is itself the next live-path failure source.

Latest staged-result finding:
- `teraterm_2026-04-09_013701.log` did fault at `ELR=...1003B298`.
- The trapped register state showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- That means the `0x101AED08` / `0x101AEDB8` helper pair also succeeds on the live path.
- Because `tbz w0, #0x1f, #0x1003B2A4` is taken, the `cmp/csel` block at `0x1003B29C..0x1003B2A0` is skipped and the carried `w20=0xC000000D` remains unchanged.
- So the next natural branch is `tbnz w20, #0x1f, #0x1003B344`.

Prepared next diagnostic run:
- The next BOOTAA64 variant has already been generated locally:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B344_udf.EFI`
- At the moment of analysis, the live media was not mounted on the host anymore:
  - `Get-Disk` showed `Disk 3 / Generic STORAGE DEVICE / No Media`
- So this next variant is ready, but not yet staged onto the removable media.

How to read the next run:
- Once the media is remounted and the `0x1003B344` stop-point variant is staged, a fault at `ELR=...1003B344` will confirm the shared continuation is taking the negative-status error leg.
- The next useful question there becomes whether the cleanup/reporting subpath (`0x1003F878`, `0x1003F4A0`, `0x101C47B8`) preserves `0xC0000225` style reporting or mutates the carried `0xC000000D`.

Latest staged-result finding:
- `teraterm_2026-04-09_014233.log` did fault at `ELR=...1003B344`.
- The trapped register state showed:
  - `X0 = 0x000000023CC9AF20`
  - `X1 = 0x000000023CC9AF20`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- That confirms the shared continuation is taking the negative-status error leg.
- At the exact trap point, `mov x0, x21` has not executed yet, so the nonzero `X0`/`X1` values are just incoming register garbage from the previous path and not the cleanup call input.
- The next real discriminator is therefore after the `0x1003F878`, `0x1003F4A0`, `0x101C47B8` call sequence, at `0x1003B358`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B358_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B358 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_014336.md`

How to read the next run:
- If the next log faults at `ELR=...1003B358`, then `X0` will show the return value from `0x101C47B8`.
- `X0 = 0` means the path falls through to the hardcoded `0xC0000225` reporting block at `0x1003B35C`.
- `X0 != 0` means the path jumps to `0x1003B3A0` and the next failure source is deeper in that reporting leg.

Latest staged-result finding:
- `teraterm_2026-04-09_014557.log` did fault at `ELR=...1003B358`.
- The trapped register state showed:
  - `X0 = 0x000000023CFAE30A`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So the `cbnz x0, #0x1003B3A0` branch is taken on the live path.
- That means this error leg does not fall through to the hardcoded `0xC0000225` reporting block at `0x1003B35C`.
- The next live-path discriminator is now the deeper reporting subpath entry at `0x1003B3A0`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B3A0_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B3A0 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_014831.md`

How to read the next run:
- If the next log faults at `ELR=...1003B3A0`, then the negative-status cleanup/reporting leg has entered the deeper reporting subpath.
- The next useful value there is the return status from `0x101E8470`, which decides whether that deeper leg reports another negative status or continues into its local success path.

Latest staged-result finding:
- `teraterm_2026-04-09_015218.log` did fault at `ELR=...1003B3A0`.
- The trapped register state showed:
  - `X0 = 0x000000023CFAE30A`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- This confirms the live path has entered the deeper reporting subpath selected by the nonzero return from `0x101C47B8`.
- At this exact stop, the `ldr w1, [sp, #0x78]` has not executed yet, so the next useful discriminator is the return status from `0x101E8470`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B3AC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B3AC -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_015425.md`

How to read the next run:
- If the next log faults at `ELR=...1003B3AC`, then `X0`/`X19` show the return status from `0x101E8470`.
- A non-negative status sends the path into the local success side at `0x1003B3E4`.
- A negative status keeps the path on the reporting/error side starting at `0x1003B3B0`.

Latest staged-result finding:
- `teraterm_2026-04-09_020835.log` did fault at `ELR=...1003B3AC`.
- The trapped register state showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- That means the `0x101E8470` helper returns success on the live path.
- So the branch `tbz w19, #0x1f, #0x1003B3E4` is taken and the path enters the local success-side block at `0x1003B3E4`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B3E4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B3E4 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_021011.md`

How to read the next run:
- If the next log faults at `ELR=...1003B3E4`, then the deeper reporting branch has resolved into its local success-side continuation.
- The next useful question is whether that continuation reaches the `0x16000048` property query around `0x1003B480..0x1003B49C` cleanly or encounters a new failure earlier.

Latest staged-result finding:
- `teraterm_2026-04-09_021251.log` did fault at `ELR=...1003B3E4`.
- The trapped register state showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- This confirms the deeper reporting subpath resolved into its local success-side continuation.
- Disassembly shows that block immediately reports the carried `w20` status and branches into the shared reporting tail, so there is little value in tracing further down that natural error leg.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_stop_1003B2D4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_021742.md`

How to read the next run:
- This is no longer the untouched natural path.
- It deliberately clears the carried `0xC000000D` at `0x1003B134` to force the code into the positive-side path after `0x1003B2B4`.
- If the next log faults at `ELR=...1003B2D4`, then the next live blocker is the `0x26000042` property query that sits behind the current `w20` failure.

Latest staged-result finding:
- `teraterm_2026-04-09_022001.log` did fault at `ELR=...1003B2D4`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x26000042`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- This confirms the forced positive-side probe reaches the `0x26000042` property query and that query itself fails with `0xC0000225`.
- So the next live blocker behind the carried `w20` failure is another missing/unsupported boot-environment property path.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a refined forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_stop_1003B2DC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_022139.md`

How to read the next run:
- This run deliberately ignores the `0x26000042` query failure once.
- If the next log faults at `ELR=...1003B2DC`, then `X8` shows whether the returned byte flag is also clear.
- `X8 = 0` means this path would still fall back into `0x1003B344` even after ignoring the status code.
- `X8 != 0` means the next gate becomes `0x101AEA58` / `0x1600007E` behind it.

Latest staged-result finding:
- `teraterm_2026-04-09_022351.log` did fault at `ELR=...1003B2DC`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x26000042`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means the forced positive-side probe still sees the returned byte flag clear after the `0x26000042` query.
- So even if the query status failure is ignored, this path would still naturally fall back into `0x1003B344` at the `cbz w8` gate.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a deeper forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_stop_1003B2E4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2E4 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_022509.md`

How to read the next run:
- This run deliberately ignores both the `0x26000042` status failure and the zero-byte gate behind it.
- If the next log faults at `ELR=...1003B2E4`, then `X0` shows the return value from `0x101AEA58`.
- `X0` bit0 clear means the path still falls back into `0x1003B344`.
- `X0` bit0 set means the next live gate becomes the later `0x1600007E` query at `0x1003B2F8`.

Latest staged-result finding:
- `teraterm_2026-04-09_022707.log` did fault at `ELR=...1003B2E4`.
- The trapped register state showed:
  - `X0 = 0x1`
  - `X1 = 0x26000042`
  - `X19 = 0`
  - `X20 = 0`
- That means `0x101AEA58` returns a value with bit0 set on the forced positive-side probe.
- So this gate does not send control back to `0x1003B344`; the next live gate is now the later `0x1600007E` query at `0x1003B2F8`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a deeper forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_stop_1003B2FC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_022816.md`

How to read the next run:
- This run deliberately carries the forced positive probe one step further.
- If the next log faults at `ELR=...1003B2FC`, then `X0` shows whether the `0x1600007E` query itself fails.
- A negative `X0` means yet another missing boot-environment property gate.
- A non-negative `X0` shifts the next gate to the returned byte at `0x1003B300`.

Latest staged-result finding:
- `teraterm_2026-04-09_023017.log` did fault at `ELR=...1003B2FC`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x1600007E`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means the forced positive-side probe reaches the later `0x1600007E` property query and that query itself also fails with `0xC0000225`.
- So this is another missing/unsupported boot-environment property gate behind the earlier `0x26000042` failure.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a deeper forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_nop_1003B2FC_stop_1003B304_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_023139.md`

How to read the next run:
- This run deliberately ignores the `0x1600007E` status failure once.
- If the next log faults at `ELR=...1003B304`, then `X8` shows whether the returned byte flag is also clear.
- `X8 = 0` means the later `0x1600007E` gate also lacks the positive flag and still collapses into `0x1003B344`.
- `X8 != 0` means the next live gate becomes `0x10043B48` behind it.

Latest staged-result finding:
- `teraterm_2026-04-09_023407.log` did fault at `ELR=...1003B304`.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x1600007E`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- That means the forced positive-side probe still sees the returned byte flag clear after the later `0x1600007E` query.
- So even if that query status failure is ignored, this path would still naturally fall back into `0x1003B344` at the `cbz w8` gate.

Latest staged-result finding:
- `teraterm_2026-04-09_023743.log` did fault at `ELR=...1003B31C`.
- The trapped register state showed:
  - `X0 = 0xC000000D`
  - `X19 = 0xC000000D`
  - `X20 = 0`
  - `X21 = 0`
- That means after forcing past the `0x26000042` and `0x1600007E` gates, the later helper `0x10043B48` still returns `0xC000000D`.
- The code at this point is no longer choosing between deep subpaths; it is already in the report-and-exit tail for that status.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a deeper forward-probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_nop_1003B2FC_nop_1003B304_clear_w19_1003B318_stop_1003BA08_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BA08 -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_024026.md`

How to read the next run:
- This run deliberately clears the later `0x10043B48 -> 0xC000000D` status once.
- If the next log faults at `ELR=...1003BA08`, then we have proven the current natural path has no more hidden gates before the shared tail cleanup/reporting block.
- From there, the next question becomes whether the shared tail itself invokes another firmware-dependent path or merely performs terminal cleanup.

Latest staged-result finding:
- `teraterm_2026-04-09_024231.log` did fault at `ELR=...1003BA08`.
- The trapped register state showed:
  - `X0 = 0`
  - `X1 = 0x50`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
- That means after clearing the later `0x10043B48 -> 0xC000000D` status once, the probe reaches the shared report/cleanup tail with no additional hidden gate before it.
- At `0x1003BA08`, `w19` is clear, so the natural tail path takes the local cleanup/report block beginning at `0x1003BA30`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now a deeper shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_nop_1003B2FC_nop_1003B304_clear_w19_1003B318_stop_1003BA5C_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BA5C -> UDF`
- `bootmgfw.efi` remains original.
- `startup.nsh` is kept as-is.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_024519.md`

How to read the next run:
- This run stops at `0x1003BA5C`, after the local cleanup/report prefix at `0x1003BA30..0x1003BA58`.
- If the next log faults at `ELR=...1003BA5C`, then `X22` decides whether the tail performs an `x22`-based cleanup branch or falls through to `0x1003BA68`.


Latest staged-result finding:
- `teraterm_2026-04-09_025052.log` did fault at `ELR=...1003BA5C`.
- The trapped register state showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- That means the shared cleanup tail executes the `x22` cleanup call at `0x1003BA60..0x1003BA64` and then reaches the `cbz x23` gate at `0x1003BA68`.
- So there is no hidden side-path here: `x22` is live, `x23` is currently null.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BA68_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BA68 -> UDF`
- `bootmgfw.efi` remains original.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_025343.md`

How to read the next run:
- This run stops at `0x1003BA68`, immediately after the `x22` cleanup call.
- If the next log faults at `ELR=...1003BA68`, then `X23` decides whether the tail skips directly to `0x1003BAA4` or enters the `x23`/`w26` cleanup loop.


Latest staged-result finding:
- `teraterm_2026-04-09_025621.log` did fault at `ELR=...1003BA68`.
- The trapped register state showed:
  - `X0 = 0`
  - `X1 = 0`
  - `X8 = 0x40000C50`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- That means the shared cleanup tail takes the `cbz x23` fallthrough.
- So the `x23` cleanup loop is skipped entirely and the next natural gate is `0x1003BAA4`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BAA4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BAA4 -> UDF`
- `bootmgfw.efi` remains original.
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_025817.md`


Latest staged-result finding:
- `teraterm_2026-04-09_030001.log` did fault at `ELR=...1003BAA4`.
- The trapped register state showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- That means the shared cleanup tail has already skipped the `x23` cleanup loop.
- The next natural gate is the optional free block at `0x1003BAA4..0x1003BAB0`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BAB4_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BAB4 -> UDF`
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_030150.md`


Latest staged-result finding:
- `teraterm_2026-04-09_030409.log` did fault at `ELR=...1003BAB4`.
- The trapped register state showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
  - `X28 = 0`
- That means the optional free block at `0x1003BAA4..0x1003BAB0` is also effectively skipped.
- The next natural gate is `cbz x21` at `0x1003BAC0`.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BAC0_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BAC0 -> UDF`
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_030546.md`


Latest staged-result finding:
- `teraterm_2026-04-09_030735.log` did fault at `ELR=...1003BAC0`.
- The trapped register state showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
  - `X28 = 0`
- That means the `cbz x21` gate is also taken, so the `x21` cleanup call is skipped.
- The next natural gate is the shared-tail state block at `0x1003BACC`.


Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BACC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BACC -> UDF`
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_030848.md`


Latest staged-result finding:
- `teraterm_2026-04-09_031037.log` did fault at `ELR=...1003BACC`.
- The trapped register state showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X27 = 0`
  - `X28 = 0`
- That means the shared tail has entered the final state/update block at `0x1003BACC`.
- The next question is whether the optional `0x10289958` cleanup and `0x10063FA8` complete cleanly before the terminal `w19/w27` split.

Current staged diagnostic run:
- BOOTAA64.EFI on `F:` is now the next shared-tail probe variant:
  - source: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BAEC_udf.EFI`
  - patches:
    - `0x10054A60 -> NOP`
    - `0x101CC428 -> mov w0, wzr`
    - `0x101AFA2C -> mov w21, wzr`
    - `0x1003AFEC -> NOP`
    - `0x1003B134 -> mov w20, wzr`
    - `0x1003B2D4 -> NOP`
    - `0x1003B2DC -> NOP`
    - `0x1003B2FC -> NOP`
    - `0x1003B304 -> NOP`
    - `0x1003B318 -> mov w19, wzr`
    - `0x1003BAEC -> UDF`
- staged media snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_031217.md`

## 2026-04-09 03:15 JST - state/update block did not reach 0x1003BAEC

- `teraterm_2026-04-09_031548.log` ended at `WindowsBootChainSvnCheckStatus -> Success` with no `A733-EXC`.
- That means the previously staged `0x1003BAEC -> UDF` was not reached in the captured run.
- The most likely live blocker is now inside the `0x1003BACC` state/update block before `0x1003BAEC`.
- Disassembly shows:
  - `0x1003BACC`: load global state
  - `0x1003BAD8`: `tbz w8,#0,#0x1003BAE8`
  - `0x1003BADC`: optional cleanup/store block
  - `0x1003BAE4`: optional call `0x10289958`
  - `0x1003BAE8`: call `0x10063FA8`
  - `0x1003BAEC`: next branch gate
- To separate the cases, staged a combined probe:
  - `0x1003BADC -> UDF`
  - `0x1003BAEC -> UDF`
- If bit0 is set and the path enters the optional cleanup block, the next run should trap at `ELR=...1003BADC`.
- If bit0 is clear and the path survives to the post-helper gate, it should trap at `ELR=...1003BAEC`.
- New staged source:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BADC_and_1003BAEC_udf.EFI`
- New staged snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_031838.md`

## 2026-04-09 03:20 JST - final state block exits to 0x1003BB0C path

- `teraterm_2026-04-09_032036.log` faulted at `ELR=...1003BAEC`.
- Registers at the branch gate were:
  - `X19=0`
  - `X20=0`
  - `X21=0`
  - `X22=0x400010A0`
  - `X23=0`
  - `X27=0`
  - `X28=0`
- This proves the `0x1003BACC` state/update block completed and control reached the post-helper split at `0x1003BAEC`.
- Since `w19` is non-negative and `w27==0`, the natural path is `0x1003BB0C`.
- Next staged split probe:
  - keep `0x1003BADC -> UDF` to catch the optional cleanup block if it ever becomes active
  - use `0x1003BB14 -> UDF` to inspect the final helper result (`x0`) and loaded state word (`w8`) after `0x101AE9C8`
- New staged source:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_nop_1003B2FC_nop_1003B304_clear_w19_1003B318_stop_1003BADC_and_1003BB14_udf.EFI`

## 2026-04-09 03:24 JST - final shared-tail branch resolves to local success path

- `teraterm_2026-04-09_032449.log` faulted at `ELR=...1003BB14`.
- The relevant state at that point was:
  - `X0=0x23CF984C0`
  - `X8=0x8001`
  - `X19=0`
  - `X20=0`
  - `X21=0`
  - `X22=0x400010A0`
  - `X23=0`
  - `X27=0`
  - `X28=0`
- Interpretation:
  - `0x101AE9C8` returned a valid context pointer in `x0`
  - the loaded state word has bit5 clear (`w8=0x8001`), and `w27==0`
  - so the final branch at `0x1003BB14/18` does **not** take the error leg `0x1003BBBC`
  - the natural path is the local success/report sequence `0x1003BB1C..0x1003BB44`, then normal return at `0x1003BB48..0x1003BB78`
- Conclusion: with the current bypass set, this function's hidden gates are effectively resolved.
- Next step is no longer another intra-function stop; the next staged run should remove the stop probes and observe the next natural blocker after this function returns.

## 2026-04-09 03:28 JST - bootmgfw now returns EFI_SUCCESS to BDS

- `teraterm_2026-04-09_032908.log` no longer faults inside the previously traced function.
- The loader progresses past `WindowsBootChainSvnCheckStatus`, reaches the normal image exit path, and returns to firmware:
  - `gBS->Exit Status=Success ExitDataSize=0`
  - `StartImage watch end Status=Success`
  - `EfiBootManagerBoot returned EFI_SUCCESS`
- After that, BDS resumes variable enumeration and console wait-loop activity instead of handing off to Windows.
- Interpretation: the current bypass set clears the traced bootmgfw function, but bootmgfw as a whole is now choosing a clean `Exit(EFI_SUCCESS)` path back to firmware rather than proceeding into OS handoff.
- Next diagnostic change is in firmware, not the loader patch set:
  - `CoreExit()` now logs image base/path and any exit text for the watched image.
- Firmware rebuilt and SD rewritten with the new `CoreExit()` diagnostics.

## 2026-04-09 03:35 JST - bootmgfw entry returns EFI_SUCCESS to firmware

- `teraterm_2026-04-09_033642.log` confirms the watched image itself returned cleanly:
  - `gBS->Exit Status=Success ExitDataSize=0`
  - `gBS->Exit ImageHandle=23DBFAA98 Base=23CC94000 Size=0x32B000 Parent=0 Started=1`
  - `gBS->Exit path=\EFI\BOOT\BOOTAA64.EFI`
  - `StartImage watch end Status=Success`
  - `EfiBootManagerBoot returned EFI_SUCCESS`
- This clarifies an important point: the current bypass set is no longer crashing inside bootmgfw; instead the BOOTAA64 entry point returns `EFI_SUCCESS` to DxeCore, which then performs `CoreExit()` on its behalf.
- Therefore the forward-probe patch `clear_w19_1003B318` is not a real fix. It suppresses the negative status from `0x10043B48`, and that success then propagates all the way out to a clean firmware return path.
- Next staged probe moves from the deep shared-tail function into `0x10043B48` itself.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_clear_w20_1003B134_nop_1003B2D4_nop_1003B2DC_nop_1003B2FC_nop_1003B304_stop_10043B70_udf.EFI`
- New stop meaning:
  - `0x10043B70 -> UDF` catches the return from the first sub-call inside `0x10043B48` and shows whether the `0xC000000D` originates immediately there.
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_033911.md`

## 2026-04-09 03:41 JST - 0x10043B48 first sub-call returns success

- `teraterm_2026-04-09_034120.log` faulted at `ELR=...10043B70`.
- This stop is immediately after `bl #0x10059360` inside `0x10043B48`.
- Registers there show:
  - `X0 = 0`
  - `X19 = 0x400010A0`
  - `X20 = 0`
  - `X22 = 0x400010A0`
- Therefore the first sub-call in `0x10043B48` is not the source of the later `0xC000000D`.
- The next meaningful gate is the return from `bl #0x101B2058` at `0x10043BA4`.
- Next staged stop moves to `0x10043BA8`.

## 2026-04-09 03:44 JST - 0x101B2058 also returns success

- `teraterm_2026-04-09_034434.log` faulted at `ELR=...10043BA8`.
- This stop is immediately after `bl #0x101B2058` inside `0x10043B48`.
- Registers there show:
  - `X0 = 0`
  - `X19 = 0x400010A0`
  - `X20 = 0`
  - `X22 = 0x400010A0`
- Therefore `0x101B2058` is not the source of the later `0xC000000D` either.
- The next live gate in `0x10043B48` is the return from `0x101B1C78`, checked at `0x10043BD4`.
- Next staged stop moves to `0x10043BD4`.

## 2026-04-09 07:30 JST - 0x101B1C78 also returns success

- `teraterm_2026-04-09_073014.log` faulted at `ELR=...10043BD4`.
- This stop is immediately after `bl #0x101B1C78` inside `0x10043B48`.
- Registers there show:
  - `X0 = 0`
  - `X19 = 0x400010A0`
  - `X20 = 0`
  - `X22 = 0x400010A0`
- Therefore `0x101B1C78` is not the source of the later negative status either.
- The next live gate in `0x10043B48` is the return from `0x101B8160`, checked at `0x10043BEC`.
- Next staged stop moves to `0x10043BEC`.


## 2026-04-09 07:39 JST - 0x101B8160 is the first 000d source inside 0x10043B48

- `teraterm_2026-04-09_073934.log` hit `ELR=...10043BEC`.
- This stop is the post-return instruction after `bl #0x101B8160` inside `0x10043B48`.
- Registers there show:
  - `X0 = 0xC000000D`
  - `X19 = 0xFFFFFFFF`
  - `X20 = 0xC000000D`
  - `X22 = 0x400010A0`
- Therefore `0x101B8160` is the first sub-call in `0x10043B48` that actually returns the negative status later propagated upward.
- The immediate next probe moves one level deeper into `0x101B8160`, stopping at `0x101B8254`, which is the post-return instruction after the first property query helper `bl #0x101B0C90` with literal property id `0x17000077`.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8254_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_074327.md`


## 2026-04-09 14:27 JST - 0x101B8254 stop hit, but exception dump recursed

- `teraterm_2026-04-09_142757.log` hit `ELR=...101B8254`.
- That confirms control reached the post-return instruction after `bl #0x101B0C90` inside `0x101B8160`.
- However, this trap produced a recursive exception during CPU-state dumping, so the return registers were not captured.
- Because the stop itself was reached, the next probe simply moves one instruction later to `0x101B8258`, preserving the same returned `w0` value while avoiding the broken dump site.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8258_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_143029.md`


## 2026-04-09 14:33 JST - 0x101B8258 still recurses, split the branch instead

- `teraterm_2026-04-09_143342.log` also hit inside the same top-of-function area, now at `ELR=...101B8258`.
- That is the `tbnz w0, #0x1f, #0x101B8284` immediately after the first `0x17000077` property query helper.
- The CPU-state dump still recursed, so the returned `w0` value could not be read directly.
- Because both `0x101B8254` and `0x101B8258` are unstable dump points, the next probe no longer tries to read registers there.
- Instead it splits the branch structurally:
  - `0x101B825C -> UDF`
  - `0x101B8284 -> UDF`
- Interpretation of the next run:
  - `ELR=...101B825C` means the `tbnz` was not taken, so the first helper did not return a negative status.
  - `ELR=...101B8284` means the `tbnz` was taken, so the first helper already returned a negative status.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B825C_or_101B8284_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_150440.md`


## 2026-04-09 15:07 JST - first 0x17000077 helper already returns negative

- `teraterm_2026-04-09_150703.log` hit `ELR=...101B8284`.
- This was the split probe around `tbnz w0, #0x1f, #0x101B8284` immediately after the first helper call in `0x101B8160`.
- Because the trap landed at `0x101B8284` and not `0x101B825C`, the branch was taken.
- Therefore the first helper `bl #0x101B0C90` for property id `0x17000077` already returns a negative status.
- The next live fork is the `tbz w8, #0x11, #0x101B82B4` branch starting at `0x101B8288`.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B828C_or_101B82B4_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_150949.md`


## 2026-04-09 15:12 JST - bit11 path is skipped after the first negative property query

- `teraterm_2026-04-09_151222.log` hit `ELR=...101B82B4`.
- This was the split probe for the `tbz w8, #0x11, #0x101B82B4` branch after the first negative `0x17000077` result.
- Therefore the `bit11` path is **not** taking the `0x101B828C` branch into the `0x15000075` helper pair.
- The natural flow drops directly into the timestamp/mismatch block starting at `0x101B82B4`.
- The next staged stop is `0x101B82B8`, immediately after `bl #0x101AE7F8`.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B82B8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_151334.md`


## 2026-04-09 15:15 JST - mismatch/timestamp path entered, compare split staged

- `teraterm_2026-04-09_151537.log` hit `ELR=...101B82B8`.
- This confirms execution entered the mismatch/timestamp path after `bl #0x101AE7F8`.
- Direct register capture at `0x101B82B8` still recursed, so the next probe again uses a structural split instead of trying to read `x0` directly.
- New split probe:
  - `0x101B82C8 -> UDF`
  - `0x101B82F8 -> UDF`
- Interpretation:
  - `0x101B82C8` hit: the `cmp x20, x0` mismatch path is taken.
  - `0x101B82F8` hit: the two helper results compare equal and flow skips the mismatch handling.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B82C8_or_101B82F8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_151702.md`


## 2026-04-09 15:18 JST - compare matched, mismatch handling skipped

- `teraterm_2026-04-09_151845.log` hit `ELR=...101B82F8`.
- This was the split probe after the `0x101AE7F8 / 0x101AE768` compare sequence.
- Therefore the compare matched and flow skipped the mismatch-handling block at `0x101B82C8`.
- Natural flow now reaches the later post-compare branch at `0x101B8300`, which decides between:
  - `0x101B8304` normal later block
  - `0x101B8BCC` long side path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8304_or_101B8BCC_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_152044.md`


## 2026-04-09 15:23 JST - long side path not taken, normal later block selected

- `teraterm_2026-04-09_152327.log` hit `ELR=...101B8304`.
- This was the split probe after the compare-equal path at `0x101B82F8`.
- Therefore the later `bit11` branch at `0x101B8300` does **not** take the long side path `0x101B8BCC`.
- Flow falls into the normal later block beginning at `0x101B8304`.
- The next live gate is the first property pair in that block:
  - `0x16000041`
  - `0x16000040`
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B834C_or_101B8380_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_152443.md`


## 2026-04-09 15:31 JST - first later property gate clears, second gate split staged

- `teraterm_2026-04-09_153146.log` hit `ELR=...101B834C`.
- This was the split probe for the first later property gate inside the normal block that starts at `0x101B8304`.
- Therefore the first local gate based on `0x16000041` cleared and flow advanced to the second property query `0x16000040`.
- The next staged split is:
  - `0x101B836C -> UDF`
  - `0x101B8380 -> UDF`
- Interpretation:
  - `0x101B836C` hit: second property gate also clears and flow reaches the flag-update block.
  - `0x101B8380` hit: second property gate raises the same local flag/error side.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B836C_or_101B8380_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_153319.md`


## 2026-04-09 15:39 JST - second later property gate also clears

- `teraterm_2026-04-09_153712.log` hit `ELR=...101B836C`.
- This proves the second later property gate based on `0x16000040` also clears and does **not** raise the local flag/error side at `0x101B8380`.
- Active flow now reaches the flag-update block at `0x101B836C..0x101B8390` and then the next live query:
  - `0x11000001` via `bl #0x10059D90`
- The next staged stop is:
  - `0x101B83A4 -> UDF`
- Interpretation:
  - `0x101B83A4` hit: the `0x11000001` query returned and its status can be inspected directly
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B83A4_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_153932.md`


## 2026-04-09 15:43 JST - post-0x11000001 return site reached, branch split staged

- `teraterm_2026-04-09_154154.log` hit `ELR=...101B83A4`.
- This confirms the `0x11000001` query (`bl #0x10059D90`) returned and flow reached the post-call handling block.
- Direct register capture was again not reliable enough to read `w0`, so the next probe switches back to a structural split.
- Next staged split:
  - `0x101B83B8 -> UDF`
  - `0x101B8B9C -> UDF`
- Interpretation:
  - `0x101B83B8` hit: the `0x11000001` result does **not** send flow to the negative-status error leg at `0x101B8B9C`
  - `0x101B8B9C` hit: the `0x11000001` result still sends flow into the error tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B83B8_or_101B8B9C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_154344.md`


## 2026-04-09 15:47 JST - 0x11000001 does not take the negative-status tail

- `teraterm_2026-04-09_154644.log` hit `ELR=...101B83B8`.
- This proves the `0x11000001` result did **not** send flow to the negative-status tail at `0x101B8B9C`.
- Active flow remains in the normal later block and now reaches the flag test:
  - `tst w9, #0x2004`
- The next staged split is:
  - `0x101B83C8 -> UDF`
  - `0x101B83E8 -> UDF`
- Interpretation:
  - `0x101B83C8` hit: flags require the extra `0x21000001` query block
  - `0x101B83E8` hit: flags skip that block and flow continues directly to the later checks
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B83C8_or_101B83E8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_154758.md`


## 2026-04-09 15:49 JST - extra 0x21000001 query block is skipped

- `teraterm_2026-04-09_154954.log` hit `ELR=...101B83E8`.
- This proves the `tst w9, #0x2004 ; b.eq #0x101B83E8` branch took the `eq` path.
- So the extra `0x21000001` query block at `0x101B83C8..0x101B83E4` is skipped entirely.
- Active flow now reaches the next flag test:
  - `tbz w8, #8, #0x101B8424`
- Next staged split:
  - `0x101B83F0 -> UDF`
  - `0x101B8424 -> UDF`
- Interpretation:
  - `0x101B83F0` hit: bit8 is set and flow enters the `0x21000005` query path
  - `0x101B8424` hit: bit8 is clear and the `0x21000005` path is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B83F0_or_101B8424_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_155108.md`


## 2026-04-09 15:55 JST - bit8 path also skips the 0x21000005 query block

- `teraterm_2026-04-09_155530.log` hit `ELR=...101B8424`.
- This proves the `tbz w8, #8, #0x101B8424` branch took the `bit8-clear` path.
- So the `0x21000005` query block at `0x101B83F0..0x101B8420` is skipped entirely.
- Active flow now reaches the `x21`-dependent gate:
  - `cbz x21, #0x101B8450`
- Next prepared split:
  - `0x101B8428 -> UDF`
  - `0x101B8450 -> UDF`
- Interpretation:
  - `0x101B8428` hit: `x21` is nonzero and flow enters the `0x10064470` helper path
  - `0x101B8450` hit: `x21` is zero and that helper path is skipped
- Prepared EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8428_or_101B8450_udf.EFI`


## 2026-04-09 16:00 JST - x21 is zero, helper path is skipped

- `teraterm_2026-04-09_160052.log` hit `ELR=...101B8450`.
- This proves the `cbz x21, #0x101B8450` branch was taken.
- So `x21` is zero and the helper path at `0x101B8428..0x101B844C` is skipped entirely.
- Active flow now reaches the global/cached pointer gate:
  - `ldr x0, [x22, #8] ; cbnz x0, #0x101B8474`
- Next staged split:
  - `0x101B8460 -> UDF`
  - `0x101B8474 -> UDF`
- Interpretation:
  - `0x101B8460` hit: cached pointer is null and flow enters the `0x10063AC0` allocator/initializer path
  - `0x101B8474` hit: cached pointer is already nonzero and flow skips directly to the `0x15000042` block
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8460_or_101B8474_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_163416.md`


## 2026-04-09 16:38 JST - cached pointer is null, allocator path is live

- `teraterm_2026-04-09_163822.log` hit `ELR=...101B8460`.
- This proves the cached/global pointer test `ldr x0, [x22, #8] ; cbnz x0, #0x101B8474` fell through the null case.
- So the allocator/initializer path at `0x101B8460..0x101B8470` is live.
- The next question is whether that allocator path leaves `x22[8]` still null or populates it before reaching the common path.
- Next staged split:
  - `0x101B8474 -> UDF`
  - `0x101B8B98 -> UDF`
- Interpretation:
  - `0x101B8474` hit: allocator path produced a nonnull pointer and flow reaches the `0x15000042` block
  - `0x101B8B98` hit: pointer is still null after the allocator path and flow falls into the null-tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8474_or_101B8B98_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_164037.md`


## 2026-04-09 16:45 JST - allocator path populated the cached pointer

- `teraterm_2026-04-09_164506.log` hit `ELR=...101B8474`.
- This proves the allocator/initializer path left `[x22 + 8]` nonnull and flow reached the common `0x15000042` block.
- The null-tail at `0x101B8B98` was not taken.
- Active flow now reaches:
  - `ldr x0, [x19, #0x18]`
  - `mov w1, #0x15000042`
  - `bl #0x101B0B60`
- Next staged split:
  - `0x101B84B0 -> UDF`
  - `0x101B84D4 -> UDF`
- Interpretation:
  - `0x101B84B0` hit: the `0x15000042` block takes its update/reporting leg
  - `0x101B84D4` hit: the `0x15000042` block converges directly to the common post-block
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B84B0_or_101B84D4_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_165352.md`


## 2026-04-09 16:57 JST - 0x15000042 block took the update/reporting leg

- `teraterm_2026-04-09_165712.log` hit `ELR=...101B84B0`.
- This proves the `0x15000042` block did not converge directly to `0x101B84D4`.
- Active flow entered the update/reporting leg:
  - `bl #0x101B1B70`
  - `mov w20, w0`
  - `tbnz w0, #0x1f, #0x101B8B9C`
- Next staged split:
  - `0x101B84D4 -> UDF`
  - `0x101B8B9C -> UDF`
- Interpretation:
  - `0x101B84D4` hit: the update/reporting call returned nonnegative and flow converged to the common post-block
  - `0x101B8B9C` hit: the update/reporting call returned negative and flow fell into the error tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B84D4_or_101B8B9C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_170147.md`


## 2026-04-09 18:07 JST - 0x15000042 update/reporting call returned nonnegative

- `teraterm_2026-04-09_180755.log` hit `ELR=...101B84D4`.
- This proves the `0x101B1B70` update/reporting call did not return a negative status.
- Active flow now converges to the common post-block:
  - `bl #0x1020B300`
  - `mov w20, w0`
  - `tbnz w20, #0x1f, #0x101B8B9C`
  - `ldrb w8, [sp, #0x48]`
  - `cbz w8, #0x101B8B98`
- Next staged split:
  - `0x101B84EC -> UDF`
  - `0x101B8B98 -> UDF`
  - `0x101B8B9C -> UDF`
- Interpretation:
  - `0x101B84EC` hit: `0x1020B300` returned nonnegative and the byte flag is nonzero
  - `0x101B8B98` hit: status stayed nonnegative but the byte flag is zero
  - `0x101B8B9C` hit: `0x1020B300` returned negative and flow fell into the error tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B84EC_or_101B8B98_or_101B8B9C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_180919.md`


## 2026-04-09 18:29 JST - common post-block succeeded but byte flag was zero

- `teraterm_2026-04-09_182944.log` hit `ELR=...101B8B98`.
- This proves `0x1020B300` did not return a negative status, but the byte flag at `[sp + 0x48]` was zero.
- Active flow now enters the null-tail cleanup and then falls through to the side path at `0x101B8BCC`.
- The next live helper is:
  - `bl #0x101B11E8` with property id `0x11000001`
- Next staged stop:
  - `0x101B8BE0 -> UDF`
- Interpretation:
  - `0x101B8BE0` hit: the `0x101B11E8` side-path query returned and we can inspect its status/handle next
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8BE0_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_183250.md`


## 2026-04-09 18:42 JST - side-path 0x11000001 query returned

- `teraterm_2026-04-09_184242.log` hit `ELR=...101B8BE0`.
- This proves the side-path query helper `0x101B11E8` returned and flow reached:
  - `ldr x21, [sp, #0x130]`
  - `mov w20, w0`
  - `tbnz w0, #0x1f, #0x101B99C8`
- Register dumping recursed at this site, so the next readout uses branch outcomes rather than raw `w0`.
- Next staged split:
  - `0x101B8BF4 -> UDF`
  - `0x101B99C8 -> UDF`
- Interpretation:
  - `0x101B8BF4` hit: the side-path `0x11000001` query returned nonnegative and flow continues into the `0x12000002` block
  - `0x101B99C8` hit: the side-path `0x11000001` query returned negative and flow jumps to the shared error/report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8BF4_or_101B99C8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_184421.md`


## 2026-04-09 19:02 JST - side-path 0x11000001 query returned nonnegative

- `teraterm_2026-04-09_190249.log` hit `ELR=...101B8BF4`.
- This proves the side-path `0x11000001` query did not return a negative status.
- Active flow now continues into the next side-path block:
  - `ldr x0, [x19, #0x18]`
  - `add x2, sp, #0xa0`
  - `ldr w1, =0x12000002`
  - `bl #0x101B0DE0`
  - `tbnz w0, #0x1f, #0x101B99C0`
- Next prepared split:
  - `0x101B8C10 -> UDF`
  - `0x101B99C0 -> UDF`
- Interpretation:
  - `0x101B8C10` hit: the side-path `0x12000002` block returned nonnegative and flow continues deeper
  - `0x101B99C0` hit: the side-path `0x12000002` block returned negative and flow jumps to the nearby cleanup/report tail
- Prepared EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8C10_or_101B99C0_udf.EFI`
- Note:
  - staging is pending because the removable media is currently not mounted as `F:/`


## 2026-04-09 20:16 JST - side-path 0x12000002 block returned nonnegative

- `teraterm_2026-04-09_201606.log` hit `ELR=...101B8C10`.
- This proves the side-path `0x12000002` block did not return a negative status.
- Active flow now enters the next helper path:
  - `add x2, sp, #0x90`
  - `mov w1, #1`
  - `mov x0, x21`
  - `bl #0x10064470`
  - `tbnz w0, #0x1f, #0x101B99A8`
- Next staged split:
  - `0x101B8C3C -> UDF`
  - `0x101B99A8 -> UDF`
- Interpretation:
  - `0x101B8C3C` hit: the `0x10064470` helper returned nonnegative and flow continues deeper
  - `0x101B99A8` hit: the `0x10064470` helper returned negative and flow jumps to the nearby cleanup/report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8C3C_or_101B99A8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_202045.md`


## 2026-04-09 20:26 JST - side-path helper 0x10064470 returned nonnegative

- `teraterm_2026-04-09_202611.log` hit `ELR=...101B8C3C`.
- This proves the side-path helper `0x10064470` did not return a negative status.
- Active flow now reaches the next byte-producing helper path:
  - `bl #0x101C72C8`
  - `uxtb w8, w0`
  - `cbnz w8, #0x101B8C64`
- Next staged split:
  - `0x101B8C5C -> UDF`
  - `0x101B8C64 -> UDF`
- Interpretation:
  - `0x101B8C5C` hit: `0x101C72C8` returned zero-like and flow takes the local `0xC0000017` path
  - `0x101B8C64` hit: `0x101C72C8` returned nonzero and flow continues into the deeper helper chain
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8C5C_or_101B8C64_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_203526.md`


## 2026-04-09 21:51 JST - 0x101C72C8 returned nonzero, deeper helper chain is live

- `teraterm_2026-04-09_215103.log` hit `ELR=...101B8C64`.
- This proves `0x101C72C8` returned nonzero and flow entered the deeper helper chain instead of the local `0xC0000017` path.
- Active flow now reaches:
  - `bl #0x102634D0`
  - `mov w20, w0`
  - `tbnz w20, #0x1f, #0x101B8C94`
  - otherwise `bl #0x101C5AF8`
- Next staged split:
  - `0x101B8C90 -> UDF`
  - `0x101B8C94 -> UDF`
- Interpretation:
  - `0x101B8C90` hit: `0x102634D0` returned nonnegative and flow continues into `0x101C5AF8`
  - `0x101B8C94` hit: `0x102634D0` returned negative and flow skips directly to the common status merge
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8C90_or_101B8C94_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_220733.md`


## 2026-04-09 22:09 JST - 0x102634D0 returned nonnegative

- `teraterm_2026-04-09_220924.log` hit `ELR=...101B8C90`.
- This proves `0x102634D0` did not return a negative status.
- Active flow now reaches:
  - `bl #0x101C5AF8`
  - `mov w20, w0`
  - `tbnz w0, #0x1f, #0x101B99A8`
- Next staged split:
  - `0x101B8CA0 -> UDF`
  - `0x101B99A8 -> UDF`
- Interpretation:
  - `0x101B8CA0` hit: `0x101C5AF8` returned nonnegative and flow continues into the `0x16000048` block
  - `0x101B99A8` hit: `0x101C5AF8` returned negative and flow falls into the side-path cleanup/report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8CA0_or_101B99A8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_222530.md`

## 2026-04-09 22:29 JST - 0x101C5AF8 returned nonnegative and flow entered the 0x16000048 block

- `teraterm_2026-04-09_222923.log` hit `ELR=...101B8CA0`.
- This proves `0x101C5AF8` did not return a negative status.
- Active flow now reaches the `0x16000048` property block and its post-helper gate:
  - `bl #0x101b0a20`
  - `csel w8, wzr, w8, lt`
  - `cbnz w8, #0x101b8cd8`
  - `bl #0x101b37c0`
  - `tbnz w0, #0x1f, #0x101b9978`
- Next staged split:
  - `0x101B8D1C -> UDF`
  - `0x101B9978 -> UDF`
- Interpretation:
  - `0x101B8D1C` hit: `0x101B37C0` returned nonnegative and flow continues deeper
  - `0x101B9978` hit: `0x101B37C0` returned negative and flow falls into the side-path report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8D1C_or_101B9978_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_225854.md`

## 2026-04-09 23:00 JST - 0x101B37C0 returned nonnegative and flow reached 0x101BCAB0

- `teraterm_2026-04-09_230052.log` hit `ELR=...101B8D1C`.
- This proves `0x101B37C0` did not return a negative status.
- Active flow now enters the next side-path call chain:
  - `bl #0x101bcab0`
  - `str w0, [sp, #0x40]`
  - `tbnz w0, #0x1f, #0x101b9978`
- Next staged split:
  - `0x101B8D70 -> UDF`
  - `0x101B9978 -> UDF`
- Interpretation:
  - `0x101B8D70` hit: `0x101BCAB0` returned nonnegative and flow continues into the post-call loop / report block
  - `0x101B9978` hit: `0x101BCAB0` returned negative and flow falls into the side-path report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B8D70_or_101B9978_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_230210.md`

## 2026-04-09 23:04 JST - 0x101BCAB0 returned negative and flow fell into the side-path report tail

- `teraterm_2026-04-09_230404.log` hit `ELR=...101B9978`.
- This proves `0x101BCAB0` returned a negative status and the branch at `0x101B8D6C` took the side-path report tail.
- Active flow is now inside the local report/cleanup tail:
  - `bl #0x101b37c0`
  - `ldr w20, [sp, #0x40]`
  - `ldr w0, [sp, #0x70]`
  - `cmn w0, #1`
  - `b.eq #0x101b99c8`
  - otherwise `bl #0x10064528`
- Next staged split:
  - `0x101B99B4 -> UDF`
  - `0x101B99C8 -> UDF`
- Interpretation:
  - `0x101B99B4` hit: the tail takes the cleanup-helper path through `0x10064528`
  - `0x101B99C8` hit: the tail skips that helper and drops directly into cleanup/report teardown
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B99B4_or_101B99C8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_230539.md`

## 2026-04-09 23:08 JST - the side-path report tail took the cleanup-helper path

- `teraterm_2026-04-09_230833.log` hit `ELR=...101B99B4`.
- This proves the report tail did not skip directly to teardown. It took the cleanup-helper path through `0x10064528`.
- The immediate next question is whether that helper returns cleanly to the local tail.
- Next staged stop:
  - `0x101B99B8 -> UDF`
- Interpretation:
  - `0x101B99B8` hit: `0x10064528` returned and flow resumed in the local report tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B99B8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_231218.md`

## 2026-04-09 23:19 JST - 0x10064528 returned and flow resumed in the local report tail

- `teraterm_2026-04-09_231933.log` hit `ELR=...101B99B8`.
- This proves the cleanup helper `0x10064528` returned and flow resumed in the local report tail.
- The next live choice is whether the first optional cleanup object at `[sp + 0x228]` is present.
- Next staged split:
  - `0x101B99D0 -> UDF`
  - `0x101B99D8 -> UDF`
- Interpretation:
  - `0x101B99D0` hit: `[sp + 0x228]` is nonzero and the first optional cleanup call to `0x101DE718` is taken
  - `0x101B99D8` hit: `[sp + 0x228]` is zero and that optional cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B99D0_or_101B99D8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_232103.md`

## 2026-04-09 23:23 JST - the first optional cleanup object is present

- `teraterm_2026-04-09_232354.log` hit `ELR=...101B99D0`.
- This proves `[sp + 0x228]` was nonzero and the first optional cleanup call to `0x101DE718` was taken.
- The next live choice is whether the second optional cleanup object at `[sp + 0xC8]` is present.
- Next staged split:
  - `0x101B99E0 -> UDF`
  - `0x101B99E8 -> UDF`
- Interpretation:
  - `0x101B99E0` hit: `[sp + 0xC8]` is nonzero and the second optional cleanup call to `0x101DE718` is taken
  - `0x101B99E8` hit: `[sp + 0xC8]` is zero and that cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B99E0_or_101B99E8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_232828.md`

## 2026-04-09 23:31 JST - the second optional cleanup object is present

- `teraterm_2026-04-09_233106.log` hit `ELR=...101B99E0`.
- This proves `[sp + 0xC8]` was nonzero and the second optional cleanup call to `0x101DE718` was taken.
- The next live choice is whether the third optional cleanup object at `[sp + 0x98]` is present.
- Next staged split:
  - `0x101B99F0 -> UDF`
  - `0x101B99F8 -> UDF`
- Interpretation:
  - `0x101B99F0` hit: `[sp + 0x98]` is nonzero and the third optional cleanup call to `0x101DE718` is taken
  - `0x101B99F8` hit: `[sp + 0x98]` is zero and that cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B99F0_or_101B99F8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_233513.md`

## 2026-04-09 23:42 JST - the third optional cleanup object is absent

- `teraterm_2026-04-09_234207.log` hit `ELR=...101B99F8`.
- This proves `[sp + 0x98]` was zero and the third optional cleanup call was skipped.
- The next live choice is whether the fourth optional cleanup object at `[sp + 0xB0]` is present.
- Next staged split:
  - `0x101B9A00 -> UDF`
  - `0x101B9A08 -> UDF`
- Interpretation:
  - `0x101B9A00` hit: `[sp + 0xB0]` is nonzero and the fourth optional cleanup call to `0x101DE718` is taken
  - `0x101B9A08` hit: `[sp + 0xB0]` is zero and that cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A00_or_101B9A08_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_234946.md`

## 2026-04-09 23:58 JST - the fourth optional cleanup object is absent

- `teraterm_2026-04-09_235851.log` hit `ELR=...101B9A08`.
- This proves `[sp + 0xB0]` was zero and the fourth optional cleanup call was skipped.
- The next live choice is the sign of `w20` at the `tbz w20, #0x1f, #0x101B9A74` branch.
- Next staged split:
  - `0x101B9A0C -> UDF`
  - `0x101B9A74 -> UDF`
- Interpretation:
  - `0x101B9A0C` hit: `w20` is still negative and flow enters the negative-status cleanup block
  - `0x101B9A74` hit: `w20` is nonnegative and flow skips into the success-side accounting block
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A0C_or_101B9A74_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_000433.md`

## 2026-04-10 00:26 JST - w20 is still negative and flow entered the negative-status cleanup block

- `teraterm_2026-04-10_002604.log` hit `ELR=...101B9A0C`.
- This proves `w20` still has its sign bit set and flow entered the negative-status cleanup block instead of the success-side accounting path.
- The next live choice is whether the first object in that block at `[sp + 0xA8]` is present.
- Next staged split:
  - `0x101B9A14 -> UDF`
  - `0x101B9A24 -> UDF`
- Interpretation:
  - `0x101B9A14` hit: `[sp + 0xA8]` is nonzero and the `0x101BD310` cleanup path is taken
  - `0x101B9A24` hit: `[sp + 0xA8]` is zero and that path is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A14_or_101B9A24_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_002756.md`

## 2026-04-10 00:59 JST - the first object in the negative-status cleanup block is absent

- `teraterm_2026-04-10_005915.log` hit `ELR=...101B9A24`.
- This proves `[sp + 0xA8]` was zero and the `0x101BD310` cleanup path was skipped.
- The next live choice is whether the next optional cleanup object at `[sp + 0xB8]` is present.
- Next staged split:
  - `0x101B9A2C -> UDF`
  - `0x101B9A34 -> UDF`
- Interpretation:
  - `0x101B9A2C` hit: `[sp + 0xB8]` is nonzero and the next cleanup call to `0x101DE718` is taken
  - `0x101B9A34` hit: `[sp + 0xB8]` is zero and that cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A2C_or_101B9A34_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_010104.md`

## 2026-04-10 01:03 JST - the next optional cleanup object at [sp + 0xB8] is absent

- `teraterm_2026-04-10_010301.log` hit `ELR=...101B9A34`.
- This proves `[sp + 0xB8]` was zero and that optional cleanup call was skipped.
- The next live choice is whether the next optional cleanup object at `[sp + 0x120]` is present.
- Next staged split:
  - `0x101B9A3C -> UDF`
  - `0x101B9A44 -> UDF`
- Interpretation:
  - `0x101B9A3C` hit: `[sp + 0x120]` is nonzero and the next cleanup call to `0x101DE718` is taken
  - `0x101B9A44` hit: `[sp + 0x120]` is zero and that cleanup is skipped
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A3C_or_101B9A44_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_015201.md`

## 2026-04-10 01:54 JST - the next optional cleanup object at [sp + 0x120] is absent

- `teraterm_2026-04-10_015400.log` hit `ELR=...101B9A44`.
- This proves `[sp + 0x120]` was zero and that optional cleanup call was skipped.
- Flow now reaches the global state block around `0x10303000 + {0xCC8,0xCD0}`.
- Next staged split:
  - `0x101B9A5C -> UDF`
  - `0x101B9A84 -> UDF`
- Interpretation:
  - `0x101B9A5C` hit: the global cleanup object at `0x10303000+0xCD0` is present and the `0x101DE718` cleanup call is taken
  - `0x101B9A84` hit: that global cleanup path is skipped and flow falls through to the tail epilogue block
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9A5C_or_101B9A84_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_015841.md`

## 2026-04-10 02:48 JST - the global cleanup object was skipped and flow reached the tail epilogue gate

- `teraterm_2026-04-10_024844.log` hit `ELR=...101B9A84`.
- This proves the global cleanup object at `0x10303000+0xCD0` was not taken and flow reached the final `0x102ef000` heartbeat gate.
- The next live choice is whether that gate takes the `0x101E47A8` call or falls straight to the epilogue.
- Next staged split:
  - `0x101B9AB8 -> UDF`
  - `0x101B9AC4 -> UDF`
- Interpretation:
  - `0x101B9AB8` hit: the heartbeat gate is live and the `0x101E47A8` call is taken
  - `0x101B9AC4` hit: the heartbeat gate falls straight through to the function epilogue
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B9AB8_or_101B9AC4_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_025159.md`

## 2026-04-10 07:09 JST - the final heartbeat gate fell straight through to the epilogue

- 	eraterm_2026-04-10_070909.log hit ELR=...101B9AC4.
- This proves the  x102EF000 heartbeat gate did not take the  x101E47A8 call and the function fell straight through to its epilogue.
- The next live question is no longer inside  x101B8160; it is whether the caller at  x10043BEC still sees a negative return and branches into its local cleanup/report tail.
- Next staged split:
  -  x10043BF0 -> UDF
  -  x10043C00 -> UDF
- Interpretation:
  -  x10043BF0 hit:  x101B8160 returned nonnegative and the caller continued into  x101B9C98
  -  x10043C00 hit:  x101B8160 still returned negative and the caller branched into its local cleanup/report tail
- New staged EFI:
  - D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_10043BF0_or_10043C00_udf.EFI
- Snapshot:
  - D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_071802.md
"@
 = @"

## 2026-04-10 07:09 JST - final heartbeat gate skipped, next split returns to the caller

- 	eraterm_2026-04-10_070909.log hit ELR=...101B9AC4.
- This proves the final heartbeat gate in  x101B8160 fell straight through to the epilogue and did not call  x101E47A8.
- Next staged split:
  -  x10043BF0 -> UDF
  -  x10043C00 -> UDF
- Meaning:
  -  x10043BF0 hit:  x101B8160 returned nonnegative and flow continues into  x101B9C98
  -  x10043C00 hit:  x101B8160 returned negative and flow branches into the caller-side cleanup/report tail

## 2026-04-10 07:19 JST -  x101B8160 still returned negative to its caller

- 	eraterm_2026-04-10_071959.log hit ELR=...10043C00.
- This proves  x101B8160 still returned a negative status and the caller  x10043B48 branched into its local cleanup/report tail instead of continuing into  x101B9C98.
- Register state at the stop confirms the propagated status is still  xC000000D.
- The next live question is now inside  x101BCAB0, the side-path helper that previously returned negative: whether it fails immediately on its local input/null checks or after the first helper call  x101C29F0.
- Next staged split:
  -  x101BCB74 -> UDF
  -  x101BCBD4 -> UDF
- Interpretation:
  -  x101BCB74 hit: local validation passed and flow reached the return from  x101C29F0
  -  x101BCBD4 hit: local validation failed and flow took the hardcoded  xC000000D path directly
- New staged EFI:
  - D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101BCB74_or_101BCBD4_udf.EFI
- Snapshot:
  - D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_072433.md
"@
 = @"

## 2026-04-10 07:19 JST - caller-side split confirmed  x101B8160 still returns negative

- 	eraterm_2026-04-10_071959.log hit ELR=...10043C00.
- This proves  x101B8160 still returns negative and caller  x10043B48 enters its local cleanup/report tail.
- Next staged split moves down into  x101BCAB0:
  -  x101BCB74 -> UDF
  -  x101BCBD4 -> UDF
- Meaning:
  -  x101BCB74 hit: local validation passed and flow reached the return from  x101C29F0
  -  x101BCBD4 hit: local validation failed and flow took the direct hardcoded  xC000000D path

## 2026-04-10 07:29 JST - local validation passed and `0x101C29F0` itself returned `0xC000000D`

- `teraterm_2026-04-10_072907.log` hit `ELR=...101BCB74`.
- This proves `0x101BCAB0` did not take the direct hardcoded `0xC000000D` path at `0x101BCBD4`; local validation passed and flow reached the return from the first helper call `0x101C29F0`.
- Register state at the stop shows `X0 = 0xC000000D`, so `0x101C29F0` itself is already returning the negative status.
- The next live question is whether `0x101C29F0` fails immediately in its first helper `0x10244878` or only after falling back into `0x100CC7E0`.
- Next staged split:
  - `0x101C2A28 -> UDF`
  - `0x101C2A4C -> UDF`
- Interpretation:
  - `0x101C2A28` hit: the first helper `0x10244878` returned nonnegative and flow is still on its primary path
  - `0x101C2A4C` hit: the first helper path failed or size-check rejected it, and flow fell into the fallback path `0x100CC7E0`
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101C2A28_or_101C2A4C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_073026.md`

## 2026-04-10 07:32 JST - `0x101C29F0` fell into its fallback path `0x100CC7E0`

- `teraterm_2026-04-10_073235.log` hit `ELR=...101C2A4C`.
- This proves the primary path in `0x101C29F0` did not complete successfully; flow fell through to the fallback path that calls `0x100CC7E0`.
- The next live question is whether fallback `0x100CC7E0` gets its special `0x104` result from `0x100CE028` and enters the deeper parse block, or immediately falls back to its exit/report logic.
- Next staged split:
  - `0x100CC870 -> UDF`
  - `0x100CCCF4 -> UDF`
- Interpretation:
  - `0x100CC870` hit: `0x100CE028` returned `0x104` and fallback parsing entered its deeper path
  - `0x100CCCF4` hit: `0x100CE028` did not return `0x104` and flow fell straight into the fallback exit/report path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CC870_or_100CCCF4_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_073348.md`

## 2026-04-10 07:36 JST - fallback `0x100CC7E0` reached its deeper block but still kept `w22 = 0xC000000D`

- `teraterm_2026-04-10_073626.log` hit `ELR=...100CCCF4`.
- This proves fallback `0x100CC7E0` did not exit early at `0x100CCCF4`; it reached the deeper block and still had `w22 = 0xC000000D` at that point.
- The next live question is whether the immediate post-check on `w25` bit7 skips the report/update block or enters it.
- Next staged split:
  - `0x100CCD00 -> UDF`
  - `0x100CCD30 -> UDF`
- Interpretation:
  - `0x100CCD00` hit: `w22` is negative but `w25` bit7 is clear, so flow enters the report/update block starting at `0x100CCCFC`
  - `0x100CCD30` hit: flow skips that block and falls directly to the tail epilogue path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CCD00_or_100CCD30_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_073735.md`

## 2026-04-10 20:22 JST - `w25` bit7 was clear and fallback flow entered the report/update block

- `teraterm_2026-04-10_202200.log` hit `ELR=...100CCD00`.
- This proves the post-check on `w25` did not skip the report/update block; flow entered the block starting at `0x100CCCFC`.
- At the stop, `w22` was still `0xC000000D`, so the negative status is still live while entering that block.
- The next live question is whether the internal flag test at `0x100CCD1C` takes the call to `0x100CC6B0` or skips directly to the tail at `0x100CCD30`.
- Next staged split:
  - `0x100CCD20 -> UDF`
  - `0x100CCD30 -> UDF`
- Interpretation:
  - `0x100CCD20` hit: the `tbz w8,#3` test did not branch and the call to `0x100CC6B0` is live
  - `0x100CCD30` hit: that test branched and the call is skipped, falling directly to the tail epilogue block
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CCD20_or_100CCD30_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_202338.md`

## 2026-04-10 20:29 JST - the fallback report/update block skipped `0x100CC6B0` and fell to its tail

- `teraterm_2026-04-10_202950.log` hit `ELR=...100CCD30`.
- This proves the internal bit3 gate in fallback `0x100CC7E0` branched and skipped the `0x100CC6B0` call.
- That block is now effectively exhausted; it just falls into the tail and returns the already-live negative status.
- The next useful move is upstream: back into `0x100CE028`, which is the source of the hardcoded `0xC000000D` on validation failure.
- Next staged split:
  - `0x100CE0E4 -> UDF`
  - `0x100CE19C -> UDF`
- Interpretation:
  - `0x100CE0E4` hit: the early argument/path validation passed and flow reached the `0x10064B08` call
  - `0x100CE19C` hit: one of the early validation gates failed and flow took the hardcoded `0xC000000D` path directly
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE0E4_or_100CE19C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_203249.md`

## 2026-04-10 20:37 JST - `0x100CE028` early validation passed, next split moves to the `0x10064B08` return

- `teraterm_2026-04-10_203432.log` hit `ELR=...100CE0E4`.
- This proves the early validation gates in `0x100CE028` all passed: `x25` was nonnull, the leading path word matched `0x5c`, `x23` was nonnull, and `(w24 & 3) != 0`.
- The stop was reached immediately before the `0x10064B08` call, so the next live gate is no longer argument validation but the call return plus the local state-machine on `[sp+0x20]`.
- Next staged split:
  - `0x100CE0F4 -> UDF`
  - `0x100CE19C -> UDF`
- Interpretation:
  - `0x100CE0F4` hit: `0x10064B08` returned nonnegative and flow reached the local state checks
  - `0x100CE19C` hit: flow still reached the hardcoded `0xC000000D` path after the `0x10064B08` stage
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE0F4_or_100CE19C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_203730.md`

## 2026-04-10 20:40 JST - `0x10064B08` returned nonnegative; next split moves into the local state machine

- `teraterm_2026-04-10_203924.log` hit `ELR=...100CE0F4`.
- `X0 = 0` at the stop, so `0x10064B08` returned nonnegative.
- This means the next live gate is no longer the call return itself but the local state-machine that decodes `[sp+0x20]` and either accepts it or falls to the hardcoded `0xC000000D` path at `0x100CE19C`.
- Next staged split:
  - `0x100CE11C -> UDF`
  - `0x100CE19C -> UDF`
- Interpretation:
  - `0x100CE11C` hit: the local state value is in the accepted set and flow reaches the normalize/merge block
  - `0x100CE19C` hit: the local state decode still falls into the hardcoded `0xC000000D` path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE11C_or_100CE19C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_204050.md`

## 2026-04-10 20:46 JST - the local state decode accepted the `0x10064B08` result and reached the merge block

- `teraterm_2026-04-10_204501.log` hit `ELR=...100CE11C`.
- This proves the local state value loaded from `[sp+0x20]` was in the accepted set; flow did not fall to the hardcoded `0xC000000D` path at `0x100CE19C`.
- The next live gate is now the return from `0x100CE4E0`, which decides whether the merged result stays usable or becomes negative before the final object export.
- Next staged split:
  - `0x100CE160 -> UDF`
  - `0x100CE19C -> UDF`
- Interpretation:
  - `0x100CE160` hit: `0x100CE4E0` returned and its raw status can be read directly in `X0`
  - `0x100CE19C` hit: flow still somehow fell back into the hardcoded `0xC000000D` path before reaching the `0x100CE4E0` return site
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE160_or_100CE19C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_204621.md`

## 2026-04-10 20:50 JST - `0x100CE4E0` itself returns `0xC000000D`; next stop moves inside it to the first major branch

- `teraterm_2026-04-10_204817.log` hit `ELR=...100CE160`.
- `X0 = 0xC000000D` at the stop, so `0x100CE4E0` itself already returns the negative status.
- This means the current live source is no longer the caller-side state merge in `0x100CE028`; the failure is inside `0x100CE4E0`.
- Next staged stop:
  - `0x100CE684 -> UDF`
- Interpretation:
  - the stop is immediately after `0x101CE530`; `X0` there will tell whether the function already produced an existing object / handle path or falls into the path-parse branch
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE684_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_205026.md`

## 2026-04-10 20:53 JST - `0x101CE530` returned null, so `0x100CE4E0` is now in its path-parse branch

- `teraterm_2026-04-10_205215.log` hit `ELR=...100CE684`.
- `X0 = 0` at the stop, so `0x101CE530` did not produce an existing object/handle path.
- Flow therefore takes the path-parse branch beginning at `0x100CE68C`.
- Next staged split:
  - `0x100CE6A0 -> UDF`
  - `0x100CE8F8 -> UDF`
- Interpretation:
  - `0x100CE6A0` hit: the input path matched the root-only special case and flow entered the short branch
  - `0x100CE8F8` hit: flow fell into the normal named-path branch instead
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE6A0_or_100CE8F8_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_205333.md`

## 2026-04-10 20:56 JST - `0x100CE4E0` took the normal named-path branch, not the root-only special case

- `teraterm_2026-04-10_205537.log` hit `ELR=...100CE8F8`.
- This proves the root-only special case was not taken; flow entered the normal named-path branch.
- The next live question is whether `0x100CEB30` can synthesize a usable object for that path, or whether the branch falls into the local `0xC0000017` failure.
- Next staged split:
  - `0x100CE914 -> UDF`
  - `0x100CE920 -> UDF`
- Interpretation:
  - `0x100CE914` hit: `0x100CEB30` returned null and the branch falls to local `0xC0000017`
  - `0x100CE920` hit: the branch produced a nonnull `x21` and continues into the deeper parse path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE914_or_100CE920_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_205654.md`

## 2026-04-10 20:58 JST - the normal named-path branch produced a nonnull `x21`, so flow continues into recursive parsing

- `teraterm_2026-04-10_205842.log` hit `ELR=...100CE920`.
- `X21 = 0x40002980` at the stop, so `0x100CEB30` produced a nonnull object/string handle and the local `0xC0000017` path was not taken.
- Flow therefore continues into the recursive parse call `0x100CE944`.
- Next staged stop:
  - `0x100CE94C -> UDF`
- Interpretation:
  - `X0` at that stop is the recursive `0x100CE4E0` return. If it is already negative, the failure chain has recursed one level deeper.
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE94C_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_210004.md`


## 2026-04-10 21:02 JST - the recursive parse fell into the root-only special-case path; next split moves inside `0x10064F48` vs local object validation

- `teraterm_2026-04-10_210230.log` hit `ELR=...100CE6A0`.
- This proves the deeper recursive `0x100CE4E0` invocation changed shape and entered the root-only special-case branch rather than staying on the normal named-path branch.
- Key state at the stop included `X24 = 0x40002A20`, `X10 = 0x5`, `X21 = 0`, `X22 = 0`, `X23 = 0`, and `X28 = 1`.
- Next staged split:
  - `0x100CE6B8 -> UDF`
  - `0x100CE704 -> UDF`
- Interpretation:
  - `0x100CE6B8` hit: `0x10064F48` returned and the next live question is whether its status is already negative
  - `0x100CE704` hit: the branch fell through the local `[sp+0x38]` / `0x101B0DE0` checks into the shared post-root path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE6B8_or_100CE704_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_210503.md`

## 2026-04-10 21:08 JST - `0x10064F48` itself is nonnegative; next split separates local object-check failure from `0x101B0DE0` failure

- `teraterm_2026-04-10_210807.log` hit `ELR=...100CE6B8`.
- `X0 = 0` there, proving `0x10064F48` itself returned nonnegative.
- This moves the live gate forward into the local `[sp+0x38]` object validation and then the `0x101B0DE0` helper.
- Next staged split:
  - `0x100CE6DC -> UDF`
  - `0x100CE700 -> UDF`
  - `0x100CE704 -> UDF`
- Interpretation:
  - `0x100CE6DC` hit: local object validation passed and `0x101B0DE0` returned
  - `0x100CE700` hit: `0x101B0DE0` returned negative and the branch took the local error leg
  - `0x100CE704` hit: the branch fell through the local `[sp+0x38]` / size / pointer checks before or without a successful `0x101B0DE0` path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE6DC_or_100CE700_or_100CE704_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_224445.md`

## 2026-04-10 22:47 JST - root-only special-case path skipped `0x101B0DE0`; local object field `[x9+0xC]` was zero

- `teraterm_2026-04-10_224715.log` hit `ELR=...100CE704`.
- The register state at the stop showed `X9 = 0x40001EC0` and `X8 = 0`, which matches the sequence `ldr x9, [sp,#0x38] ; ldr w8, [x9,#0xC] ; cbz w8, #0x100CE704`.
- This proves `0x10064F48` returned nonnegative and produced a nonnull local object, but that object's `+0xC` field was zero, so flow never reached `0x101B0DE0` and instead merged directly into the shared post-root path.
- Next staged split:
  - `0x100CE7A4 -> UDF`
  - `0x100CE81C -> UDF`
  - `0x100CE884 -> UDF`
- Interpretation:
  - `0x100CE7A4` hit: the optional callback path via global object table and `[x8+0x88]` returned, exposing `x20`
  - `0x100CE81C` hit: `x20` was nonzero and survived the `0x1021FB48` / `0x100CD9B0` checks
  - `0x100CE884` hit: `x20` stayed zero and flow took the local list/scan fallback path
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE7A4_or_100CE81C_or_100CE884_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_224835.md`

## 2026-04-10 22:50 JST - the callback-produced `x20` was zero; flow fell into the local list/scan fallback

- `teraterm_2026-04-10_225043.log` hit `ELR=...100CE7A4`.
- At that stop, `X0 = 0`, and the instruction is `mov x20, x0`, so the callback/dispatch path did not produce a usable `x20` object.
- This means the later `cbz x20, #0x100CE884` branch is taken, and flow falls into the local list/scan fallback rather than the `0x1021FB48` / `0x100CD9B0` validation path.
- Next staged split:
  - `0x100CE89C -> UDF`
  - `0x100CE8F0 -> UDF`
- Interpretation:
  - `0x100CE89C` hit: the local list is nonempty and flow reaches the first entry scan block
  - `0x100CE8F0` hit: the local list is empty and flow skips directly to the post-scan tail
- New staged EFI:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CE89C_or_100CE8F0_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260410_225209.md`
## 2026-04-10 22:59 JST
- `teraterm_2026-04-10_225937.log` is valid against the `22:52` staging of `stop_100CE89C_or_100CE8F0_udf`.
- Hit `ELR=...100CE89C`.
- Meaning: the local list fallback is nonempty and flow entered the first-entry scan block.
- Next split staged: `0x100CE8A4 / 0x100CE8D4 / 0x100CE8E4`.
## 2026-04-10 23:04 JST
- `teraterm_2026-04-10_230434.log` is valid against the `23:02` staging of `stop_100CE8A4_or_100CE8D4_or_100CE8E4_udf`.
- Hit `ELR=...100CE8A4`.
- Meaning: flow entered the first-entry callback path of the local list fallback; it did not go directly to empty-list merge.
- Next split prepared: `0x100CE8C8 / 0x100CE8D4` to distinguish `w28` equality from other callback return statuses.
## 2026-04-10 23:08 JST
- `teraterm_2026-04-10_230851.log` is valid against the `23:06` staging of `stop_100CE8C8_or_100CE8D4_udf`.
- Hit `ELR=...100CE8D4`.
- Meaning: the first-entry callback return matched the local `w28` sentinel and flowed to the next-entry path, not the merge path.
- Next split staged: `0x100CE8A4 / 0x100CE8E4` to distinguish retrying the next entry from reaching list-end merge.
## 2026-04-10 23:11 JST
- `teraterm_2026-04-10_231202.log` is valid against the `23:09` staging of `stop_100CE8A4_or_100CE8E4_udf_loopcheck`.
- Hit `ELR=...100CE8A4` again.
- Meaning: first-entry callback returned the local `w28` sentinel and the scan actually advanced to a subsequent entry; merge was not reached yet.
- Next probe staged: `0x100CE8E4` only, to see whether any later entry eventually reaches merge.
## 2026-04-10 23:15 JST
- `teraterm_2026-04-10_231513.log` is valid against the `23:13` staging of `stop_100CE8E4_udf_mergereach`.
- Hit `ELR=...100CE8E4`.
- Meaning: the list scan eventually reached merge; the loop did not stay in per-entry retry forever.
- Next split staged: `0x100CE9A4 / 0x100CEABC` to distinguish success-side object commit from negative tail cleanup.
## 2026-04-10 23:19 JST
- `teraterm_2026-04-10_231920.log` is valid against the `23:16` staging of `stop_100CE9A4_or_100CEABC_udf`.
- Hit `ELR=...100CEABC`.
- Meaning: after merge, flow falls into the negative tail cleanup rather than the success-side object commit path.
- Next split staged: `0x100CEAC4 / 0x100CEAD0` to distinguish local object cleanup from direct tail cleanup.
## 2026-04-10 23:25 JST
- 	eraterm_2026-04-10_232525.log is valid against the 23:20 staging of stop_100CEAC4_or_100CEAD0_udf.
- Hit ELR=...100CEAD0.
- Meaning: the negative tail skipped the local [sp+0x28] cleanup object and reached the post-local cleanup branch.
- Next split prepared:  x100CEADC / 0x100CEAE4 / 0x100CEAF0 / 0x100CEAF8.
- Interpretation:
  -  x100CEADC hit: x21 cleanup call is live
  -  x100CEAE4 hit: x22 cleanup call is live
  -  x100CEAF0 hit: x23 cleanup call is live
  -  x100CEAF8 hit: all earlier cleanup calls were skipped and flow fell straight to the epilogue
- Prepared EFI:
  - D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_100CEADC_or_100CEAE4_or_100CEAF0_or_100CEAF8_udf.EFI
- Staging pending because the removable media is not currently visible to Windows (Disk 3 / No Media).
## 2026-04-10 23:54 JST
- `teraterm_2026-04-10_235136.log` was valid against the image actually staged at that time, but that staged `BOOTAA64.stop_100CE94C_udf` binary was stale.
- The stale image still contained older stop points at `0x100CE6A0` and `0x100CE814`, so that run did not answer the intended clean `0x100CE94C` question.
- Rebuilt and verified a clean image `BOOTAA64.stop_100CE94C_udf.clean.EFI`.
- Verification on the clean image:
  - `0x100CE6A0` restored to original instruction stream
  - `0x100CE814` restored to original instruction stream
  - `0x100CE94C` is the only active `UDF`
- Restaged clean probe at `2026-04-10 23:54 JST`.
- Current staged split: clean `0x100CE94C` only.
## 2026-04-11 00:00 JST
- `teraterm_2026-04-10_235637.log` is valid against the `23:54 JST` clean `0x100CE94C` staging.
- Hit `ELR=...100CE94C` exactly, so the recursive `0x100CE4E0` call returned and `mov w25, w0` has executed.
- The CPU-state dump still recursed, so exact `w25` could not be read at that site.
- To avoid stale-image confusion and read the returned status more cleanly, restaged a new unique clean probe at `0x100CE950` only.
## 2026-04-11 00:06 JST
- `teraterm_2026-04-11_000207.log` is valid against the `23:59 JST` clean2 `0x100CE950` staging.
- No `ELR=...100CE950` fired.
- Instead, `BOOTAA64.EFI` returned via `gBS->Exit Status=Invalid Parameter`, which implies the preceding branch at `0x100CE94C` was taken.
- Meaning: recursive `0x100CE4E0` returned a negative status and flow branched directly to the local negative path at `0x100CE814`.
- Restaged a new unique clean probe with only `0x100CE814 = UDF`.
## 2026-04-11 00:18 JST
- `teraterm_2026-04-11_001554.log` is valid against the `00:13 JST` clean3 `0x100CE814` staging.
- Hit `ELR=...100CE814` exactly, confirming the recursive negative branch from `0x100CE94C` really lands on the local negative path.
- CPU-state dumping still recursed there, so exact returned status was not directly readable.
- Restaged a new unique clean probe at `0x100CE818` only, with `0x100CE814` restored to the original `ldr w2, [sp,#0x10]`.
## 2026-04-11 00:21 JST
- `teraterm_2026-04-11_002130.log` is valid against the `00:18 JST` clean4 `0x100CE818` staging.
- Hit `ELR=...100CE818`.
- Meaning: the recursive negative branch from `0x100CE94C` has executed `ldr w2, [sp,#0x10]` and reached the immediate branch-to-cleanup site; the local negative path itself is confirmed.
- Direct register recovery is still noisy at that site, so the next probe switches from raw register reading to a compare harness.
- New staged probe compares `w25` against `0xC000000D` using a temporary local harness at `0x100CE814..0x100CE828`.
- Interpretation of the new split:
  - `0x100CE824` hit: the recursive negative return is not `0xC000000D`
  - `0x100CE828` hit: the recursive negative return equals `0xC000000D`
## 2026-04-11 01:04 JST
- `teraterm_2026-04-11_010418.log` is valid against the `00:28 JST` compare probe `BOOTAA64.cmp_100CE814_eq_C000000D.clean5`.
- Hit `ELR=...100CE828`, the equal branch of the temporary compare harness.
- Meaning: the recursive `0x100CE4E0` call returning into `0x100CE94C` produced exactly `0xC000000D`.
- Next staged probe moves the compare to the local list merge site at `0x100CE8E4..0x100CE8F8` to determine whether `w25` is already `0xC000000D` when the scan reaches merge.
## 2026-04-11 01:11 JST
- `teraterm_2026-04-11_011133.log` is valid against the `01:09 JST` compare probe `BOOTAA64.cmp_100CE8E4_eq_C000000D.clean6`.
- Hit `ELR=...100CE8F8`, the equal branch of the temporary merge-site compare harness.
- Meaning: at the local list merge site, `w25` is already exactly `0xC000000D`.
- Therefore the later negative tail is not manufacturing `0xC000000D`; the error is already present when the scan loop reaches merge.
- Next staged probe moves the compare to the per-entry callback return at `0x100CE8C8..0x100CE8DC` to determine whether the callback itself returns `0xC000000D` before merge.
## 2026-04-11 01:44 JST
- `teraterm_2026-04-11_014428.log` is valid against the `01:41 JST` compare probe `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- Hit `ELR=...100CE8DC`, the equal branch of the temporary callback-return compare harness.
- Meaning: the local list per-entry callback itself returns exactly `0xC000000D`.
- This proves the merge site and later negative tail are only carrying `0xC000000D`; they are not generating it.
- The next staged probe no longer inspects merge/tail. It stops at `0x100CE8B8` so the live list entry dispatch state (`x19`, loaded callback pointer in `x8`, copied target in `x15`) can be read directly.
## 2026-04-11 12:03 JST
- Built and staged `BOOTAA64.stop_100CE8B8_udf.clean8`.
- Restored the temporary compare harness at `0x100CE8C8..0x100CE8DC` to the original instruction stream.
- The only new live stop is now `0x100CE8B8`, immediately before the per-entry `blr x15`.
- Intended readout:
  - recover the list node in `x19`
  - recover the loaded callback target in `x8` / `x15`
  - distinguish real code callback dispatch from static data-object traversal
## 2026-04-11 20:37 JST
- `teraterm_2026-04-11_203754.log` is valid against the `12:03 JST` clean8 staging.
- Hit `ELR=...100CE8B8`, confirming the path reaches the per-entry dispatch site immediately before the imported helper `0x102B26C0` and the final `blr x15`.
- Exact register recovery at that site was still obscured by recursive exception logging noise.
- Offline inspection of the nearby static image data showed that `bootmgfw + 0x2C39F0` is in `.data`, not `.text`, and contains what looks like a descriptor/table payload rather than executable code.
- This means the raw list-entry field is likely descriptor/data-driven and the live callback target must be understood after the helper return, not before it.
- Next staged probe moved to `0x100CE8BC` so the post-helper `x15` state can be observed directly.
## 2026-04-11 20:48 JST
- `teraterm_2026-04-11_204812.log` is valid against the `20:42 JST` clean9 staging.
- Hit `ELR=...100CE8BC`, confirming the imported helper `0x102B26C0` has already run and the path is now immediately before the final `blr x15`.
- This is the right observation point for the helper-resolved callback target, but the old exception handler still recursed before the general-purpose register dump became readable.
- To remove that blocker, the AArch64 `DefaultExceptionHandler` was patched so it emits a compact serial-only register block (`X0`, `X8`, `X15`, `X19..X28`) before any symbol walk / stack walk.
- The updated firmware was rebuilt and written back to SD after this log, so the next run on the same clean9 media should finally expose the live callback target directly.

## 2026-04-11 20:52 clean9 run and stale sd_boot image
- `teraterm_2026-04-11_205231.log` matched the staged `BOOTAA64.stop_100CE8BC_udf.clean9` probe on `F:` and hit `ELR=...100CE8BC`, but UART still showed the old exception output format with no `[A733-EXC-REG]` lines.
- Root cause was not the probe. `A733.fd` had been rebuilt with the new exception handler, but `write_sd.py` was still writing a stale `sd_boot.img` carrier.
- Manually reran `make_sd_image.py`, confirmed the regenerated image embedded `FD_MTIME_UTC=2026-04-11 11:50:09` and the new build stamp, then rewrote `PhysicalDrive3` and restaged clean9 onto `F:`.
- After this point, any new log must be taken after the `2026-04-11 20:58 JST` rewrite/restage, otherwise it is not valid for the new exception-register probe.

## 2026-04-11 21:09 clean9 callback-target resolution
- `teraterm_2026-04-11_210906.log` was captured after the regenerated `sd_boot.img` rewrite and clean9 restage. It showed the new firmware banner (`built at 11:49:55 on Apr 11 2026`) and emitted the new `[A733-EXC-REG]` line.
- At `ELR=bootmgfw+0xCE8BC`, the important registers were `X0=0`, `X8=0x23CD75210`, `X15=0x23CD75210`.
- Using the loaded BOOTAA64 base `0x23CC94000`, this resolves the live per-entry callback target to `bootmgfw + 0xE1210`.
- Disassembly of `0x100E1210` shows a full validation/parser callback, not a stub. The next split is whether that callback falls into the early hardcoded `0xC0000001` return at `0x100E13EC` or passes early validation and reaches the deeper helper block starting at `0x100E145C`.
- Current staged probe after this run: `BOOTAA64.stop_100E13EC_or_100E145C.clean10`.

## 2026-04-11 21:30 JST - later-entry callback returns exact 0xC000000D
- `teraterm_2026-04-11_213055.log` is valid against the `21:29 JST` compare probe `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- Hit `ELR=...100CE8DC`, the equal branch of the temporary callback-return compare harness.
- The compact register block at that site showed:
  - `X0 = 0xC000000D`
  - `X19 = 0x40001500`
  - `X25 = 0xC0000001`
  - `X28 = 0xC0000001`
- Therefore a later local-list per-entry callback itself returns exact `0xC000000D`; merge/tail code is only carrying it.
- `X15` observed at the compare site is not yet trusted as the actual callback target, because it was sampled after the callback returned.
- The next staged probe reverts the compare harness and moves back to the live dispatch site `0x100CE8B8` to recover the later-entry dispatch context directly.
- Current staged probe after this run: `BOOTAA64.stop_100CE8B8_udf.clean8`.

## 2026-04-11 21:56 JST clean11 descriptor decode

- Valid log: `teraterm_2026-04-11_215609.log`
- Dispatch site: `bootmgfw + 0xCE8B4` before `mov x15, x8`
- Raw values:
  - `X0=0`, `X2=0x23FFFEDD8`, `X8=0x23CD75210`, `X19=0x40001500`, `X24=0`
- Node dump for `X19=0x40001500`:
  - `+00=0x40001550`
  - `+08=bootmgfw+0x2C39F0` (data payload, not code)
  - `+10=bootmgfw+0xE1168`
  - `+18=bootmgfw+0xE11C8`
  - `+20=bootmgfw+0xE1210`
  - `+28=bootmgfw+0xE1D18`
- Static decode:
  - `0x100E1168`: alloc/init helper, writes globals at `0x10308000+0x9F0/+0x9F8`, returns `0` or `0xC0000017`
  - `0x100E11C8`: uses those globals, calls `0x101CE660`, cleanup, returns that status
  - `0x100E1210`: main callback target; early validation sentinel path returns `0xC0000001`, deeper path starts at `0x100E145C`
  - `0x100E1D18`: side helper around same globals, always returns `0`
- Meaning:
  - The later-entry descriptor is a structured callback record, not a single function pointer blob.
  - `+20` is the actual dispatch target seen at the site.

## 2026-04-11 22:00 JST clean11 + x2 dump firmware

- Exception firmware now also dumps `X2` and 4 qwords from `X2` when it points into the BOOTAA64 stack window.
- Rebuilt raw firmware at local build stamp `2026-04-11 21:59:57+0900` and rewrote `PhysicalDrive3`.
- Restaged current probe unchanged: `BOOTAA64.stop_100CE8B4_udf.clean11`.
- Static note: `0x102B26C0` is only a thunk (`ldr x16, [bootmgfw+0x1000]; br x16`), so the meaningful callback identity remains the raw `X8` target at the dispatch site.

## 2026-04-11 22:05 JST clean11 x2 dump re-enabled

- `teraterm_2026-04-11_220303.log` was valid against `clean11` and firmware `built at 12:59:58 on Apr 11 2026`.
- It confirmed the same later-entry dispatch values as `215609`, but still lacked `[A733-EXC-X2]` lines.
- Cause: the `X2` dump block had been dropped from `DefaultExceptionHandler.c` even though the firmware build stamp was newer.
- Fixed by re-adding `[A733-EXC-X2] +00/+08/+10/+18`, rebuilding raw firmware (`built at 13:04:52 UTC / 22:04:52 JST`), regenerating `sd_boot.img`, rewriting `PhysicalDrive3`, and restaging `BOOTAA64.stop_100CE8B4_udf.clean11`.

## 2026-04-11 22:27 JST clean11 with X2 dump

- Valid log: `teraterm_2026-04-11_222749.log` against firmware `built at 13:04:52 on Apr 11 2026` and `BOOTAA64.stop_100CE8B4_udf.clean11`.
- Dispatch site still stops at `bootmgfw + 0xCE8B4`.
- Captured pre-dispatch state:
  - `X0=0`, `X2=0x23FFFEDD8`, `X8=bootmgfw+0xE1210`, `X19=0x40001480`, `X24=0`
  - `X2` contents: `+00=0`, `+08=0`, `+10=0`, `+18=0xC0000001`
  - node contents: `+08=bootmgfw+0x2C29F0`, `+10=bootmgfw+0xE1168`, `+18=bootmgfw+0xE11C8`, `+20=bootmgfw+0xE1210`, `+28=bootmgfw+0xE1D18`
- Interpretation: this confirms the dispatch descriptor shape and that `x2` carries a mostly-zero context with a sentinel at `+18`, but `clean11` alone may still be stopping on the first dispatch occurrence rather than the exact entry that later returns `0xC000000D`.
- Switched back to `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` to catch the actual `000d`-returning entry under the new exception dump.

## 2026-04-11 22:31 JST clean7 with new X2/FP tracing

- Valid log: `teraterm_2026-04-11_223135.log` against `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` and firmware `built at 13:04:52 on Apr 11 2026`.
- It hit `ELR=bootmgfw+0xCE8DC`, i.e. the compare harness equality side for the later-entry callback loop.
- However the live register set at that site was already partly clobbered (`X2=7`, `X8=0x4E`, `X0=0xC0000001`), so it is not sufficient to recover the original callback context from registers alone.
- Added stack-local dump at `FP+0x18` (`[A733-EXC-FP18]`) to recover the original `sp+0x18` callback context even at the compare site.
- Rebuilt raw firmware (`built at 13:33:29 UTC / 22:33:29 JST`), regenerated `sd_boot.img`, rewrote `PhysicalDrive3`, and restaged `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.

## 2026-04-11 22:40 JST clean7 with FP+0x18 dump

- Valid log: `teraterm_2026-04-11_224025.log` against `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` and firmware `built at 13:33:30 on Apr 11 2026`.
- It again hit `ELR=bootmgfw+0xCE8DC`, the compare-harness equality side.
- `FP+0x18` recovered the original stack-local callback context:
  - `+00=0`, `+08=0`, `+10=0`, `+18=0xC0000001`
- The node dump remained the same descriptor cluster:
  - `+08=bootmgfw+0x2C39F0`
  - `+10=bootmgfw+0xE1168`
  - `+18=bootmgfw+0xE11C8`
  - `+20=bootmgfw+0xE1210`
  - `+28=bootmgfw+0xE1D18`
- Interpretation: even on the compare-harness equality side, the recovered callback context is still the same mostly-zero sentinel payload seen at the dispatch site. That means the `000d` source is not distinguished by richer `x2/sp+0x18` payload at this site.
- Switched back to `BOOTAA64.stop_100E13EC_or_100E145C.clean10` to re-enter the shared callback target `bootmgfw+0xE1210` and split early-sentinel return (`0x100E13EC`) from deeper-helper path (`0x100E145C`).

## 2026-04-12 01:53 JST clean10 early-return decode

- Valid log: `teraterm_2026-04-12_015325.log` against `BOOTAA64.stop_100E13EC_or_100E145C.clean10` and firmware `built at 13:33:30 on Apr 11 2026`.
- It hit `ELR=bootmgfw+0xE13EC`, i.e. the early sentinel-return block inside callback target `bootmgfw+0xE1210`.
- This means the current callback instance is not taking the deeper helper/global-state path at `0x100E145C`.
- The stack-local decode block around `FP+0x18` showed multiple invalid fields at once:
  - `FP+0x18 +00 = 0x00000001FFFFFFFF`
  - `FP+0x18 +08 = 0x0000020000000200`
  - `FP+0x18 +10 = 0x00088E7F00002351`
  - `FP+0x18 +18 = 0x800FB6BC00000900`
- Interpreting those qwords as the byte fields validated at `0x100E1324..0x100E13E8`:
  - `[sp+0x21] = 0x02` / `[sp+0x22] = 0x00`, so `ldurh [sp+0x21]` is nonzero and would already branch to `0x100E13EC`
  - `[sp+0x1B] = 0xFFFF`, which is outside the accepted set `{0x0200, 0x0400, 0x0800, 0x1000}`
  - `[sp+0x25] = 0x02`, which also fails the later `0xF0/0xF8` range gate
- Conclusion: this `clean10` hit is just an early `0xC0000001` reject on a malformed locally-decoded block, not the later callback invocation that actually returns `0xC000000D`.
- Because `clean10` is catching the first matching callback invocation rather than the interesting `000d` one, it is not the right active probe for the next run.
- Expanded the exception dump to print `FP+0x18 .. +0x38`, rebuilt raw firmware (`built at 2026-04-11T17:04:17Z / 2026-04-12T02:04:17+0900`), rewrote `PhysicalDrive3`, and switched the active ESP probe back to `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.

## 2026-04-12 02:18 JST clean7 with expanded FP dump

- Valid log: `teraterm_2026-04-12_021943.log` against `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` and firmware `built at 17:04:18 on Apr 11 2026`.
- It again hit `ELR=bootmgfw+0xCE8DC`, the compare-harness equality side for the `000d`-returning later-entry.
- Expanded `FP+0x18` dump now shows:
  - `+00=0`
  - `+08=0`
  - `+10=0`
  - `+18=0xC0000001`
  - `+20=0`
  - `+28=bootmgfw+0x2C39F0`
  - `+30=0x23FFFF070`
  - `+38=0x23FFFEE98`
- Node remains the same descriptor cluster at `X19=0x40001480` with `+20=bootmgfw+0xE1210`.
- Interpretation: the actual `000d`-returning later-entry still carries the same sentinel callback context and descriptor cluster; the extra frame locals do not introduce a new obvious discriminator at the compare site.
- Conclusion: the compare site is now exhausted as a source of new structure. The next useful probe is to let early `0xC0000001` returns in `bootmgfw+0xE1210` pass through and trap only if some invocation reaches the deeper path at `0x100E145C`.
- Built `BOOTAA64.stop_100E145C_only.clean12.EFI` with only the shared base patches plus `0x100E145C -> UDF`. Staging is pending the ESP remount because `F:` disappeared after the latest run.

## 2026-04-12 15:58 JST clean12 miss and rollback

- Valid log: `teraterm_2026-04-12_155835.log` against `BOOTAA64.stop_100E145C_only.clean12` staged at `2026-04-12 15:36:29 JST`.
- Direct removable boot still occurred:
  - `StartImage path=\EFI\BOOT\BOOTAA64.EFI`
  - `gBS->Exit Status=Invalid Parameter`
  - `StartImage watch end Status=Invalid Parameter`
  - `EfiBootManagerBoot failed: Invalid Parameter`
- No `[A733-EXC]` stop was emitted at `0x100E145C`.
- Interpretation: on this run no invocation of `bootmgfw+0xE1210` reached the deeper helper/global-state path. `clean12` therefore did not catch the true `000d` source and only proved that the direct `BOOTAA64` path still returns `EFI_INVALID_PARAMETER`.
- The later `bootmgfw.efi` start from shell fallback showed `ConvertPages: Incompatible memory types`; that is retry contamination after `BOOTAA64.EFI` already returned.
- Conclusion: the working hypothesis "the interesting `000d` comes from the deeper `0x100E145C` path of `bootmgfw+0xE1210`" is weak.
- Rebuilt raw firmware from the current `DefaultExceptionHandler.c` source with next-node exception tracing (`BUILD_STAMP_LOCAL=2026-04-12T16:08:36+0900`), regenerated `sd_boot.img`, rewrote `PhysicalDrive3`, and restaged `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- Current active ESP probe after restaging:
  - marker: `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_160911.md`

## 2026-04-12 16:12 JST clean7 ambiguity and next-node cluster

- Valid log: `teraterm_2026-04-12_161209.log` against `windows_media_F_20260412_160911.md` / active marker `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- It hit `ELR=bootmgfw+0xCE8DC`, but disassembly of `clean7` showed this probe is ambiguous: the patched block can trap on the local sentinel equality path before the explicit `C000000D` compare.
- Therefore `ELR=...100CE8DC` cannot be treated as a unique proof of `C000000D`.
- The useful new structure in this log is the next-node descriptor cluster exposed by `[A733-EXC-NODE]`:
  - current node `X19=0x40001480` still carries `+20 = bootmgfw+0xE1210`
  - next node `0x400014D0` carries a different cluster with `+10=bootmgfw+0xDC158`, `+18=bootmgfw+0xDC190`, `+20=bootmgfw+0xDC1A0`, `+28=0`
- Static disassembly confirms `0x100DC1A0` is not a function entry but an interior block inside the larger routine `0x100DB4C0-0x100DC710`; it is still the exact target stored in the next-node descriptor.
- Conclusion: stop treating `clean7` as a precise `000d` probe. The next useful experiment is to trap the alternate next-node callback target directly.
- Built and staged `BOOTAA64.stop_100DC1A0_udf.clean13`.
- Active marker after staging:
  - `BOOTAA64.stop_100DC1A0_udf.clean13`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_161920.md`

## 2026-04-12 16:43 JST clean13 miss and fallback to wider dispatch-chain tracing

- Valid log: `teraterm_2026-04-12_164343.log` against `analysis/media_snapshots/windows_media_F_20260412_161920.md` / active marker `BOOTAA64.stop_100DC1A0_udf.clean13`.
- No `[A733-EXC]` stop was emitted at `0x100DC1A0`.
- Direct removable boot still returned `gBS->Exit(Status=Invalid Parameter)` from `\EFI\BOOT\BOOTAA64.EFI`; later `ConvertPages: Incompatible memory types` belongs to shell-fallback retry noise.
- Interpretation: the speculative alternate-cluster target `bootmgfw+0xDC1A0` did not execute on the direct path in this run. Treating the next-node cluster as the immediate live callback source is too strong.
- Pivot: stop chasing the speculative alternate target and go back to the known dispatch site `0x100CE8B4`, but widen the firmware exception dump from `NODE/NEXT` to `NODE/NEXT/NEXT2` so one trap captures a larger slice of the callback chain.
- Updated `DefaultExceptionHandler.c` to emit `[A733-EXC-NEXT2]`, rebuilt firmware (`BUILD_STAMP_UTC=2026-04-12T07:49:47Z` / local 16:49:47+0900), regenerated `sd_boot.img`, rewrote `PhysicalDrive3`, and restaged `BOOTAA64.stop_100CE8B4_udf.clean11`.
- Active snapshot after restaging: `analysis/media_snapshots/windows_media_F_20260412_165014.md`.


## 2026-04-12 17:00 JST clean11 with NODE/NEXT/NEXT2 chain

- Valid log: `teraterm_2026-04-12_170051.log` against `analysis/media_snapshots/windows_media_F_20260412_165014.md` / active marker `BOOTAA64.stop_100CE8B4_udf.clean11`.
- It again hit the dispatch site `ELR=bootmgfw+0xCE8B4`.
- Live dispatch-site registers:
  - `X0=0`
  - `X2=0x23FFFEDD8`
  - `X8=0x23CC54210`
  - `X19=0x40001580`
  - `X24=0`
  - `X25=0xC0000001`
  - `X28=0xC0000001`
- `X2` and `FP+0x18` both still carry the same sentinel-style payload:
  - `+00=0`
  - `+08=0`
  - `+10=0`
  - `+18=0xC0000001`
- Descriptor chain captured from the node list:
  - current node `0x40001580`: `+20 = bootmgfw+0xE1210`
  - next node `0x400015D0`: `+20 = bootmgfw+0xDE1A0`
  - next-next node `0x40001620`: `+20 = bootmgfw+0xD8840`
- Static disassembly on `BOOTAA64.original.EFI` confirms:
  - `0x100DE1A0` is a real function entry (`0x100DE1A0-0x100DEA68`)
  - `0x100D8840` is also a real function entry (`0x100D8840-0x100D9408`)
- Interpretation: instead of chasing speculative interior sites, the immediate alternate callback chain now exposes two concrete function-entry targets.
- Pivot: build and stage a direct probe for the first alternate live target `bootmgfw+0xDE1A0`.
- Current active ESP probe after pivot:
  - marker: `BOOTAA64.stop_100DE1A0_udf.clean14`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_170406.md`


## 2026-04-12 17:06 JST clean14 direct hit on NEXT callback

- Valid log: `teraterm_2026-04-12_170632.log` against `analysis/media_snapshots/windows_media_F_20260412_170406.md` / active marker `BOOTAA64.stop_100DE1A0_udf.clean14`.
- It hit `ELR=bootmgfw+0xDE1A0`, so the immediate `NEXT` node callback target is live on the direct removable-media path.
- Registers at the hit:
  - `X0=0`
  - `X2=0x23FFFEDD8`
  - `X8=X15=bootmgfw+0xDE1A0`
  - `X19=0x400015D0`
  - `X24=0`
  - `X25=0xC0000001`
  - `X28=0xC0000001`
- The trapped node is the `NEXT` descriptor cluster captured from the previous `clean11` run:
  - `+10=bootmgfw+0xDC158`
  - `+18=bootmgfw+0xDC190`
  - `+20=bootmgfw+0xDE1A0`
  - `+28=0`
- `NEXT2` from this run also exposes a further real-function cluster:
  - node `0x40001690`
  - `+10=bootmgfw+0x105B70`
  - `+18=bootmgfw+0x105DE0`
  - `+20=bootmgfw+0x105EC8`
  - `+28=bootmgfw+0x85120`
- Interpretation: the callback chain is now confirmed to step from the sentinel-style current node into a real alternate function-entry target at `0x100DE1A0`.
- Next split should stay inside `0x100DE1A0` itself and decide whether its first global gate falls into hardcoded `0xC00000BB` (`0x100DE210`) or proceeds to the deeper body (`0x100DE218`).
- Active probe after restaging:
  - marker: `BOOTAA64.stop_100DE210_or_100DE218.clean15`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_170742.md`


## 2026-04-12 17:24 JST clean15 first-gate result

- Valid log: `teraterm_2026-04-12_172424.log` against `analysis/media_snapshots/windows_media_F_20260412_170742.md` / active marker `BOOTAA64.stop_100DE210_or_100DE218.clean15`.
- It hit `ELR=bootmgfw+0xDE218`, not `0xDE210`.
- Interpretation: the first global-byte gate in `bootmgfw+0xDE1A0` passes. The hardcoded `0xC00000BB` early return at `0x100DE210` is not the current path.
- The trapped invocation has:
  - `X0=0`
  - `X2=0x23FFFEDD8`
  - `X8=1`
  - `X15=bootmgfw+0xDE1A0`
  - `X19=0x400015D0`
  - `X25=0`
  - `X28=0x23FFFEDD8`
- Next probe should stop after the first helper call `0x10064B08` to read its exact return status.
- Active probe after restaging:
  - marker: `BOOTAA64.stop_100DE224.clean16`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_205359.md`


## 2026-04-12 20:57 JST clean16 helper return

- Valid log: `teraterm_2026-04-12_205729.log` against `analysis/media_snapshots/windows_media_F_20260412_205359.md` / active marker `BOOTAA64.stop_100DE224.clean16`.
- It hit `ELR=bootmgfw+0xDE224`, immediately after `bl #0x10064B08` in `bootmgfw+0xDE1A0`.
- `X0=0`, so `0x10064B08` itself is nonnegative/success.
- Current invocation state at the hit:
  - `X2=0`
  - `X8=0x400025F0`
  - `X19=0x400015D0`
  - `X24=0`
  - `X25=0`
  - `X28=0x23FFFEDD8`
- The next useful split is the local decode/validation gate after `0x10064B08`:
  - success path into `0x100DE260`
  - error path into `0x100DEA18` / hardcoded `0xC00000BB`
- Active probe after restaging:
  - marker: `BOOTAA64.stop_100DE260_or_100DEA18.clean17`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_205835.md`

## 2026-04-12 21:01 JST clean17 local validation failure

- Valid log: `teraterm_2026-04-12_210107.log` against `analysis/media_snapshots/windows_media_F_20260412_205835.md` / active marker `BOOTAA64.stop_100DE260_or_100DEA18.clean17`.
- It hit `ELR=bootmgfw+0xDEA18`, not `0xDE260`.
- Interpretation: after `0x10064B08` succeeds, the local decode/validation inside `bootmgfw+0xDE1A0` fails and enters the hardcoded `0xC00000BB` report path.
- The failure-site state has:
  - `X0=0`
  - `X2=0`
  - `X8=3`
  - `X19=0`
  - `X24=0`
  - `X25=0`
  - `X28=0x23FFFEDD8`
- `X8=3` is the value to explain next, but it is still ambiguous whether it came from the nonzero `[sp+0x40]` path or the zero `[sp+0x40]` / `[sp+0x48]` path.
- Active probe after restaging:
  - marker: `BOOTAA64.stop_100DE22C_or_100DE24C.clean18`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_210338.md`

## 2026-04-12 21:25 JST clean18 decoded-word entry

- Valid log: `teraterm_2026-04-12_212527.log` against `analysis/media_snapshots/windows_media_F_20260412_210338.md` / active marker `BOOTAA64.stop_100DE22C_or_100DE24C.clean18`.
- It hit `ELR=bootmgfw+0xDE22C`.
- Interpretation: execution reached the local decode inspection point immediately after `0x10064B08`; it is about to load the first decoded word from `[sp+0x40]`.
- The hit occurs before the `ldr w8, [sp,#0x40]` executes, so `X8=0x400025F0` is stale and does not yet identify the decoded word.
- Generated next split, but staging is pending because `F:` was not present:
  - pending image: `build/BOOTAA64.stop_100DE240_or_100DE250.clean19.EFI`
  - pending SHA256: `E62FCF4329C142D14973F856DADBE510753C7094EF590521EEFF9C7BE74949DC`
  - intended marker: `BOOTAA64.stop_100DE240_or_100DE250.clean19`
  - intended stop sites: `0x100DE240` and `0x100DE250`
- Staged after `F:` returned:
  - marker: `BOOTAA64.stop_100DE240_or_100DE250.clean19`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_213159.md`
- Reading rule for the pending split:
  - `0x100DE240` hit: `[sp+0x40]` is nonzero and its original value should be in `X8`
  - `0x100DE250` hit: `[sp+0x40]` was zero and `[sp+0x48]` should be in `X8`

## 2026-04-12 21:34 JST clean19 decoded type/version value

- Valid log: `teraterm_2026-04-12_213404.log` against `analysis/media_snapshots/windows_media_F_20260412_213159.md` / active marker `BOOTAA64.stop_100DE240_or_100DE250.clean19`.
- It hit `ELR=bootmgfw+0xDE250`, not `0xDE240`.
- Interpretation:
  - `[sp+0x40] == 0`
  - `[sp+0x48] == 3`
  - the local validation fails because `bootmgfw+0xDE250` compares this value against `4`
- Generated and staged the next bypass probe:
  - marker: `BOOTAA64.bypass_100DE254_stop_100DE25C.clean20`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_213515.md`
  - SHA256: `2E057B951C8F1FB5FB9A7A7C06615D7BA5AE3F6910220BF39CDC54F629400D66`
- Clean20 temporarily NOPs the failing `b.ne` at `0x100DE254` and stops at `0x100DE25C`, after `ldr w8, [sp,#0x54]`.
- Reading rule:
  - at `0x100DE25C`, `X8` should contain `[sp+0x54]`, the next local-validation value

## 2026-04-12 21:37 JST clean20 second field value

- Valid log: `teraterm_2026-04-12_213704.log` against `analysis/media_snapshots/windows_media_F_20260412_213515.md` / active marker `BOOTAA64.bypass_100DE254_stop_100DE25C.clean20`.
- It hit `ELR=bootmgfw+0xDE25C` with `X8=2`.
- Interpretation: after temporarily bypassing the `[sp+0x48] == 4` check, the next validation field is `[sp+0x54] == 2`; the original `cbnz w8` would fail because it expects zero.
- Current decoded local fields:
  - `[sp+0x40] == 0`
  - `[sp+0x48] == 3`, but this path expects `4`
  - `[sp+0x54] == 2`, but this path expects `0`
- Generated and staged the next bypass probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE278.clean21`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_213838.md`
  - SHA256: `652626C6A87FDF3339E4EBBF0D809C0C1F445530D9AB2A52D79EFD488664B8F0`
- Clean21 temporarily bypasses both local field checks and stops at `0x100DE278`, immediately after `bl #0x10055790`.
- Reading rule:
  - at `0x100DE278`, `X0` is the return status from `0x10055790`
  - `X20` is not loaded yet, because the original instruction at `0x100DE278` is `ldr x20, [sp,#0x18]`

## 2026-04-12 21:40 JST clean21 first helper after field-bypass

- Valid log: `teraterm_2026-04-12_214049.log` against `analysis/media_snapshots/windows_media_F_20260412_213838.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE278.clean21`.
- It hit `ELR=bootmgfw+0xDE278`.
- `X0=0`, so helper `0x10055790` succeeds after temporarily bypassing the two local field checks.
- The frame-local dump at the hit shows:
  - `[sp+0x18] == 0x40002AC0`, the table/list pointer that `0x100DE278` would load into `X20`
  - `[sp+0x30] == 0x23FFFEF70`, the count/descriptor value that later `0x100DE284` would load into `X27`
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2A0.clean22`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_214148.md`
  - SHA256: `D5D5D89BC7F8A938FC923677B0B10587FFE1481F7870E4BB8A23CADC12EAF608`
- Clean22 keeps the same two field bypasses and stops at `0x100DE2A0`, immediately after loop helper `0x10055938`.
- Reading rule:
  - at `0x100DE2A0`, `X0` is the return status from `0x10055938`
  - if `X0` is nonnegative, the next local check reads `[x9+4]` and expects `2`

## 2026-04-12 21:43 JST clean22 loop helper result

- Valid log: `teraterm_2026-04-12_214348.log` against `analysis/media_snapshots/windows_media_F_20260412_214148.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2A0.clean22`.
- It hit `ELR=bootmgfw+0xDE2A0`.
- `X0=0`, so loop helper `0x10055938` succeeds for the first table/list entry.
- The same frame-local values remain visible:
  - `[sp+0x18] == 0x40002AC0`
  - `[sp+0x30] == 0x23FFFEF70`
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2AC.clean23`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_215131.md`
  - SHA256: `A0D4B95F26F3090C91E0CE70A3B5FF0A54696741129DB55365EB6A9FF08768EB`
- Clean23 keeps the same two field bypasses and stops at `0x100DE2AC`, immediately after `ldr w8, [x9,#4]`.
- Reading rule:
  - at `0x100DE2AC`, `X8` is the `[x9+4]` field that the original code compares against `2`

## 2026-04-12 22:00 JST clean23 descriptor type field

- Valid log: `teraterm_2026-04-12_220020.log` against `analysis/media_snapshots/windows_media_F_20260412_215131.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2AC.clean23`.
- It hit `ELR=bootmgfw+0xDE2AC`.
- `X8=2`, so the `[x9+4]` descriptor field matches the expected value `2`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2C4.clean24`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_220115.md`
  - SHA256: `79FE67003E6D764E793B52F84518DDA91262E3AEAE862BB6DF5A4FA9E9E0EC70`
- Clean24 keeps the same two field bypasses and stops at `0x100DE2C4`, immediately after `bl #0x10066D18`.
- Reading rule:
  - at `0x100DE2C4`, `X0` is the return value from helper `0x10066D18`
  - original code compares that return value against `0x10`

## 2026-04-12 22:03 JST clean24 descriptor compare helper

- Valid log: `teraterm_2026-04-12_220312.log` against `analysis/media_snapshots/windows_media_F_20260412_220115.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2C4.clean24`.
- It hit `ELR=bootmgfw+0xDE2C4`.
- `X0=0` from helper `0x10066D18`.
- The following original instructions are:
  - `cmp x0, #0x10`
  - `csinc w23, w23, wzr, ne`
- Interpretation: this does not appear to be a simple fail-if-not-`0x10` gate. With the observed `X0=0`, the `ne` condition would preserve `w23` rather than setting it to `1`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2D8.clean25`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_220434.md`
  - SHA256: `6C02950959836E0B144A77F7ACBBD31CD6918169AD777EF66DC1B1DAA565986C`
- Clean25 keeps the same two field bypasses and stops at `0x100DE2D8`, immediately after helper `0x10056060`.
- Reading rule:
  - at `0x100DE2D8`, read `X0` as the return value from `0x10056060`
  - read `X23`/`W23` to see whether the earlier compare set the match flag

## 2026-04-12 22:06 JST clean25 post-descriptor-cleanup helper

- Valid log: `teraterm_2026-04-12_220653.log` against `analysis/media_snapshots/windows_media_F_20260412_220434.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2D8.clean25`.
- It hit `ELR=bootmgfw+0xDE2D8`.
- `X0=0`, so helper `0x10056060` succeeds.
- The current firmware exception dump does not print `X23`, so the `cbnz w23` branch at `0x100DE2D8` cannot be read directly from registers.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2DC_or_100DE2EC.clean26`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_220752.md`
  - SHA256: `48CCBC289A72731655C846A58B83587E724F06238B813D75697716A45E29D0E4`
- Clean26 keeps the same two field bypasses and stops on the branch outcomes after `0x100DE2D8`.
- Reading rule:
  - `0x100DE2DC` hit: `W23 == 0`, no match yet; loop advances to the next entry
  - `0x100DE2EC` hit: `W23 != 0`, match found; code enters the follow-up path

## 2026-04-12 22:10 JST clean26 no-match branch

- Valid log: `teraterm_2026-04-12_221011.log` against `analysis/media_snapshots/windows_media_F_20260412_220752.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2DC_or_100DE2EC.clean26`.
- It hit `ELR=bootmgfw+0xDE2DC`, not `0xDE2EC`.
- Interpretation: `W23 == 0`; the current descriptor entry did not match, and the code takes the loop-advance path.
- Generated and staged the next loop/end probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE290_or_100DE308.clean27`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_221058.md`
  - SHA256: `600CE24CCF97FA5E1E1490616235CF5059CFB4799B039EC3BF923BBF7D57E62D`
- Clean27 keeps the same two field bypasses and stops on the loop result after incrementing `w19`.
- Reading rule:
  - `0x100DE290` hit: loop continues to another table/list entry
  - `0x100DE308` hit: loop exhausted without a match and loads the default failure status

## 2026-04-12 22:14 JST clean27 ambiguous first-entry stop

- Valid log: `teraterm_2026-04-12_221422.log` against `analysis/media_snapshots/windows_media_F_20260412_221058.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE290_or_100DE308.clean27`.
- It hit `ELR=bootmgfw+0xDE290`.
- Correction: `0x100DE290` is also the first-entry processing site before any loop advance, so this hit is ambiguous and cannot prove that the loop advanced to a second entry.
- The register dump also shows `X19=0`, matching a first-entry invocation rather than a post-increment loop entry.
- Generated and staged the corrected loop/end probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2E0_or_100DE308.clean28`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_221517.md`
  - SHA256: `ED1B46C15893C1DB2BEC3BD52264E7DAF870CD2A9045186149F4D0D9433CA10F`
- Clean28 keeps the same two field bypasses and stops after the loop index increment at `0x100DE2E0`, or at the no-match default status load `0x100DE308`.
- Reading rule:
  - `0x100DE2E0` hit: loop reached the post-increment compare; read `X19/W19` as the incremented entry index if available
  - `0x100DE308` hit: loop exhausted without a match and loads the default failure status

## 2026-04-12 22:17 JST clean28 post-increment loop index

- Valid log: `teraterm_2026-04-12_221738.log` against `analysis/media_snapshots/windows_media_F_20260412_221517.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2E0_or_100DE308.clean28`.
- It hit `ELR=bootmgfw+0xDE2E0`, not `0x100DE308`.
- `X19=1` at the stop site, confirming the first descriptor/list entry was no-match and the loop reached the post-increment compare with entry index 1.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2A0.clean29`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_222021.md`
  - SHA256: `612CDB88BA088B6AEAF0C65EF0853184B18E47BDF72D20381B3185C69065C73E`
- Clean29 keeps the two local-field bypasses, changes `0x100DE288` from `mov w19,#0` to `mov w19,#1`, and stops at `0x100DE2A0`.
- Purpose:
  - skip directly to descriptor/list entry index 1
  - read `X0` at `0x100DE2A0` as the return value from helper `0x10055938` for entry index 1

## 2026-04-12 22:22 JST clean29 entry-1 helper result

- Valid log: `teraterm_2026-04-12_222217.log` against `analysis/media_snapshots/windows_media_F_20260412_222021.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2A0.clean29`.
- It hit `ELR=bootmgfw+0xDE2A0`.
- `X19=1`, confirming this is the forced entry-index-1 path.
- `X0=0`, so helper `0x10055938` succeeds for entry index 1 as well.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2DC_or_100DE2EC.clean30`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_222407.md`
  - SHA256: `AE62D8DC51B5011F7520629C04DF235FA1BF4962A659EE78B58AC0DAC44E0609`
- Clean30 keeps the two local-field bypasses, keeps `0x100DE288 -> mov w19,#1`, and stops on the branch outcomes after descriptor cleanup.
- Reading rule:
  - `0x100DE2DC` hit: entry index 1 is also no-match; loop would advance
  - `0x100DE2EC` hit: entry index 1 matched and enters the follow-up path

## 2026-04-12 22:26 JST clean30 entry-1 branch result

- Valid log: `teraterm_2026-04-12_222601.log` against `analysis/media_snapshots/windows_media_F_20260412_222407.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2DC_or_100DE2EC.clean30`.
- It hit `ELR=bootmgfw+0xDE2DC`, not `0x100DE2EC`.
- `X19=1`, confirming this was the forced entry-index-1 path.
- Interpretation: entry index 1 is also no-match; the original code would increment and continue scanning.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_start_index2_stop_100DE2A0.clean31`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_222652.md`
  - SHA256: `979A125291A0BA1D0ED309B240FC933A65CD8D6D096646E6D76A77DFE190AE94`
- Clean31 keeps the two local-field bypasses, changes `0x100DE288` to `mov w19,#2`, and stops at `0x100DE2A0`.
- Purpose:
  - skip directly to descriptor/list entry index 2
  - read `X0` at `0x100DE2A0` as the return value from helper `0x10055938` for entry index 2

## 2026-04-12 22:28 JST clean31 entry-2 helper result

- Valid log: `teraterm_2026-04-12_222858.log` against `analysis/media_snapshots/windows_media_F_20260412_222652.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_start_index2_stop_100DE2A0.clean31`.
- It hit `ELR=bootmgfw+0xDE2A0`.
- `X19=2`, confirming this is the forced entry-index-2 path.
- `X0=0xC000000D`, so helper `0x10055938` fails for entry index 2 with Invalid Parameter.
- Important interpretation: entry 0 and 1 were valid helper calls but no-match; entry 2 is not a valid next entry. This makes the observed `x27` count value suspect rather than proving that many entries must be scanned.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_stop_100DE308_or_100DE318.clean32`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_223203.md`
  - SHA256: `2A5DDA14E1C95A45B0E4665DE58D3E92EF9D1A7B76DE92DDCBDE6664681FCF39`
- Clean32 keeps the two local-field bypasses, patches `0x100DE284` from `ldr x27,[sp,#0x30]` to `mov x27,#2`, and stops at `0x100DE308` or `0x100DE318`.
- Purpose:
  - force the descriptor/list count to 2, matching the two entries that made valid helper calls
  - check whether the loop then reaches the no-match default status path at `0x100DE308` or gets past the post-cleanup failure gate to `0x100DE318`

## 2026-04-12 22:34 JST clean32 forced-count no-match default

- Valid log: `teraterm_2026-04-12_223400.log` against `analysis/media_snapshots/windows_media_F_20260412_223203.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_stop_100DE308_or_100DE318.clean32`.
- It hit `ELR=bootmgfw+0xDE308` with `X19=2`.
- Interpretation: with the descriptor/list count forced to 2, the loop checks entry 0 and 1, finds no match, and reaches the default no-match status load.
- The literal loaded at `0x100DE308` is `0xC0000225` from `0x100DEA5C`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE31C.clean33`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_223521.md`
  - SHA256: `F9EF78055758176AE11DD04F4FFBC4D8CF4893D88F4691F0141DD531958DA5E7`
- Clean33 keeps the two local-field bypasses and `x27=2`, changes `0x100DE308` from `ldr w19,#0x100DEA5C` to `mov w19,#0`, and stops at `0x100DE31C`.
- Purpose:
  - verify whether clearing only the no-match `0xC0000225` status lets execution pass the `0x100DE318` negative-status gate

## 2026-04-12 22:37 JST clean33 cleared no-match status reaches next block

- Valid log: `teraterm_2026-04-12_223709.log` against `analysis/media_snapshots/windows_media_F_20260412_223521.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE31C.clean33`.
- It hit `ELR=bootmgfw+0xDE31C`.
- `X19=0`, confirming that clearing the no-match `0xC0000225` status at `0x100DE308` lets execution pass the `0x100DE318` negative-status gate.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE32C.clean34`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_223911.md`
  - SHA256: `950727693B451B6F299EF74C70D4F11BB48947702306370DC9A8B744B484D93A`
- Clean34 keeps the two local-field bypasses, `x27=2`, and `0x100DE308 -> mov w19,#0`, then stops at `0x100DE32C`.
- Purpose:
  - read `X0` at `0x100DE32C` as the return value from helper `0x1028DA30`

## 2026-04-12 22:40 JST clean34 helper after cleared no-match

- Valid log: `teraterm_2026-04-12_224055.log` against `analysis/media_snapshots/windows_media_F_20260412_223911.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE32C.clean34`.
- It hit `ELR=bootmgfw+0xDE32C`.
- `X0=1`, so helper `0x1028DA30` returns `1`.
- Important limitation: `X19=0` at this stop, so clearing the no-match status alone likely leaves `[sp+0x38]` unset. Continuing from here would likely enter the `w20 == 1` path and then dereference `x19` at `0x100DE368`, which is not a valid way to progress.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE300.clean35`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_224211.md`
  - SHA256: `23C36666484CFCBAA97891E4E5224BF5626A7A095EF9078DAE95BF4D668F1AC4`
- Clean35 forces the match flag with `0x100DE230 -> mov w23,#1`, keeps the two local-field bypasses, forces `x27=2`, and stops at `0x100DE300`.
- Purpose:
  - force the `0x100DE2EC` match path for entry 0
  - read `X0` at `0x100DE300` as the return value from helper `0x10055938` that should populate `[sp+0x38]`

## 2026-04-12 22:45 JST clean35 forced-match helper result

- Valid log: `teraterm_2026-04-12_224547.log` against `analysis/media_snapshots/windows_media_F_20260412_224211.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE300.clean35`.
- It hit `ELR=bootmgfw+0xDE300`.
- `X0=0`, so the forced match path helper `0x10055938` succeeds for entry 0 with lookup key at `0x10013460` and output at `[sp+0x38]`.
- This is a better progression path than just clearing the no-match `0xC0000225` status, because it should populate the object pointer used after `0x100DE31C`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE320.clean36`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_224719.md`
  - SHA256: `2415CF09B8CB80D5300816A352442008F1B699B92E28DA8B43AF80F0FD91E421`
- Clean36 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE320`.
- Purpose:
  - execute `mov w19,w0`, cleanup, status gate, and `ldr x19,[sp,#0x38]`
  - read `X19` at `0x100DE320` as the object pointer loaded from `[sp+0x38]`

## 2026-04-12 22:49 JST clean36 forced-match object pointer

- Valid log: `teraterm_2026-04-12_224903.log` against `analysis/media_snapshots/windows_media_F_20260412_224719.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE320.clean36`.
- It hit `ELR=bootmgfw+0xDE320`.
- `X19=0x23FC514C0`, so the `0x100DE31C: ldr x19,[sp,#0x38]` load produced a non-null object pointer.
- Interpretation: the forced match path successfully populates the object pointer needed by the next block.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE32C.clean37`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_225032.md`
  - SHA256: `13719EA88C18D477A807B90F4FF19191177316CCBD7B7F2372606CC98C3CD65E`
- Clean37 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE32C`.
- Purpose:
  - read `X0` at `0x100DE32C` as the helper `0x1028DA30` return value on the forced-match/object-pointer-valid path

## 2026-04-12 22:52 JST clean37 object-pointer-valid helper result

- Valid log: `teraterm_2026-04-12_225219.log` against `analysis/media_snapshots/windows_media_F_20260412_225032.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE32C.clean37`.
- It hit `ELR=bootmgfw+0xDE32C`.
- `X0=1`, so helper `0x1028DA30` returns `1` on the forced-match/object-pointer-valid path.
- `X19=0x23FC514C0`, so the object pointer is still valid at this point.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE378.clean38`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_225408.md`
  - SHA256: `F301DD8C15F25D2D60C5FCA6E259996858F4F8456F786E6275DD3179ADC9594C`
- Clean38 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE378`.
- Purpose:
  - take the `w20 == 1` path to `0x100DE368`
  - read `X15` at `0x100DE378` as the indirect-call target loaded from `[x19+8]`
  - read `X0`/`X1` as the arguments to the nearby setup helper before `blr x15`

## 2026-04-12 22:55 JST clean38 object callback target

- Valid log: `teraterm_2026-04-12_225551.log` against `analysis/media_snapshots/windows_media_F_20260412_225408.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE378.clean38`.
- It hit `ELR=bootmgfw+0xDE378`.
- `X19=0x23FC514C0`, `X0=0x23FC514C0`, `X15=0x23FC25680`.
- `X15=0x23FC25680` is within the earlier observed DxeCore image range (`DxeCore Base=0x23FC22000 Size=0x35000`), so the upcoming `blr x15` target looks like a valid firmware callback/function pointer rather than garbage.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE380.clean39`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_225639.md`
  - SHA256: `604CBDC457CC2D0BFACC8D8F2D0F2645549F691A78F4CE831E1703051788B3FE`
- Clean39 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE380`.
- Purpose:
  - execute the indirect call `blr x15`
  - read `X0` at `0x100DE380` as the callback return value

## 2026-04-12 22:59 JST clean39 object callback return

- Valid log: `teraterm_2026-04-12_225909.log` against `analysis/media_snapshots/windows_media_F_20260412_225639.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE380.clean39`.
- It hit `ELR=bootmgfw+0xDE380`.
- `X0=0`, so the indirect `blr x15` callback returns success.
- The log also shows `OpenVolume Exit ... -> Success Root=23FC50B78` immediately before the stop, which is consistent with the callback successfully opening a Simple File System volume.
- `X19=0x23FC514C0` remains the object pointer.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE39C.clean40`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_225954.md`
  - SHA256: `F83B25CD6E42DC8A0EB48731B67D89537942CBE8499331B6D638787F6561020D`
- Clean40 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE39C`.
- Purpose:
  - follow the `w20 == 1` path through `0x100DE394 -> 0x100536E8`
  - read `X0` at `0x100DE39C` as the return value from helper `0x100536E8`

## 2026-04-12 23:01 JST clean40 post-callback validation helper

- Valid log: `teraterm_2026-04-12_230143.log` against `analysis/media_snapshots/windows_media_F_20260412_225954.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE39C.clean40`.
- It hit `ELR=bootmgfw+0xDE39C`.
- `X0=0`, so helper `0x100536E8` succeeds after the object callback path.
- At the stop, the replaced instruction is `mov w19,w0`, so the next original instruction would make `w19=0` and the negative-status gate at `0x100DE3A0` should not branch to `0x100DEA1C`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3A4.clean41`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_230241.md`
  - SHA256: `18FE4EA050322BE947B9182B396416A546419640912CDE63AA4EBD00ABEC9A93`
- Clean41 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE3A4`.
- Purpose:
  - confirm the negative-status gate after `0x100536E8` is passed and execution enters the next block

## 2026-04-12 23:04 JST clean41 enters next block

- Valid log: `teraterm_2026-04-12_230428.log` against `analysis/media_snapshots/windows_media_F_20260412_230241.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3A4.clean41`.
- It hit `ELR=bootmgfw+0xDE3A4`.
- `X19=0`, confirming the `0x100DE39C: mov w19,w0` / `0x100DE3A0: tbnz w19,#0x1f` gate was passed after helper `0x100536E8` returned success.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3C0_or_100DE3E8.clean42`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_230527.md`
  - SHA256: `344FA6839B7A7FD2F6F93A5280315CC32CE54D90B4C8E46A5C725D330D5BB001`
- Clean42 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE3C0` or `0x100DE3E8`.
- Purpose:
  - identify the first global-state branch path after entering the next block
  - `0x100DE3C0` hit: `w9 != 0` and `[x27+#0xdf4] == 0`; it enters the counter/update path
  - `0x100DE3E8` hit: global state skips that path, either because `w9 == 0` or `[x27+#0xdf4] != 0`

## 2026-04-12 23:07 JST clean42 first global-state branch

- Valid log: `teraterm_2026-04-12_230737.log` against `analysis/media_snapshots/windows_media_F_20260412_230527.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3C0_or_100DE3E8.clean42`.
- It hit `ELR=bootmgfw+0xDE3E8`, not `0x100DE3C0`.
- Interpretation: the counter/update path at `0x100DE3C0` was skipped due to global state (`w9 == 0` or `[x27+#0xdf4] != 0`).
- At the stop, `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE408_or_100DE534.clean43`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_230839.md`
  - SHA256: `76D1562DDA9CD8AF64415FF2AC61FD6FE1143ED23F333DD2E716F9F271F23E2F`
- Clean43 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE408` or `0x100DE534`.
- Purpose:
  - after the `0x100DE3E8` path, check whether global `[0x102EFDD8] == 1`
  - `0x100DE408` hit: global value equals `1`, enters the allocation/list scan path
  - `0x100DE534` hit: global value is not `1`, skips to the later no-`x20` failure handling path

## 2026-04-12 23:11 JST clean43 second global-state branch

- Valid log: `teraterm_2026-04-12_231139.log` against `analysis/media_snapshots/windows_media_F_20260412_230839.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE408_or_100DE534.clean43`.
- It hit `ELR=bootmgfw+0xDE408`, not `0x100DE534`.
- Interpretation: global `[0x102EFDD8] == 1`, so execution enters the allocation/list scan path.
- At the stop, `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE420.clean44`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_231230.md`
  - SHA256: `5F2FE3DA69D98C475808E2F237CD4BFE4702DC92EE3921EB1ACE81581963AD3F`
- Clean44 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE420`.
- Purpose:
  - read `X9` at `0x100DE420` as the global list/table pointer loaded by `0x100DE41C: ldr x9,[x20,#0xde0]`
  - this determines whether the following loop has a list to scan or falls to the no-list path

## 2026-04-12 23:14 JST clean44 list/table pointer probe

- Valid log: `teraterm_2026-04-12_231415.log` against `analysis/media_snapshots/windows_media_F_20260412_231230.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE420.clean44`.
- It hit `ELR=bootmgfw+0xDE420`.
- `X8=2`, so execution is in the list scan loop with the initial index value.
- At this point the original instruction is `0x100DE420: cbz x9,#0x100DE450`, with `x9` loaded by `0x100DE41C: ldr x9,[x20,#0xde0]`.
- The exception dump does not include `X9`, so the list/table pointer value is not directly readable from this run.
- At the stop, `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE428_or_100DE450.clean45`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_231705.md`
  - SHA256: `38FDB3A20BA8759427FA67A2348CBDC06B9849CB2689F75206E4847014871789`
- Clean45 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE428` or `0x100DE450`.
- Purpose:
  - `0x100DE428` hit: `x9` was nonzero; `0x100DE424: ldr x0,[x9,w8,uxtw #3]` ran and `X0` should contain the entry pointer for index 2
  - `0x100DE450` hit: `x9` was null and the code took the no-list path

## 2026-04-12 23:19 JST clean45 list entry index 2

- Valid log: `teraterm_2026-04-12_231902.log` against `analysis/media_snapshots/windows_media_F_20260412_231705.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE428_or_100DE450.clean45`.
- It hit `ELR=bootmgfw+0xDE428`, not `0x100DE450`.
- Interpretation: the global list/table pointer from `[x20+#0xde0]` was non-null.
- `X0=0` and `X8=2`, so list entry index 2 is null after `0x100DE424: ldr x0,[x9,w8,uxtw #3]`.
- At the stop, `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE42C_or_100DE460.clean46`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_232023.md`
  - SHA256: `B56139438F6E71848154EBDD729B6330BFF39CACD7E374170E06505D45646EF7`
- Clean46 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE42C` or `0x100DE460`.
- Purpose:
  - `0x100DE42C` hit: a non-null list entry was found before loop exhaustion; read `X0` as that entry pointer and `X8` as the index
  - `0x100DE460` hit: the list scan reached the loop-exit test; read `X0`/`X8` to determine whether entries 2..6 were all null

## 2026-04-12 23:22 JST clean46 list scan exhausted

- Valid log: `teraterm_2026-04-12_232204.log` against `analysis/media_snapshots/windows_media_F_20260412_232023.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE42C_or_100DE460.clean46`.
- It hit `ELR=bootmgfw+0xDE460`, not `0x100DE42C`.
- `X0=0` and `X8=7`.
- Interpretation: the scan of list entries index 2..6 found no usable/non-null entry, so original `0x100DE460: cbz x0,#0x100DE4B8` would branch to the fallback/allocation path.
- At the stop, `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE524_or_100DE590.clean47`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260412_232335.md`
  - SHA256: `EA641A82AB257E80301CF0912C63B2BB03964E528C2CA29B1DCEDD08C0525FCC`
- Clean47 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE524` or `0x100DE590`.
- Purpose:
  - `0x100DE524` hit: fallback allocation helper `0x101DEAC8(0x90)` returned; read `X0` as its status/pointer value
  - `0x100DE590` hit: a usable block was obtained from the free-list/success path; read `X0` as the block pointer

## 2026-04-12 23:29 JST clean47 fallback block acquired

- Valid log: `teraterm_2026-04-12_232923.log` against `analysis/media_snapshots/windows_media_F_20260412_232335.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE524_or_100DE590.clean47`.
- It hit `ELR=bootmgfw+0xDE590`, not `0x100DE524`.
- `X0=0x40002AD0`, so the fallback/free-list path produced a usable block pointer.
- The following original code would do `x24=x0`, then `x20=x24+0x10`, so expected `x20` for the next initialized object area is approximately `0x40002AE0`.
- `X19=0x23CE62000`; `[sp+0x38]` also shows `0x23CE62000`.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE564_or_100DE5A8.clean48`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_022259.md`
  - SHA256: `7F53D52056CC15E929DE50EE3858758C0F66C39B28F4EC9DDF29E3E6AB418402`
- Clean48 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE564` or `0x100DE5A8`.
- Purpose:
  - `0x100DE5A8` hit: `x20` is non-null and the newly acquired block/object initialization path is entered
  - `0x100DE564` hit: `x20` is null and the path is falling to status `0xC0000225`/failure handling

## 2026-04-13 02:32 JST clean48 block initialization reached

- Valid log: `teraterm_2026-04-13_023225.log` against `analysis/media_snapshots/windows_media_F_20260413_022259.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE564_or_100DE5A8.clean48`.
- It hit `ELR=bootmgfw+0xDE5A8`, not `0x100DE564`.
- `X0=0x40002AD0` and `X24=0x40002AD0`, confirming the fallback/free-list block from clean47 is now the active block.
- `X8=0`, consistent with the header pointer having been masked/cleared before initialization.
- Interpretation: `x20` was non-null and the new block/object initialization path is reached, not the `0xC0000225` failure path.
- Generated and staged the next global-gate branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE5FC_or_100DE728.clean49`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_023332.md`
  - SHA256: `2A132FB436FD46F591F979695BC1A29A13220C8452544D6FF59ADB8C5BBDD1CB`
- Clean49 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE5FC` or `0x100DE728`.
- Purpose:
  - `0x100DE5FC` hit: global `[0x102EFDD8] == 1` and the second/smaller block scan-allocation path is entered
  - `0x100DE728` hit: global `[0x102EFDD8] != 1` or post-allocation fallback reached the later counter/finalization block

## 2026-04-13 02:50 JST clean49 second allocation path entered

- Valid log: `teraterm_2026-04-13_025010.log` against `analysis/media_snapshots/windows_media_F_20260413_023332.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE5FC_or_100DE728.clean49`.
- It hit `ELR=bootmgfw+0xDE5FC`, not `0x100DE728`.
- `X0=0x40002AD0`, `X8=0`, `X24=0` at the stop.
- Interpretation: the global gate again sees `[0x102EFDD8] == 1`, so execution enters the second/smaller block scan-allocation path.
- Generated and staged the next list-entry probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE61C_or_100DE644.clean50`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_025109.md`
  - SHA256: `837BF4F57A1C560DD9328ABF497B482DF28888EB587E587EDF440AD593604DA4`
- Clean50 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE61C` or `0x100DE644`.
- Purpose:
  - `0x100DE61C` hit: second list/table pointer is non-null and index 0 entry was loaded; read `X0` as the entry pointer/value
  - `0x100DE644` hit: second list/table pointer is null, so the no-list path is taken

## 2026-04-13 02:54 JST clean50 second list index 0 entry

- Valid log: `teraterm_2026-04-13_025412.log` against `analysis/media_snapshots/windows_media_F_20260413_025109.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE61C_or_100DE644.clean50`.
- It hit `ELR=bootmgfw+0xDE61C`, not `0x100DE644`.
- `X0=0x40002AB0`, `X8=0`, `X24=0x23CE62000`.
- Interpretation: the second list/table pointer is non-null, and index 0 contains a non-null entry pointer/value `0x40002AB0`.
- Generated and staged the next validation/result branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE658_or_100DE6AC.clean51`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_025516.md`
  - SHA256: `7A6A08B8CA1F28AE1D8938D2F3F39A3007A55FF8317B0F45293220688885DFB5`
- Clean51 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE658` or `0x100DE6AC`.
- Purpose:
  - `0x100DE658` hit: the second list entry validated as usable; read `X0` as the accepted entry/block pointer before helper `0x101DEA18`
  - `0x100DE6AC` hit: the scan did not produce a usable entry and falls to the fallback/allocation path

## 2026-04-13 07:36 JST clean51 second entry accepted

- Valid log: `teraterm_2026-04-13_073611.log` against `analysis/media_snapshots/windows_media_F_20260413_025516.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE658_or_100DE6AC.clean51`.
- It hit `ELR=bootmgfw+0xDE658`, not `0x100DE6AC`.
- `X0=0x40002AB0`, `X8=1`, `X24=0x23CE62000`.
- Interpretation: the second list entry `0x40002AB0` passed the scan's local validation and is accepted for helper `0x101DEA18`.
- Generated and staged the next helper/result branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE65C_or_100DE70C.clean52`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_073757.md`
  - SHA256: `1C49A665681A129512D04335F97945A17CEEA6E549A64AAC27FDBF884D1617ED`
- Clean52 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE65C` or `0x100DE70C`.
- Purpose:
  - `0x100DE65C` hit: helper `0x101DEA18` returned; read `X0` as its returned pointer/value
  - `0x100DE70C` hit: helper returned non-null and subsequent list-integrity/size validation reached the later accepted/fallback-merge point; read `X0`

## 2026-04-13 07:40 JST clean52 second helper return

- Valid log: `teraterm_2026-04-13_074008.log` against `analysis/media_snapshots/windows_media_F_20260413_073757.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE65C_or_100DE70C.clean52`.
- It hit `ELR=bootmgfw+0xDE65C`, not `0x100DE70C`.
- `X0=0x40002AB0`, so helper `0x101DEA18` returned non-null and effectively preserved/returned the accepted entry pointer.
- `X8=0x4007FFC8`, `X24=0x23CE62000` at the stop.
- Generated and staged the next validation-branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE694_or_100DE70C_or_100DE784.clean53`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_074125.md`
  - SHA256: `32429F4D08C96AB08F60CEF65D8F36C86852DEA5071D35B37471F3C5A91875EE`
- Clean53 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE694`, `0x100DE70C`, or `0x100DE784`.
- Purpose:
  - `0x100DE694` hit: list integrity check failed and cleanup helper `0x101DE820` would run
  - `0x100DE70C` hit: accepted pointer reaches the non-split/merge path
  - `0x100DE784` hit: accepted pointer reaches the split-block path

## 2026-04-13 21:19 JST clean53 accepted pointer merge path

- Valid log: `teraterm_2026-04-13_211915.log` against `analysis/media_snapshots/windows_media_F_20260413_074125.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE694_or_100DE70C_or_100DE784.clean53`.
- It hit `ELR=bootmgfw+0xDE70C`, not `0x100DE694` or `0x100DE784`.
- `X0=0x40002AB0`, `X8=0x40002AD0`, `X24=0x23CE62000`.
- Interpretation: accepted pointer `0x40002AB0` reaches the non-split/merge path. It did not take the list-integrity cleanup path and did not take the split-block path.
- Generated and staged the next branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE75C_or_100DE7C0.clean54`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_212212.md`
  - SHA256: `4D172B7A453DAA270350233EC9207D9C13B15F5D797CF2013AE6138371C89C92`
- Clean54 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE75C` or `0x100DE7C0`.
- Purpose:
  - `0x100DE7C0` hit: `x24` is non-null after merge/finalization and the object initialization path continues
  - `0x100DE75C` hit: `x24` is null and execution falls to the failure path

## 2026-04-13 21:25 JST clean54 object initialization continues

- Valid log: `teraterm_2026-04-13_212532.log` against `analysis/media_snapshots/windows_media_F_20260413_212212.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE75C_or_100DE7C0.clean54`.
- It hit `ELR=bootmgfw+0xDE7C0`, not `0x100DE75C`.
- `X0=0x40002AB0`, `X24=0x40002AC0`, `X8=0`.
- Interpretation: `x24` is non-null and object initialization continues; the immediate failure path was not taken.
- Generated and staged the next global-gate probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE830_or_100DE990.clean55`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_212827.md`
  - SHA256: `09B4F15940007C5EAF9423E4E8BC99252E1E57DCA1781A04DF363D6EDE4D018D`
- Clean55 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE830` or `0x100DE990`.
- Purpose:
  - `0x100DE830` hit: global `[0x102EFDD8] == 1` and execution enters the third scan/allocation path
  - `0x100DE990` hit: third scan/allocation path is skipped

## 2026-04-13 21:31 JST clean55 third allocation path entered

- Valid log: `teraterm_2026-04-13_213116.log` against `analysis/media_snapshots/windows_media_F_20260413_212827.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE830_or_100DE990.clean55`.
- It hit `ELR=bootmgfw+0xDE830`, not `0x100DE990`.
- `X0=0x40002AB0`, `X24=0x40002AC0`, `X8=0`.
- Interpretation: global `[0x102EFDD8] == 1`, so execution enters the third scan/allocation path.
- Generated and staged the next third-list probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE84C_or_100DE874.clean56`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_213206.md`
  - SHA256: `BDEA78028EF34BA9BCFC7886A8567B666189C9804CD99A0FBE281FC5B4E96FF3`
- Clean56 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE84C` or `0x100DE874`.
- Purpose:
  - `0x100DE84C` hit: third list/table pointer is non-null and index 1 entry was loaded; read `X0`
  - `0x100DE874` hit: third list/table pointer is null; no-list path

## 2026-04-13 22:11 JST clean56 third list index 1 empty

- Valid log: `teraterm_2026-04-13_221119.log` against `analysis/media_snapshots/windows_media_F_20260413_213206.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE84C_or_100DE874.clean56`.
- It hit `ELR=bootmgfw+0xDE84C`, not `0x100DE874`.
- `X0=0`, `X8=1`, `X24=0x40002AC0`, `X19=0x23CE62000`.
- Interpretation: the third list/table pointer is non-null, but the index 1 entry loaded into `X0` is null. Original execution would branch through the increment/loop path and continue scanning later indexes.
- Generated and staged the next third-list continuation probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE850_or_100DE884.clean57`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_221328.md`
  - SHA256: `597298217E8F4A328ED88532A1DFF02DE5634A6CF7682F750BC1885BAFE8EC4F`
- Clean57 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE850` or `0x100DE884`.
- Purpose:
  - `0x100DE850` hit: a later third-list index produced a non-null candidate entry; read `X0` as that entry and `X8` as the index.
  - `0x100DE884` hit: indexes 1..6 did not produce a usable non-null candidate, and the scan is about to take the empty/fallback branch.

## 2026-04-13 22:15 JST clean57 third list exhausted

- Valid log: `teraterm_2026-04-13_221526.log` against `analysis/media_snapshots/windows_media_F_20260413_221328.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE850_or_100DE884.clean57`.
- It hit `ELR=bootmgfw+0xDE884`, not `0x100DE850`.
- `X0=0`, `X8=7`, `X24=0x40002AC0`, `X19=0x23CE62000`.
- Interpretation: the third list scan exhausted indexes 1..6 without a usable candidate and is about to take the empty/fallback path.
- Generated and staged the next fallback allocation/list probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE90C_or_100DE940.clean58`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_221804.md`
  - SHA256: `D63AEFA2B7980607B8EE35929705E05BFC753ABE984A3FD06834AC07F10E981D`
- Clean58 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE90C` or `0x100DE940`.
- Purpose:
  - `0x100DE90C` hit: an existing list block can provide the 0x40-byte allocation; read `X0` and `X10` if available.
  - `0x100DE940` hit: existing-list allocation is unavailable or failed bounds checks, so execution is about to call helper `0x101DEAC8` to allocate 0x40 bytes.

## 2026-04-13 22:20 JST clean58 existing-list allocation path

- Valid log: `teraterm_2026-04-13_222041.log` against `analysis/media_snapshots/windows_media_F_20260413_221804.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE90C_or_100DE940.clean58`.
- It hit `ELR=bootmgfw+0xDE90C`, not `0x100DE940`.
- `X0=0x40002B60`, `X8=0x4007EFB8`, `X24=0x40002AC0`, `X19=0x23CE62000`.
- Interpretation: the fallback path can carve a 0x40-byte block from the existing list; it did not call helper `0x101DEAC8` for a fresh 0x40-byte allocation.
- Generated the next object-init helper return probe, but did not stage it because `F:` was not present at generation time:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE9E0_or_100DE75C.clean59`
  - SHA256: `FF9A55F6B2B0CFABB321DC18348BEEB50D5899A47F06E9DE311D49241BF84472`
- Clean59 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE9E0` or `0x100DE75C`.
- Purpose:
  - `0x100DE9E0` hit: helper `0x100DE0A8` returned after object initialization; read `W0`/`X0`, `X21`, and `X25`.
  - `0x100DE75C` hit: `x21` was null and the failure path was taken before the object-init helper.

- Update: clean59 was staged after F: was reinserted. Snapshot: `analysis/media_snapshots/windows_media_F_20260413_222327.md`.

## 2026-04-13 22:24 JST clean59 object-init helper returned success-looking status

- Valid log: `teraterm_2026-04-13_222454.log` against `analysis/media_snapshots/windows_media_F_20260413_222327.md` / active marker `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE9E0_or_100DE75C.clean59`.
- It hit `ELR=bootmgfw+0xDE9E0`, not `0x100DE75C`.
- `X0=0`, `X8=0`, `X24=0x40002AC0`, `X19=0x23CE62000`.
- `FP18 +30=0x40002B60`, matching the carved block from the prior allocation path.
- Interpretation: helper `0x100DE0A8` returned a success-looking status (`W0=0`). Because the stop replaced `ldr x25, [sp,#0x28]`, `X25=0` in this log is still the pre-load register value and should not be interpreted as the helper output pointer.
- Generated and staged the next success-vs-cleanup branch probe:
  - marker: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE9EC_or_100DE760.clean60`
  - snapshot: `analysis/media_snapshots/windows_media_F_20260413_222702.md`
  - SHA256: `ACF2D5FD09285940633AB5B3CAAB32A6850EE07AA1AD0476CAED863258D453A9`
- Clean60 keeps `0x100DE230 -> mov w23,#1`, the two local-field bypasses, and `x27=2`, then stops at `0x100DE9EC` or `0x100DE760`.
- Purpose:
  - `0x100DE9EC` hit: helper status was non-error and execution entered the object registration path; read `X25` and `X21`.
  - `0x100DE760` hit: helper status was an error and execution entered cleanup.
