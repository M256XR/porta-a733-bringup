# BOOTAA64 stop ladder (2026-04-08)

Purpose:
- Keep loader-side diagnostics minimal.
- Use a single `UDF` stop-point on top of `BOOTAA64.original.EFI`.
- Move deeper only after a log proves the current stop-point is reached.

Current staged media:
- `F:/EFI/BOOT/BOOTAA64.EFI` = `BOOTAA64.nop_10054A60_stop_10054A68.EFI`
- `F:/EFI/Microsoft/Boot/bootmgfw.efi` = original
- `F:/startup.nsh` = no-op stub

Latest result before this stage:
- `BOOTAA64.stop_10054A50_udf.EFI` raised the expected synchronous exception.
- `ELR=...10054A50` proved control returned from firmware's `SetVariable` implementation back into BOOTAA64's caller-side wrapper.
- `BOOTAA64.stop_101B6A78_udf.EFI` did not raise an exception even though the marker confirmed it was staged.
- `BOOTAA64.stop_10054A68_udf.EFI` also did not raise an exception even though the marker confirmed it was staged.
- Therefore the remaining blocker is between `0x10054A50` and `0x10054A68`, with the call at `0x10054A60` as the cleanest next probe.
- A direct `0x1028D950` function-entry probe stopped the run too early and is treated as ambiguous.
- `BOOTAA64.stop_10054A60_udf.EFI` then raised the expected exception at the exact call-site.
- Therefore the current leading hypothesis is that the call at `0x10054A60` does not return cleanly.

Prepared variants:

1. Runtime-service wrapper return
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_10054A50_udf.EFI`
- patch: `0x10054A50` `7f060071 -> 00000000`
- sha256: `0D2C2B56CBDC6F53DE6BB4B876F1F11F8A1844EB056183CF7D465B3773CF6138`
- meaning: prove control returns from `gRT->SetVariable` back into BOOTAA64's caller-side wrapper

2. Post-SetVariable helper
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_101B6A78_udf.EFI`
- patch: `0x101B6A78` `b2390094 -> 00000000`
- sha256: `B1A6E16085D5AD7923A6D933768E34EC969123BFD78662C569E17F840E52A3F0`
- meaning: prove execution gets past the wrapper and reaches the first helper call immediately after `WindowsBootChainSvnCheckStatus`

3. Later wrapper boundary
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_10054A68_udf.EFI`
- patch: `0x10054A68` `20fbff97 -> 00000000`
- sha256: `50CA7315238BB864532530279ABA3785AC6698690409E045933CEBA419C94CD8`
- meaning: prove the wrapper gets past `0x1028D950` and reaches the `0x100536E8` call boundary

4. Wrapper epilogue entry
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_10054A6C_udf.EFI`
- patch: `0x10054A6C` `fd7bc3a8 -> 00000000`
- sha256: `9E7EDFE5FA17487A1237D0C69BEDB787F9FB731B2D414CA3C116D6AA5F93DAF6`
- meaning: prove `0x100536E8` returns and the wrapper reaches its epilogue

5. Follow-up call-site
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_10054A60_udf.EFI`
- patch: `0x10054A60` `bce30894 -> 00000000`
- sha256: `33D4695B19CAF74D54399CF2475A013312752D685630764FB7060B67814D5BB3`
- meaning: prove execution reaches the exact branch into the suspected follow-up function

6. Skip-and-stop test
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_stop_10054A68.EFI`
- patches:
  - `0x10054A60` `bce30894 -> 1f2003d5`
  - `0x10054A68` `20fbff97 -> 00000000`
- sha256: `F6111BC0E1E1F29E7EB03235636F83D4436ACC1923644EB9B20D672FBE3F4613`
- meaning: skip the suspected blocking call and see whether execution reaches the next wrapper boundary

7. Follow-up function entry
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1028D950_udf.EFI`
- patch: `0x1028D950` `f353bda9 -> 00000000`
- sha256: `4157626A33F091B8E4E151733FC9036AF2543AB0026015B65C73F5F34F8B269C`
- meaning: prove execution enters the intervening follow-up function called from the wrapper
- caveat: ambiguous because this function may have other callers

8. Deep helper function entry
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003AD38_udf.EFI`
- patch: `0x1003AD38` `f353bba9 -> 00000000`
- sha256: `4F32780B08EEEC9635B5B23534C51CB3382CAE98FD4ED6436E8EDD08DB99F6DA`
- meaning: prove the clean current path reaches the large post-policy helper function at all

9. Deep helper mid-path proof
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003B49C_udf.EFI`
- patch: `0x1003B49C` `1f000071 -> 00000000`
- sha256: `C475B0970CAD7E63330EC2ABD964FE9E9FDD114164E8745626DE8FF305F66898`
- meaning: prove execution reaches the mid-function success path inside that helper

10. Pre-helper call
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BA58_udf.EFI`
- patch: `0x1003BA58` `e0250094 -> 00000000`
- sha256: `FA5F29EC42E0F80B84D9E80287FA0ECD4B12EB763CBF8FE3659DB500468AA1FC`
- meaning: stop just before the helper call that older patch archaeology associated with BCD progress

11. Post-cleanup flag gate
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BAEC_udf.EFI`
- patch: `0x1003BAEC` `1301f836 -> 00000000`
- sha256: `947BA4F204D9B6E14F65F78A58573E6A42569CEED3FF2EFF27FF5A8FA7328755`
- meaning: stop after the cleanup section and just before the final status/flag gate

12. Late status fetch
- file: `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BB08_udf.EFI`
- patch: `0x1003BB08` `fbcb4039 -> 00000000`
- sha256: `B54C9A949AE358F1321956EFF462F4867D47D38CF49E307B8E9DA24DCA1B6FCA`
- meaning: stop immediately after the conditional query path and before the final late branch logic

Interpretation guide:
- Exception at `ELR=...10054A50`: BOOTAA64 returns from firmware's SetVariable implementation.
- Silence before hitting `0x10054A50`: the remaining blocker is inside or immediately around the runtime-service return path.
- Exception at `ELR=...101B6A78`: execution gets past the wrapper and into the immediate post-SetVariable helper chain.
- Silence before `0x101B6A78` but after `0x10054A50`: blocker sits between wrapper return and the higher-level helper.
- Exception at `ELR=...10054A60`: execution reaches the exact branch into the suspected follow-up function.
- Silence before `0x10054A60` but after `0x10054A50`: blocker sits between wrapper return and that branch site.
- Exception at `ELR=...10054A68` with `0x10054A60` NOPed: skipping the suspected call lets execution reach the next wrapper boundary.
- `teraterm_2026-04-08_222707.log` confirmed this exact case.
- That result strongly implicates the original call at `0x10054A60`.
- Silence even with `0x10054A60` NOPed: the blocker is not solely the call body and the model needs revision.
- Exception at `ELR=...10054A68`: wrapper gets past `0x1028D950` and reaches the `0x100536E8` call boundary.
- The current staged follow-up run is `0x10054A60 -> NOP` plus `0x10054A6C -> UDF`.
- If that next run hits `ELR=...10054A6C`, the wrapper also returns past the next post-call step.
- `teraterm_2026-04-08_223117.log` confirmed this exact case.
- That means `0x100536E8` returns cleanly too, and the wrapper epilogue begins.
- The current staged follow-up run is now `0x10054A60 -> NOP` plus `0x101B6A78 -> UDF`.
- If that next run hits `ELR=...101B6A78`, skipping the suspected call lets execution return to the higher-level caller and reach its next call boundary.
- `teraterm_2026-04-08_224003.log` confirmed this exact case.
- That means the bypassed path returns not just through the wrapper but also back to the higher-level caller.
- The current staged run is now `0x10054A60 -> NOP` only, with no stop-point.
- Use that run to learn the next natural failure mode after bypassing the dominant blocker.
- `teraterm_2026-04-08_224422.log` revealed that next natural failure mode:
  - a null callback dispatch at `0x101CC428` (`blr x15`) that collapses into `ELR=0`.
- This matches the older `skip_null_callback_101cc428` archaeology already present in the repo.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
- Use that run to see how far the previously-known null-callback bypass gets on the now-cleaner current path.
- `teraterm_2026-04-08_230053.log` showed the answer:
  - with both bypasses in place, the path reaches the real Windows Boot Manager `\EFI\Microsoft\Boot\BCD / 0xc000000d` screen again.
- That re-establishes the older BCD milestone on the current cleaner firmware path.
- From this point, the next debugging axis is BCD/media semantics, not the earlier silent-stop boot path.
- `teraterm_2026-04-08_232906.log` then showed that swapping to the older `BCD.pre_restore_test.bak` logical variant still produced the same `\EFI\Microsoft\Boot\BCD / 0xc000000d` screen.
- That demotes the BCD logical-content hypothesis and moves the next diagnostic step back to a later bootmgr branch.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
- This reintroduces only the older ConfigAccessPolicy-related bypass on top of the two already-proven early-path bypasses.
- Use that run to see whether the current clean path still depends on the `0x101AFA2C` branch to escape the `0xc000000d` screen.
- `teraterm_2026-04-08_233844.log` showed that it does not: the run still landed on the same `\EFI\Microsoft\Boot\BCD / 0xc000000d` screen.
- That means the current divergence is deeper than `0x101AFA2C`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> UDF`
- This is the first post-query checkpoint on the older `BCD`-focused ladder.
- If the next run hits `ELR=...1003AFEC`, the current clean path has rejoined that older ladder.
- If it still falls straight to `0xc000000d`, the path diverges before `0x1003AFEC` and the next breakpoint should move back to `0x1003AF38`.
- `teraterm_2026-04-08_234500.log` confirmed that the current clean path does hit `ELR=...1003AFEC`.
- The trapped `X0` value there was `0xC000000D`.
- That means the immediate status returned by `0x101B3D48` is itself `0xc000000d`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003AFF4 -> UDF`
- This bypasses the immediate error branch once and stops at the following bit-flag gate.
- If the next run hits `ELR=...1003AFF4`, then the next discriminator is the bit 0 flag stored at `[sp+0x60]`.
- If it does not, the model around `0x1003AFEC` needs revision.
- `teraterm_2026-04-08_235719.log` confirmed the `ELR=...1003AFF4` case.
- The trapped register state there showed:
  - `X0 = 0xC000000D`
  - `X8 = 0`
- So even after bypassing the immediate `0xc000000d` branch, the following flag gate still naturally chooses the branch target at `0x1003B02C`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B02C -> UDF`
- This follows the natural branch target after the cleared-bit gate and stops at the start of that alternate path.
- Prepared follow-on stop variants also exist for:
  - `0x1003B040`
  - `0x1003B098`
  - `0x1003B0B8`
- These will let the next turn keep walking the same alternate path without rebuilding the ladder from scratch.
- `teraterm_2026-04-09_002818.log` confirmed the `ELR=...1003B02C` case.
- So the live path now definitely enters the alternate post-query branch after the cleared-bit gate.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B040 -> UDF`
- This stops at the first status branch after the `0x2600002A` property query on that alternate path.
- If the next run hits `ELR=...1003B040`, the next discriminator is the status returned by `0x101B0A20`.
- `teraterm_2026-04-09_003351.log` confirmed the `ELR=...1003B040` case.
- The trapped register state showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
- So the `0x2600002A` query itself is currently failing on the live path.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B040 -> NOP`
  - `0x1003B048 -> UDF`
- This ignores that immediate negative status once and stops at the next byte-flag branch.
- If the next run hits `ELR=...1003B048`, then `w8` will reflect the actual byte loaded from `[sp+0x31]`.
- `teraterm_2026-04-09_004123.log` confirmed the `ELR=...1003B048` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So even after bypassing the immediate negative status once, the following byte flag is also clear.
- That means the natural live path is not the forced-success body at `0x1003B04C`; it still flows to `0x1003B06C`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B06C -> UDF`
- This stops at the natural alternate-path branch target after both the negative `0x2600002A` status and the clear `[sp+0x31]` byte.
- If the next run hits `ELR=...1003B06C`, the next discriminator becomes the `w20` gate immediately after the failed query path.
- `teraterm_2026-04-09_005046.log` confirmed the `ELR=...1003B06C` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x2600002A`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So the natural live path also skips the `w20!=0` side-path and falls straight through to the next query/status block at `0x1003B088-0x1003B098`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B098 -> UDF`
- This stops at the status branch immediately after the next alternate-path query (`bl #0x101B1530`).
- If the next run hits `ELR=...1003B098`, the next discriminator becomes the return status of that second query/helper pair.
- `teraterm_2026-04-09_005434.log` confirmed the `ELR=...1003B098` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X24 = 0x23CF984C4`
- So the second alternate-path query/helper pair returns success on the live path.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B0B8 -> UDF`
- This stops at the branch immediately after `bl #0x1003E290`.
- If the next run hits `ELR=...1003B0B8`, then the next discriminator is the return status of `0x1003E290`.
- `teraterm_2026-04-09_005744.log` confirmed the `ELR=...1003B0B8` case.
- The trapped register state there showed:
  - `X0 = 0xC000000D`
  - `X19 = 0`
  - `X20 = 0`
- So `0x1003E290` returns another direct negative status on the live path.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B0C0 -> UDF`
- This stops immediately after the following `ldrb w8, [sp, #0x30]`.
- If the next run hits `ELR=...1003B0C0`, then `X8` will show whether this negative `0x1003E290` status is paired with a clear byte that jumps directly to `0x1003B12C`.
- `teraterm_2026-04-09_010124.log` confirmed the `ELR=...1003B0C0` case.
- The trapped register state there showed:
  - `X0 = 0xC000000D`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So the negative `0x1003E290` status is paired with a clear `[sp+0x30]` byte.
- The natural live path therefore skips the deeper side-path and falls directly to `0x1003B12C`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B12C -> UDF`
- This stops at the shared join point after the local branch family has fully collapsed.
- If the next run hits `ELR=...1003B12C`, then the next work is to understand the state that reaches that shared continuation.
- `teraterm_2026-04-09_010449.log` confirmed the `ELR=...1003B12C` case.
- The trapped register state there showed:
  - `X0 = 0xC000000D`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So the negative `0x1003E290` return is indeed what reaches the shared continuation, and the local branch family is no longer the interesting part.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B154 -> UDF`
- This stops at the status check immediately after the first shared-continuation query/helper pair (`bl #0x101B11E8`).
- If the next run hits `ELR=...1003B154`, then the next discriminator is the return status of that `0x11000084` query and whether it populates `[sp+0x68]`.
- `teraterm_2026-04-09_010952.log` confirmed the `ELR=...1003B154` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x11000084`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X22 = 0x400010A0`
- So the first shared-continuation query/helper pair also fails on the live path and does not populate `[sp+0x68]`.
- The natural path therefore skips the `0x101B0808` cleanup helper and falls through to `0x1004C1F0`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B178 -> UDF`
- This stops immediately after `bl #0x1004C1F0`.
- If the next run hits `ELR=...1003B178`, then the next discriminator is the return status of that shared-continuation helper.
- `teraterm_2026-04-09_011331.log` confirmed the `ELR=...1003B178` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So `0x1004C1F0` returns success on the live path.
- The natural path now takes the branch to `0x1003B1D0`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B1F0 -> UDF`
- This stops at the branch immediately after `bl #0x10264838`.
- If the next run hits `ELR=...1003B1F0`, then the next discriminator is the return status of `0x10264838`.
- `teraterm_2026-04-09_011832.log` confirmed the `ELR=...1003B1F0` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X8 = 2`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So `0x10264838` also returns success on the live path.
- The natural path now continues into `bl #0x102615B8`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B1FC -> UDF`
- This stops at the status branch immediately after `bl #0x102615B8`.
- If the next run hits `ELR=...1003B1FC`, then the next discriminator is the return status of `0x102615B8`.
- `teraterm_2026-04-09_012351.log` confirmed the `ELR=...1003B1FC` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So `0x102615B8` also returns success on the live path.
- The next discriminator is now the byte loaded from `[sp+0x31]` at `0x1003B200`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B204 -> UDF`
- This stops at the `cbz w8, #0x1003B268` branch immediately after `ldrb w8, [sp, #0x31]`.
- If the next run hits `ELR=...1003B204`, then `X8` shows whether the byte flag is zero or whether the path enters the deeper side-path at `0x1003B208`.
- `teraterm_2026-04-09_012849.log` confirmed the `ELR=...1003B204` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So the byte loaded from `[sp+0x31]` is also clear on the live path.
- The natural path now takes the `cbz w8, #0x1003B268` branch into the shared continuation.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B268 -> UDF`
- This stops at the start of the shared continuation block after the stage-3 selector settles.
- If the next run hits `ELR=...1003B268`, then the current path has fully chosen the shared post-selector continuation rather than the deeper side-path at `0x1003B208`.
- `teraterm_2026-04-09_013257.log` confirmed the `ELR=...1003B268` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So the path has entered the shared continuation carrying the earlier negative `w20` status.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B298 -> UDF`
- This stops at the branch immediately after the `0x101AED08` / `0x101AEDB8` helper pair.
- If the next run hits `ELR=...1003B298`, then `X0` shows whether that helper pair succeeds or becomes the next live-path failure source.
- `teraterm_2026-04-09_013701.log` confirmed the `ELR=...1003B298` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
- So the `0x101AED08` / `0x101AEDB8` helper pair also returns success on the live path.
- Because the success branch is taken, the `cmp/csel` block at `0x1003B29C..0x1003B2A0` is skipped and the carried negative `w20` remains intact.
- The natural path therefore takes `tbnz w20, #0x1f, #0x1003B344`.
- The next BOOTAA64 variant has already been generated locally:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.nop_10054A60_skip_null_callback_101CC428_bypass_configaccesspolicy_101AFA2C_nop_1003AFEC_stop_1003B344_udf.EFI`
- It was not staged yet because the removable media was no longer mounted on the host at analysis time.
- Once staged, `ELR=...1003B344` will confirm entry into the negative-status cleanup/reporting leg of the shared continuation.
- `teraterm_2026-04-09_014233.log` confirmed the `ELR=...1003B344` case.
- The trapped register state there showed:
  - `X0 = 0x000000023CC9AF20`
  - `X1 = 0x000000023CC9AF20`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So the shared continuation is definitely taking the negative-status cleanup/reporting leg.
- Because the stop-point is on `mov x0, x21`, those incoming `X0`/`X1` values are not yet meaningful for the cleanup subpath itself.
- The next real discriminator is the `cbnz x0, #0x1003B3A0` branch after the `0x1003F878`, `0x1003F4A0`, `0x101C47B8` call sequence.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B358 -> UDF`
- This stops exactly at the `cbnz x0, #0x1003B3A0` branch.
- If the next run hits `ELR=...1003B358`, then `X0` decides whether the path falls into the hardcoded `0xC0000225` reporting block or takes the deeper reporting subpath.
- Silence before `0x10054A68` but after `0x10054A50`: blocker is inside the wrapper, most likely `0x1028D950` or adjacent cleanup.
- Exception at `ELR=...10054A6C`: `0x100536E8` returns and the wrapper reaches its epilogue.
- Exception at `ELR=...1028D950`: execution enters the intervening follow-up function.
- Silence before `0x1028D950` but after `0x10054A50`: blocker sits immediately around the wrapper-to-follow-up transition.
- Exception at `ELR=...1003AD38`: the clean current path reaches the large deep helper function.
- Exception at `ELR=...1003B49C`: the clean current path reaches the deeper success path within that helper.
- Exception at `ELR=...1003BA58`: the path reaches the helper-call boundary.
- Exception at `ELR=...1003BAEC`: the path survives the cleanup/helper section.
- Exception at `ELR=...1003BB08`: the path gets through the late query setup and dies only after that.
- Silence before hitting the current stop-point means the remaining blocker is earlier.

Important constraint:
- Do not restage both `BOOTAA64.EFI` and `bootmgfw.efi` with the same patched variant.
- Keep `bootmgfw.efi` original and keep `startup.nsh` quiet to avoid retry contamination.
- `teraterm_2026-04-09_014557.log` confirmed the `ELR=...1003B358` case.
- The trapped register state there showed:
  - `X0 = 0x000000023CFAE30A`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So the branch `cbnz x0, #0x1003B3A0` is taken on the live path.
- The path does not fall through to the fixed `0xC0000225` reporting block at `0x1003B35C`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B3A0 -> UDF`
- This stops at the entry to the deeper reporting subpath selected by the nonzero return from `0x101C47B8`.
- If the next run hits `ELR=...1003B3A0`, then the next discriminator is the return status of `0x101E8470`.
- `teraterm_2026-04-09_015218.log` confirmed the `ELR=...1003B3A0` case.
- The trapped register state there showed:
  - `X0 = 0x000000023CFAE30A`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So the deeper reporting subpath selected by `cbnz x0, #0x1003B3A0` is definitely live.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B3AC -> UDF`
- This stops immediately after the `0x101E8470` call and `mov w19, w0`.
- If the next run hits `ELR=...1003B3AC`, then `X0` and `X19` show whether that helper returns success or another negative status.
- `teraterm_2026-04-09_020835.log` confirmed the `ELR=...1003B3AC` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So `0x101E8470` returns success on the live path and the branch goes to `0x1003B3E4`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B3E4 -> UDF`
- This stops at the start of the local success-side continuation after the deeper reporting subpath resolves.
- If the next run hits `ELR=...1003B3E4`, then the next live discriminator is the later `0x16000048` query block near `0x1003B480..0x1003B49C`.
- `teraterm_2026-04-09_021251.log` confirmed the `ELR=...1003B3E4` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X19 = 0`
  - `X20 = 0xC000000D`
  - `X21 = 0`
- So the deeper reporting subpath resolves into its local success-side block, but that block only reports the carried `w20` failure and rejoins the shared reporting tail.
- The ladder therefore pivots here from natural-path tracing to a forward-probe.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B134 -> mov w20, wzr`
  - `0x1003B2D4 -> UDF`
- This deliberately clears the carried `0xC000000D` before the `tbnz w20, #0x1f, #0x1003B344` gate.
- If the next run hits `ELR=...1003B2D4`, then the next live blocker is the `0x26000042` query on the forced positive path.
- `teraterm_2026-04-09_022001.log` confirmed the forward-probe `ELR=...1003B2D4` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x26000042`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So the forced positive path reaches the `0x26000042` property query, and that query itself fails with `0xC0000225`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B134 -> mov w20, wzr`
  - `0x1003B2D4 -> NOP`
  - `0x1003B2DC -> UDF`
- This ignores the `0x26000042` status failure once and stops at the byte-flag gate immediately after it.
- If the next run hits `ELR=...1003B2DC`, then `X8` decides whether the path still falls back into `0x1003B344` or advances to `0x101AEA58` / `0x1600007E`.
- `teraterm_2026-04-09_022351.log` confirmed the forward-probe `ELR=...1003B2DC` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x26000042`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So after ignoring the `0x26000042` status failure once, the returned byte flag is still clear.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B134 -> mov w20, wzr`
  - `0x1003B2D4 -> NOP`
  - `0x1003B2DC -> NOP`
  - `0x1003B2E4 -> UDF`
- This ignores both the query-status gate and the zero-byte gate, and stops after `0x101AEA58`.
- If the next run hits `ELR=...1003B2E4`, then `X0` decides whether the path still falls back into `0x1003B344` or advances to the later `0x1600007E` query.
- `teraterm_2026-04-09_022707.log` confirmed the forward-probe `ELR=...1003B2E4` case.
- The trapped register state there showed:
  - `X0 = 0x1`
  - `X1 = 0x26000042`
  - `X19 = 0`
  - `X20 = 0`
- So `0x101AEA58` returns bit0 set and this gate no longer falls back into `0x1003B344`.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B134 -> mov w20, wzr`
  - `0x1003B2D4 -> NOP`
  - `0x1003B2DC -> NOP`
  - `0x1003B2FC -> UDF`
- This pushes the probe to the later `0x1600007E` query.
- If the next run hits `ELR=...1003B2FC`, then `X0` shows whether that later property query also fails.
- `teraterm_2026-04-09_023017.log` confirmed the forward-probe `ELR=...1003B2FC` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x1600007E`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So the later `0x1600007E` property query also fails with `0xC0000225` on the forced positive path.
- The current staged run is now:
  - `0x10054A60 -> NOP`
  - `0x101CC428 -> mov w0, wzr`
  - `0x101AFA2C -> mov w21, wzr`
  - `0x1003AFEC -> NOP`
  - `0x1003B134 -> mov w20, wzr`
  - `0x1003B2D4 -> NOP`
  - `0x1003B2DC -> NOP`
  - `0x1003B2FC -> NOP`
  - `0x1003B304 -> UDF`
- This ignores the `0x1600007E` status failure once and stops at the byte-flag gate immediately after it.
- If the next run hits `ELR=...1003B304`, then `X8` decides whether the path still falls back into `0x1003B344` or advances to `0x10043B48`.
- `teraterm_2026-04-09_023407.log` confirmed the forward-probe `ELR=...1003B304` case.
- The trapped register state there showed:
  - `X0 = 0xC0000225`
  - `X1 = 0x1600007E`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
- So after ignoring the `0x1600007E` status failure once, the returned byte flag is still clear.
- `teraterm_2026-04-09_023743.log` confirmed the forward-probe `ELR=...1003B31C` case.
- The trapped register state there showed:
  - `X0 = 0xC000000D`
  - `X19 = 0xC000000D`
  - `X20 = 0`
  - `X21 = 0`
- So after bypassing the `0x26000042` and `0x1600007E` gates, the helper `0x10043B48` still returns `0xC000000D`.
- The current staged run is now:
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
- This clears the later `0x10043B48` status once and stops at the shared report/cleanup tail.

- `teraterm_2026-04-09_024231.log` confirmed the shared-tail `ELR=...1003BA08` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X1 = 0x50`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
- So after clearing the later `0x10043B48 -> 0xC000000D` result once, the forward-probe reaches the shared report/cleanup tail with no more hidden gate before it.
- Since `w19=0` at `0x1003BA08`, the tail takes the local cleanup/report leg that begins at `0x1003BA30`.
- The current staged run is now:
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
- This keeps the same forward-probe but moves the stop-point to the `cbz x22` gate inside the shared cleanup tail.
- If the next run hits `ELR=...1003BA5C`, then `X22` decides whether the tail performs the `x22`-based cleanup branch or falls through to `0x1003BA68`.


- `teraterm_2026-04-09_025052.log` confirmed the shared-tail `ELR=...1003BA5C` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X8 = 0`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- So the shared cleanup tail does execute the `x22` cleanup call and then reaches the `cbz x23` gate at `0x1003BA68`.
- The current staged run is now:
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
- This moves the stop-point to the `cbz x23` gate after the `x22` cleanup call.
- If the next run hits `ELR=...1003BA68`, then `X23` decides whether the tail skips directly to `0x1003BAA4` or enters the `x23` cleanup loop.


- `teraterm_2026-04-09_025621.log` confirmed the shared-tail `ELR=...1003BA68` case.
- The trapped register state there showed:
  - `X0 = 0`
  - `X1 = 0`
  - `X8 = 0x40000C50`
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- So the `cbz x23` gate falls through and the `x23` cleanup loop is skipped entirely.
- The current staged run is now:
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
- This moves the stop-point to the next shared-tail free gate after the skipped `x23` cleanup loop.


- `teraterm_2026-04-09_030001.log` confirmed the shared-tail `ELR=...1003BAA4` case.
- The trapped register state there showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
- So the `x23` cleanup loop is skipped entirely and the next natural gate is the optional free block at `0x1003BAA4..0x1003BAB0`.
- The current staged run is now:
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


- `teraterm_2026-04-09_030409.log` confirmed the shared-tail `ELR=...1003BAB4` case.
- The trapped register state there showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
  - `X28 = 0`
- So the optional free block at `0x1003BAA4..0x1003BAB0` is effectively skipped too.
- The current staged run is now:
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


- `teraterm_2026-04-09_030735.log` confirmed the shared-tail `ELR=...1003BAC0` case.
- The trapped register state there showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X26 = 0`
  - `X28 = 0`
- So the `cbz x21` gate is taken and the `x21` cleanup call is skipped too.


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


- `teraterm_2026-04-09_031037.log` confirmed the shared-tail `ELR=...1003BACC` case.
- The trapped register state there showed:
  - `X19 = 0`
  - `X20 = 0`
  - `X21 = 0`
  - `X22 = 0x400010A0`
  - `X23 = 0`
  - `X27 = 0`
  - `X28 = 0`
- So the shared tail has entered its final state/update block.
- The current staged run is now:
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

## 2026-04-09 03:15 JST - state/update block split probe

- `teraterm_2026-04-09_031548.log` did not fault; capture ended at `WindowsBootChainSvnCheckStatus -> Success`.
- Therefore the staged `0x1003BAEC -> UDF` was not reached in that run.
- The active branch to resolve is now inside the `0x1003BACC` state/update block.
- Next staged EFI adds a second probe at `0x1003BADC` while keeping `0x1003BAEC -> UDF` in place.
- Expected outcomes:
  - `ELR=...1003BADC`: bit0 path entered the optional cleanup block
  - `ELR=...1003BAEC`: optional block skipped or returned, post-helper gate reached
- New staged source:
  - `D:/Projects/porta-a733-bringup/build/BOOTAA64.stop_1003BADC_and_1003BAEC_udf.EFI`
- Snapshot:
  - `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260409_031838.md`

## 2026-04-09 03:20 JST - 0x1003BAEC branch resolved

- `teraterm_2026-04-09_032036.log` faulted at `ELR=...1003BAEC`.
- Branch inputs at that stop were `w19=0`, `w27=0`.
- Therefore the next natural block is `0x1003BB0C`.
- Updated split probe now uses:
  - `0x1003BADC -> UDF`
  - `0x1003BB14 -> UDF`
- Goal:
  - `ELR=...1003BADC`: optional state cleanup block became live
  - `ELR=...1003BB14`: inspect post-`0x101AE9C8` state word and final mode/status gate

## 2026-04-09 03:24 JST - 0x1003BB14 confirms local success branch

- `teraterm_2026-04-09_032449.log` faulted at `ELR=...1003BB14`.
- Branch inputs:
  - `x0` is a valid context pointer
  - `w8=0x8001`
  - `w27=0`
- Therefore neither `cbnz w27` nor `tbnz w8,#5` takes the `0x1003BBBC` error leg.
- The natural path is `0x1003BB1C..0x1003BB44`, followed by normal function return.
- This means the current bypass set is sufficient to clear the shared-tail function itself; the next meaningful run is a free run beyond this function.

## 2026-04-09 03:28 JST - free run exits cleanly back to BDS

- `teraterm_2026-04-09_032908.log` shows no exception.
- Observed sequence:
  - `gBS->Exit Status=Success ExitDataSize=0`
  - `StartImage watch end Status=Success`
  - `EfiBootManagerBoot returned EFI_SUCCESS`
- Therefore the current bypass set is enough to let bootmgfw return cleanly; the next blocker is outside the traced function and now appears as a clean early exit path back to firmware.
- Firmware-side `CoreExit()` diagnostics were expanded and rebuilt to capture image path and exit text on the next run.

## 2026-04-09 03:35 JST - free run returns success, probe moves into 0x10043B48

- `teraterm_2026-04-09_033642.log` shows no exception and a clean `CoreExit()` path for `\EFI\BOOT\BOOTAA64.EFI`.
- The entry point now returns `EFI_SUCCESS` to DxeCore under the current bypass set.
- This means `clear_w19_1003B318` is masking the real negative status source rather than fixing it.
- Next probe targets the start of `0x10043B48` directly.
- Staged stop:
  - `0x10043B70 -> UDF`
- Goal:
  - determine whether the first sub-call in `0x10043B48` is already producing the status that later became `0xC000000D`.

## 2026-04-09 03:41 JST - 0x10059360 is not the 000d source

- `teraterm_2026-04-09_034120.log` hit `ELR=...10043B70`.
- That is the post-return instruction after `bl #0x10059360` in `0x10043B48`.
- `x0=0` there, so the first sub-call succeeds.
- Next stop is `0x10043BA8` to inspect the return from `0x101B2058`.

## 2026-04-09 03:44 JST - 0x101B2058 is not the 000d source

- `teraterm_2026-04-09_034434.log` hit `ELR=...10043BA8`.
- That is the post-return instruction after `bl #0x101B2058` in `0x10043B48`.
- `x0=0` there, so the second sub-call succeeds.
- Next stop is `0x10043BD4` to inspect the return from `0x101B1C78`.

## 2026-04-09 07:30 JST - 0x101B1C78 is not the 000d source

- `teraterm_2026-04-09_073014.log` hit `ELR=...10043BD4`.
- That is the post-return instruction after `bl #0x101B1C78` in `0x10043B48`.
- `x0=0` there, so the third sub-call succeeds.
- Next stop is `0x10043BEC` to inspect the return from `0x101B8160`.


## 2026-04-09 07:43 JST - move from 0x10043B48 into 0x101B8160

- `teraterm_2026-04-09_073934.log` hit `ELR=...10043BEC`.
- That is the post-return instruction after `bl #0x101B8160` in `0x10043B48`.
- Observed register state:
  - `X0 = 0xC000000D`
  - `X19 = 0xFFFFFFFF`
  - `X20 = 0xC000000D`
  - `X22 = 0x400010A0`
- Conclusion:
  - `0x101B8160` is the first sub-call inside `0x10043B48` that returns the negative status.
- Next staged stop:
  - `0x101B8254 -> UDF`
- Meaning of the next stop:
  - inspect the return from `bl #0x101B0C90` with property id `0x17000077` near the top of `0x101B8160`.


## 2026-04-09 14:30 JST - shift 0x101B8160 probe by one instruction

- `teraterm_2026-04-09_142757.log` hit `ELR=...101B8254`.
- This confirms the return site after `bl #0x101B0C90` is live.
- But that exact stop caused a recursive exception during dump, so the `x0/w0` return status was not captured.
- The next staged stop is therefore `0x101B8258 -> UDF`.
- This preserves the same return value from `0x101B0C90` while avoiding the problematic dump point.


## 2026-04-09 15:04 JST - branch split around 0x101B8258

- `teraterm_2026-04-09_143342.log` reached `ELR=...101B8258`.
- Direct register capture at both `0x101B8254` and `0x101B8258` is unstable because the exception dump recurses.
- The next staged probe is therefore a structural split:
  - `0x101B825C -> UDF`
  - `0x101B8284 -> UDF`
- Meaning:
  - `0x101B825C` hit: `tbnz w0,#31` not taken
  - `0x101B8284` hit: `tbnz w0,#31` taken


## 2026-04-09 15:09 JST - 0x17000077 branch taken to 0x101B8284

- `teraterm_2026-04-09_150703.log` hit `ELR=...101B8284`.
- This proves the `tbnz w0,#31` at `0x101B8258` was taken.
- Therefore the first helper in `0x101B8160`, `bl #0x101B0C90` with property id `0x17000077`, already returned a negative status.
- Next staged split:
  - `0x101B828C -> UDF`
  - `0x101B82B4 -> UDF`
- Meaning:
  - `0x101B828C` hit: bit11 path taken into the `0x15000075` helper pair
  - `0x101B82B4` hit: bit11 path skipped and flow falls through to the timestamp/mismatch block


## 2026-04-09 15:13 JST - 0x101B82B4 path selected

- `teraterm_2026-04-09_151222.log` hit `ELR=...101B82B4`.
- This proves the `tbz w8,#11` branch was taken.
- So after the first negative `0x17000077` result, flow does **not** enter the `0x15000075` helper pair at `0x101B828C`.
- It falls directly into the `0x101AE7F8 / 0x101AE768` mismatch/timestamp path.
- Next staged stop:
  - `0x101B82B8 -> UDF`


## 2026-04-09 15:17 JST - split after 0x101AE7F8 / 0x101AE768 compare

- `teraterm_2026-04-09_151537.log` hit `ELR=...101B82B8`.
- This confirms the `0x101AE7F8` path is live.
- Because direct register capture still recurses there, the next split is:
  - `0x101B82C8 -> UDF`
  - `0x101B82F8 -> UDF`
- Meaning:
  - `0x101B82C8` hit: compare mismatch path taken
  - `0x101B82F8` hit: compare matched and flow skips directly to the later block


## 2026-04-09 15:20 JST - compare-equal path selected

- `teraterm_2026-04-09_151845.log` hit `ELR=...101B82F8`.
- This proves the `cmp x20, x0 ; b.eq #0x101B82F8` path was taken.
- So the mismatch-handling block `0x101B82C8..0x101B82F4` is skipped.
- Next staged split:
  - `0x101B8304 -> UDF`
  - `0x101B8BCC -> UDF`
- Meaning:
  - `0x101B8304` hit: normal later block selected
  - `0x101B8BCC` hit: long side path selected by the bit11 branch at `0x101B8300`


## 2026-04-09 15:24 JST - normal later block selected at 0x101B8304

- `teraterm_2026-04-09_152327.log` hit `ELR=...101B8304`.
- This proves the branch to `0x101B8BCC` was not taken.
- The active path is now the normal later block beginning with the `0x16000041 / 0x16000040` property pair.
- Next staged split:
  - `0x101B834C -> UDF`
  - `0x101B8380 -> UDF`
- Meaning:
  - `0x101B834C` hit: first property gate clears and flow advances to the second query
  - `0x101B8380` hit: first property gate raises the local flag/error side


## 2026-04-09 15:33 JST - second later property gate split

- `teraterm_2026-04-09_153146.log` hit `ELR=...101B834C`.
- This proves the first later property gate did not raise the local error flag.
- Active flow advanced to the second property query (`0x16000040`) and its post-query flag check.
- Next staged split:
  - `0x101B836C -> UDF`
  - `0x101B8380 -> UDF`


## 2026-04-09 15:39 JST - both later property gates cleared

- `teraterm_2026-04-09_153712.log` hit `ELR=...101B836C`.
- This proves the second later property gate (`0x16000040`) also clears.
- So neither `0x16000041` nor `0x16000040` raises the local flag/error side at `0x101B8380`.
- The active path now reaches the flag-update block at `0x101B836C..0x101B8390` and then the next live query:
  - `0x11000001` via `bl #0x10059D90`
- Next staged stop:
  - `0x101B83A4 -> UDF`


## 2026-04-09 15:43 JST - split after 0x11000001 query return

- `teraterm_2026-04-09_154154.log` hit `ELR=...101B83A4`.
- This confirms the `0x11000001` query returned and flow reached the post-call handling block.
- Because direct `w0` capture remains unstable here, the next probe is a structural split:
  - `0x101B83B8 -> UDF`
  - `0x101B8B9C -> UDF`
- Meaning:
  - `0x101B83B8` hit: the `0x11000001` result stays in the normal later block
  - `0x101B8B9C` hit: the `0x11000001` result still takes the negative-status error leg


## 2026-04-09 15:47 JST - 0x11000001 stays in the normal later block

- `teraterm_2026-04-09_154644.log` hit `ELR=...101B83B8`.
- This proves the `0x11000001` result does not branch to `0x101B8B9C`.
- The active path now reaches the flag test on `w9 & 0x2004`.
- Next staged split:
  - `0x101B83C8 -> UDF`
  - `0x101B83E8 -> UDF`
- Meaning:
  - `0x101B83C8` hit: extra `0x21000001` query block is taken
  - `0x101B83E8` hit: that block is skipped


## 2026-04-09 15:49 JST - extra 0x21000001 query block skipped

- `teraterm_2026-04-09_154954.log` hit `ELR=...101B83E8`.
- This proves the `tst w9, #0x2004 ; b.eq #0x101B83E8` branch took the skip path.
- The extra `0x21000001` query block at `0x101B83C8..0x101B83E4` is not executed.
- Active flow now reaches the next gate:
  - `tbz w8, #8, #0x101B8424`
- Next staged split:
  - `0x101B83F0 -> UDF`
  - `0x101B8424 -> UDF`
- Meaning:
  - `0x101B83F0` hit: bit8 is set and flow enters the `0x21000005` query path
  - `0x101B8424` hit: bit8 is clear and the `0x21000005` path is skipped


## 2026-04-09 15:55 JST - 0x21000005 query block skipped, x21 gate is next

- `teraterm_2026-04-09_155530.log` hit `ELR=...101B8424`.
- This proves the `tbz w8, #8, #0x101B8424` branch took the bit8-clear path.
- The `0x21000005` query block at `0x101B83F0..0x101B8420` is not executed.
- Active flow now reaches:
  - `cbz x21, #0x101B8450`
- Next prepared split:
  - `0x101B8428 -> UDF`
  - `0x101B8450 -> UDF`
- Meaning:
  - `0x101B8428` hit: `x21` is nonzero and flow enters the `0x10064470` helper path
  - `0x101B8450` hit: `x21` is zero and that helper path is skipped


## 2026-04-09 16:00 JST - x21 helper path skipped, cached-pointer gate is next

- `teraterm_2026-04-09_160052.log` hit `ELR=...101B8450`.
- This proves the `cbz x21, #0x101B8450` branch was taken.
- So `x21` is zero and the helper path at `0x101B8428..0x101B844C` is skipped.
- Active flow now reaches:
  - `ldr x0, [x22, #8] ; cbnz x0, #0x101B8474`
- Next staged split:
  - `0x101B8460 -> UDF`
  - `0x101B8474 -> UDF`
- Meaning:
  - `0x101B8460` hit: cached pointer is null and flow enters the `0x10063AC0` path
  - `0x101B8474` hit: cached pointer is already nonzero and flow skips directly to the `0x15000042` block


## 2026-04-09 16:38 JST - allocator path taken after null cached pointer

- `teraterm_2026-04-09_163822.log` hit `ELR=...101B8460`.
- This proves the cached/global pointer was null and the `0x10063AC0` allocator/initializer path is live.
- Next staged split:
  - `0x101B8474 -> UDF`
  - `0x101B8B98 -> UDF`
- Meaning:
  - `0x101B8474` hit: allocator path produced a nonnull pointer and flow reaches the `0x15000042` block
  - `0x101B8B98` hit: pointer remains null after the allocator path and flow falls into the null-tail


## 2026-04-09 16:45 JST - allocator path populated pointer, 0x15000042 block is live

- `teraterm_2026-04-09_164506.log` hit `ELR=...101B8474`.
- This proves the allocator/initializer path populated `[x22 + 8]` and the null-tail was not taken.
- Active flow now enters the `0x15000042` block.
- Next staged split:
  - `0x101B84B0 -> UDF`
  - `0x101B84D4 -> UDF`
- Meaning:
  - `0x101B84B0` hit: the `0x15000042` block takes its update/reporting leg
  - `0x101B84D4` hit: the `0x15000042` block converges directly to the common post-block


## 2026-04-09 16:57 JST - 0x15000042 update/reporting leg is live

- `teraterm_2026-04-09_165712.log` hit `ELR=...101B84B0`.
- This proves the `0x15000042` block took its update/reporting leg rather than converging directly at `0x101B84D4`.
- Next staged split:
  - `0x101B84D4 -> UDF`
  - `0x101B8B9C -> UDF`
- Meaning:
  - `0x101B84D4` hit: the update/reporting call returned nonnegative and flow converged to the common post-block
  - `0x101B8B9C` hit: the update/reporting call returned negative and flow fell into the error tail


## 2026-04-09 18:07 JST - 0x15000042 update/reporting call succeeded

- `teraterm_2026-04-09_180755.log` hit `ELR=...101B84D4`.
- This proves the `0x101B1B70` update/reporting call returned nonnegative and flow converged to the common post-block.
- Next staged split:
  - `0x101B84EC -> UDF`
  - `0x101B8B98 -> UDF`
  - `0x101B8B9C -> UDF`
- Meaning:
  - `0x101B84EC` hit: `0x1020B300` returned nonnegative and the byte flag is nonzero
  - `0x101B8B98` hit: status stayed nonnegative but the byte flag is zero
  - `0x101B8B9C` hit: `0x1020B300` returned negative and flow fell into the error tail


## 2026-04-09 18:29 JST - byte flag was zero, null-tail side path is live

- `teraterm_2026-04-09_182944.log` hit `ELR=...101B8B98`.
- This proves the common post-block kept a nonnegative status but the byte flag at `[sp + 0x48]` was zero.
- Flow enters the null-tail cleanup and then falls through to the side path at `0x101B8BCC`.
- Next staged stop:
  - `0x101B8BE0 -> UDF`
- Meaning:
  - `0x101B8BE0` hit: the `0x101B11E8` side-path query returned and we can inspect that side path next


## 2026-04-09 18:42 JST - side-path 0x11000001 query returned

- `teraterm_2026-04-09_184242.log` hit `ELR=...101B8BE0`.
- This proves the side-path query helper `0x101B11E8` returned.
- Because register dumping recursed at this site, the next split reads the branch outcome directly.
- Next staged split:
  - `0x101B8BF4 -> UDF`
  - `0x101B99C8 -> UDF`
- Meaning:
  - `0x101B8BF4` hit: the side-path `0x11000001` query returned nonnegative and flow continues into the `0x12000002` block
  - `0x101B99C8` hit: the side-path `0x11000001` query returned negative and flow jumps to the shared error/report tail


## 2026-04-09 19:02 JST - side-path 0x11000001 query succeeded

- `teraterm_2026-04-09_190249.log` hit `ELR=...101B8BF4`.
- This proves the side-path `0x11000001` query returned nonnegative.
- Next prepared split:
  - `0x101B8C10 -> UDF`
  - `0x101B99C0 -> UDF`
- Meaning:
  - `0x101B8C10` hit: the side-path `0x12000002` block returned nonnegative and flow continues deeper
  - `0x101B99C0` hit: the side-path `0x12000002` block returned negative and flow jumps to the nearby cleanup/report tail


## 2026-04-09 20:16 JST - side-path 0x12000002 block succeeded

- `teraterm_2026-04-09_201606.log` hit `ELR=...101B8C10`.
- This proves the side-path `0x12000002` block returned nonnegative.
- Next staged split:
  - `0x101B8C3C -> UDF`
  - `0x101B99A8 -> UDF`
- Meaning:
  - `0x101B8C3C` hit: the `0x10064470` helper returned nonnegative and flow continues deeper
  - `0x101B99A8` hit: the `0x10064470` helper returned negative and flow jumps to the nearby cleanup/report tail


## 2026-04-09 20:26 JST - side-path helper 0x10064470 succeeded

- `teraterm_2026-04-09_202611.log` hit `ELR=...101B8C3C`.
- This proves the side-path helper `0x10064470` returned nonnegative.
- Next staged split:
  - `0x101B8C5C -> UDF`
  - `0x101B8C64 -> UDF`
- Meaning:
  - `0x101B8C5C` hit: `0x101C72C8` returned zero-like and flow takes the local `0xC0000017` path
  - `0x101B8C64` hit: `0x101C72C8` returned nonzero and flow continues into the deeper helper chain


## 2026-04-09 21:51 JST - 0x101C72C8 returned nonzero

- `teraterm_2026-04-09_215103.log` hit `ELR=...101B8C64`.
- This proves `0x101C72C8` returned nonzero and flow entered the deeper helper chain.
- Next staged split:
  - `0x101B8C90 -> UDF`
  - `0x101B8C94 -> UDF`
- Meaning:
  - `0x101B8C90` hit: `0x102634D0` returned nonnegative and flow continues into `0x101C5AF8`
  - `0x101B8C94` hit: `0x102634D0` returned negative and flow skips directly to the common status merge


## 2026-04-09 22:09 JST - 0x102634D0 returned nonnegative

- `teraterm_2026-04-09_220924.log` hit `ELR=...101B8C90`.
- This proves `0x102634D0` returned nonnegative.
- Next staged split:
  - `0x101B8CA0 -> UDF`
  - `0x101B99A8 -> UDF`
- Meaning:
  - `0x101B8CA0` hit: `0x101C5AF8` returned nonnegative and flow continues into the `0x16000048` block
  - `0x101B99A8` hit: `0x101C5AF8` returned negative and flow falls into the side-path cleanup/report tail

## 2026-04-09 22:29 JST - 0x16000048 block reached, next live gate is 0x101B37C0

- `teraterm_2026-04-09_222923.log` hit `ELR=...101B8CA0`.
- This proves `0x101C5AF8` returned nonnegative and flow continued into the `0x16000048` block.
- Next staged split:
  - `0x101B8D1C -> UDF`
  - `0x101B9978 -> UDF`
- Meaning:
  - `0x101B8D1C` hit: `0x101B37C0` returned nonnegative and flow continues deeper through the side path
  - `0x101B9978` hit: `0x101B37C0` returned negative and flow drops into the side-path report tail

## 2026-04-09 23:00 JST - 0x101B37C0 returned nonnegative, next live gate is 0x101BCAB0

- `teraterm_2026-04-09_230052.log` hit `ELR=...101B8D1C`.
- This proves `0x101B37C0` returned nonnegative and flow continued deeper through the side path.
- Next staged split:
  - `0x101B8D70 -> UDF`
  - `0x101B9978 -> UDF`
- Meaning:
  - `0x101B8D70` hit: `0x101BCAB0` returned nonnegative and flow continues into the post-call loop / report block
  - `0x101B9978` hit: `0x101BCAB0` returned negative and flow drops into the side-path report tail

## 2026-04-09 23:04 JST - 0x101BCAB0 failed, next live split is inside the report tail

- `teraterm_2026-04-09_230404.log` hit `ELR=...101B9978`.
- This proves `0x101BCAB0` returned negative and flow entered the local side-path report tail.
- Next staged split:
  - `0x101B99B4 -> UDF`
  - `0x101B99C8 -> UDF`
- Meaning:
  - `0x101B99B4` hit: the tail takes the cleanup-helper path through `0x10064528`
  - `0x101B99C8` hit: the tail skips that helper and drops directly into cleanup/report teardown

## 2026-04-09 23:08 JST - report tail chose the 0x10064528 cleanup helper

- `teraterm_2026-04-09_230833.log` hit `ELR=...101B99B4`.
- This proves the side-path report tail took the cleanup-helper path through `0x10064528`.
- Next staged stop:
  - `0x101B99B8 -> UDF`
- Meaning:
  - `0x101B99B8` hit: `0x10064528` returned and flow resumed in the local report tail

## 2026-04-09 23:19 JST - 0x10064528 returned, next split checks the first optional cleanup object

- `teraterm_2026-04-09_231933.log` hit `ELR=...101B99B8`.
- This proves `0x10064528` returned and flow resumed in the local report tail.
- Next staged split:
  - `0x101B99D0 -> UDF`
  - `0x101B99D8 -> UDF`
- Meaning:
  - `0x101B99D0` hit: `[sp + 0x228]` is nonzero and the first optional cleanup call to `0x101DE718` is taken
  - `0x101B99D8` hit: `[sp + 0x228]` is zero and that optional cleanup is skipped

## 2026-04-09 23:23 JST - first optional cleanup call is live, next split checks the second one

- `teraterm_2026-04-09_232354.log` hit `ELR=...101B99D0`.
- This proves `[sp + 0x228]` is nonzero and the first optional cleanup call to `0x101DE718` is taken.
- Next staged split:
  - `0x101B99E0 -> UDF`
  - `0x101B99E8 -> UDF`
- Meaning:
  - `0x101B99E0` hit: `[sp + 0xC8]` is nonzero and the second optional cleanup call to `0x101DE718` is taken
  - `0x101B99E8` hit: `[sp + 0xC8]` is zero and that cleanup is skipped

## 2026-04-09 23:31 JST - second optional cleanup call is live, next split checks the third one

- `teraterm_2026-04-09_233106.log` hit `ELR=...101B99E0`.
- This proves `[sp + 0xC8]` is nonzero and the second optional cleanup call to `0x101DE718` is taken.
- Next staged split:
  - `0x101B99F0 -> UDF`
  - `0x101B99F8 -> UDF`
- Meaning:
  - `0x101B99F0` hit: `[sp + 0x98]` is nonzero and the third optional cleanup call to `0x101DE718` is taken
  - `0x101B99F8` hit: `[sp + 0x98]` is zero and that cleanup is skipped

## 2026-04-09 23:42 JST - third optional cleanup was skipped, next split checks the fourth one

- `teraterm_2026-04-09_234207.log` hit `ELR=...101B99F8`.
- This proves `[sp + 0x98]` is zero and the third optional cleanup call is skipped.
- Next staged split:
  - `0x101B9A00 -> UDF`
  - `0x101B9A08 -> UDF`
- Meaning:
  - `0x101B9A00` hit: `[sp + 0xB0]` is nonzero and the fourth optional cleanup call to `0x101DE718` is taken
  - `0x101B9A08` hit: `[sp + 0xB0]` is zero and that cleanup is skipped

## 2026-04-09 23:58 JST - fourth optional cleanup was skipped, next split checks the sign of w20

- `teraterm_2026-04-09_235851.log` hit `ELR=...101B9A08`.
- This proves `[sp + 0xB0]` is zero and the fourth optional cleanup call is skipped.
- Next staged split:
  - `0x101B9A0C -> UDF`
  - `0x101B9A74 -> UDF`
- Meaning:
  - `0x101B9A0C` hit: `w20` is still negative and flow enters the negative-status cleanup block
  - `0x101B9A74` hit: `w20` is nonnegative and flow skips into the success-side accounting block

## 2026-04-10 00:26 JST - negative-status cleanup block is live, next split checks [sp + 0xA8]

- `teraterm_2026-04-10_002604.log` hit `ELR=...101B9A0C`.
- This proves `w20` is still negative and flow entered the negative-status cleanup block.
- Next staged split:
  - `0x101B9A14 -> UDF`
  - `0x101B9A24 -> UDF`
- Meaning:
  - `0x101B9A14` hit: `[sp + 0xA8]` is nonzero and the `0x101BD310` cleanup path is taken
  - `0x101B9A24` hit: `[sp + 0xA8]` is zero and that path is skipped

## 2026-04-10 00:59 JST - [sp + 0xA8] was zero, next split checks [sp + 0xB8]

- `teraterm_2026-04-10_005915.log` hit `ELR=...101B9A24`.
- This proves `[sp + 0xA8]` is zero and the `0x101BD310` cleanup path is skipped.
- Next staged split:
  - `0x101B9A2C -> UDF`
  - `0x101B9A34 -> UDF`
- Meaning:
  - `0x101B9A2C` hit: `[sp + 0xB8]` is nonzero and the next cleanup call to `0x101DE718` is taken
  - `0x101B9A34` hit: `[sp + 0xB8]` is zero and that cleanup is skipped

## 2026-04-10 01:03 JST - [sp + 0xB8] was zero, next split checks [sp + 0x120]

- `teraterm_2026-04-10_010301.log` hit `ELR=...101B9A34`.
- This proves `[sp + 0xB8]` is zero and that optional cleanup is skipped.
- Next staged split:
  - `0x101B9A3C -> UDF`
  - `0x101B9A44 -> UDF`
- Meaning:
  - `0x101B9A3C` hit: `[sp + 0x120]` is nonzero and the next cleanup call to `0x101DE718` is taken
  - `0x101B9A44` hit: `[sp + 0x120]` is zero and that cleanup is skipped

## 2026-04-10 01:54 JST - [sp + 0x120] was zero, next split checks the global cleanup object

- `teraterm_2026-04-10_015400.log` hit `ELR=...101B9A44`.
- This proves `[sp + 0x120]` is zero and that optional cleanup is skipped.
- Next staged split:
  - `0x101B9A5C -> UDF`
  - `0x101B9A84 -> UDF`
- Meaning:
  - `0x101B9A5C` hit: the global cleanup object at `0x10303000+0xCD0` is present and the `0x101DE718` cleanup call is taken
  - `0x101B9A84` hit: that global cleanup path is skipped and flow falls through to the tail epilogue block

## 2026-04-10 02:48 JST - global cleanup was skipped, next split checks the final heartbeat gate

- `teraterm_2026-04-10_024844.log` hit `ELR=...101B9A84`.
- This proves the global cleanup path is skipped and flow reached the final `0x102ef000` heartbeat gate.
- Next staged split:
  - `0x101B9AB8 -> UDF`
  - `0x101B9AC4 -> UDF`
- Meaning:
  - `0x101B9AB8` hit: the gate takes the `0x101E47A8` call
  - `0x101B9AC4` hit: the gate falls straight through to the epilogue

## 2026-04-10 07:29 JST - `0x101C29F0` is the first helper in this chain that already returns `0xC000000D`

- `teraterm_2026-04-10_072907.log` hit `ELR=...101BCB74`.
- This proves `0x101BCAB0` passed its local validation and reached the return from `0x101C29F0`.
- `X0 = 0xC000000D` at the stop, so `0x101C29F0` itself already returns the negative status.
- Next staged split moves into `0x101C29F0`:
  - `0x101C2A28 -> UDF`
  - `0x101C2A4C -> UDF`
- Meaning:
  - `0x101C2A28` hit: the first helper `0x10244878` returned nonnegative and the primary path continues
  - `0x101C2A4C` hit: the first helper path failed or its size-check rejected it, and flow falls into the fallback path `0x100CC7E0`

## 2026-04-10 07:32 JST - `0x101C29F0` primary path failed, next split moves into fallback `0x100CC7E0`

- `teraterm_2026-04-10_073235.log` hit `ELR=...101C2A4C`.
- This proves `0x101C29F0` fell into the fallback path `0x100CC7E0` instead of staying on its primary path.
- Next staged split:
  - `0x100CC870 -> UDF`
  - `0x100CCCF4 -> UDF`
- Meaning:
  - `0x100CC870` hit: `0x100CE028` returned `0x104` and fallback parsing entered the deeper path
  - `0x100CCCF4` hit: `0x100CE028` did not return `0x104` and flow fell into the fallback exit/report path

## 2026-04-10 07:36 JST - fallback deeper block is live, next split checks the `w25` bit7 gate

- `teraterm_2026-04-10_073626.log` hit `ELR=...100CCCF4`.
- This proves `0x100CC7E0` reached the deeper block and still carried `w22 = 0xC000000D`.
- Next staged split:
  - `0x100CCD00 -> UDF`
  - `0x100CCD30 -> UDF`
- Meaning:
  - `0x100CCD00` hit: `w25` bit7 is clear and flow enters the report/update block
  - `0x100CCD30` hit: `w25` bit7 is set or the block is skipped and flow falls directly to the tail epilogue

## 2026-04-10 20:22 JST - fallback report/update block is live, next split checks the internal bit3 gate

- `teraterm_2026-04-10_202200.log` hit `ELR=...100CCD00`.
- This proves `w25` bit7 was clear and flow entered the report/update block at `0x100CCCFC`.
- Next staged split:
  - `0x100CCD20 -> UDF`
  - `0x100CCD30 -> UDF`
- Meaning:
  - `0x100CCD20` hit: the bit3 gate does not branch and the `0x100CC6B0` call is live
  - `0x100CCD30` hit: the bit3 gate branches and that call is skipped, falling straight to the tail

## 2026-04-10 20:29 JST - fallback tail is exhausted, next split returns to `0x100CE028` early validation

- `teraterm_2026-04-10_202950.log` hit `ELR=...100CCD30`.
- This proves the `0x100CC6B0` call was skipped and the fallback report/update block simply falls into its tail.
- Next staged split moves upstream into `0x100CE028`:
  - `0x100CE0E4 -> UDF`
  - `0x100CE19C -> UDF`
- Meaning:
  - `0x100CE0E4` hit: early validation passed and flow reached `0x10064B08`
  - `0x100CE19C` hit: one of the early validation gates failed and flow took the hardcoded `0xC000000D` path directly

## 2026-04-10 20:37 JST - `0x100CE028` early validation passed; next split moves from the pre-call site to the post-call site

- `teraterm_2026-04-10_203432.log` hit `ELR=...100CE0E4`.
- This proves `0x100CE028` passed its early validation gates and reached the `0x10064B08` call site.
- Next staged split:
  - `0x100CE0F4 -> UDF`
  - `0x100CE19C -> UDF`
- Meaning:
  - `0x100CE0F4` hit: `0x10064B08` returned nonnegative and flow reached the local state checks on `[sp+0x20]`
  - `0x100CE19C` hit: flow still ended in the hardcoded `0xC000000D` path after the `0x10064B08` stage

## 2026-04-10 20:40 JST - `0x10064B08` returned nonnegative, so the next split checks the local state decode

- `teraterm_2026-04-10_203924.log` hit `ELR=...100CE0F4`.
- `X0 = 0` at the stop, proving `0x10064B08` returned nonnegative.
- Next staged split:
  - `0x100CE11C -> UDF`
  - `0x100CE19C -> UDF`
- Meaning:
  - `0x100CE11C` hit: the local state decode accepts the `[sp+0x20]` value and reaches the normalize/merge block
  - `0x100CE19C` hit: the local state decode still falls into the hardcoded `0xC000000D` path

## 2026-04-10 20:46 JST - the local state decode accepted the state value; next stop moves to the `0x100CE4E0` return

- `teraterm_2026-04-10_204501.log` hit `ELR=...100CE11C`.
- This proves the local state decode accepted the `[sp+0x20]` value and reached the normalize/merge block.
- Next staged split:
  - `0x100CE160 -> UDF`
  - `0x100CE19C -> UDF`
- Meaning:
  - `0x100CE160` hit: `0x100CE4E0` returned and its raw status can be read directly
  - `0x100CE19C` hit: flow still fell back into the hardcoded `0xC000000D` path before the `0x100CE4E0` return site

## 2026-04-10 20:50 JST - `0x100CE4E0` is the live source of `0xC000000D`; next stop moves to the `0x101CE530` return

- `teraterm_2026-04-10_204817.log` hit `ELR=...100CE160`.
- `X0 = 0xC000000D` there, proving `0x100CE4E0` itself already returns the negative status.
- Next staged stop:
  - `0x100CE684 -> UDF`
- Meaning:
  - `X0` at `0x100CE684` shows whether `0x101CE530` produced a nonzero object/handle path or whether flow will continue into the path-parse branch

## 2026-04-10 20:53 JST - `0x101CE530` returned null, so the next split distinguishes root-only vs normal named-path parsing

- `teraterm_2026-04-10_205215.log` hit `ELR=...100CE684`.
- `X0 = 0` there, proving `0x101CE530` did not produce an existing object/handle path.
- Next staged split:
  - `0x100CE6A0 -> UDF`
  - `0x100CE8F8 -> UDF`
- Meaning:
  - `0x100CE6A0` hit: the input path matched the root-only special case
  - `0x100CE8F8` hit: flow entered the normal named-path branch

## 2026-04-10 20:56 JST - the normal named-path branch is live; next split checks whether `0x100CEB30` produces a usable object

- `teraterm_2026-04-10_205537.log` hit `ELR=...100CE8F8`.
- This proves flow entered the normal named-path branch rather than the root-only special case.
- Next staged split:
  - `0x100CE914 -> UDF`
  - `0x100CE920 -> UDF`
- Meaning:
  - `0x100CE914` hit: `0x100CEB30` returned null and flow falls into local `0xC0000017`
  - `0x100CE920` hit: the branch produced a nonnull `x21` and continues into deeper parsing

## 2026-04-10 20:58 JST - the named-path branch produced a usable `x21`; next stop moves to the recursive `0x100CE4E0` return

- `teraterm_2026-04-10_205842.log` hit `ELR=...100CE920`.
- `X21` was nonnull, proving `0x100CEB30` succeeded and flow continued into the recursive parse call.
- Next staged stop:
  - `0x100CE94C -> UDF`
- Meaning:
  - `X0` there is the recursive `0x100CE4E0` return. If negative, the failure chain is being reproduced one level deeper.


## 2026-04-10 21:02 JST - recursive parse switched into the root-only special-case branch

- `teraterm_2026-04-10_210230.log` hit `ELR=...100CE6A0`.
- This proves the recursive `0x100CE4E0` invocation did not stay on the normal named-path branch; it entered the root-only special-case path instead.
- Next staged split:
  - `0x100CE6B8 -> UDF`
  - `0x100CE704 -> UDF`
- Meaning:
  - `0x100CE6B8` hit: `0x10064F48` returned and its status becomes the next live gate
  - `0x100CE704` hit: the branch passed or bypassed `0x10064F48`/local-object validation and merged into the shared post-root path

## 2026-04-10 21:08 JST - `0x10064F48` is not the failure; next split moves to local object validation vs `0x101B0DE0`

- `teraterm_2026-04-10_210807.log` hit `ELR=...100CE6B8`.
- `X0 = 0` there, proving `0x10064F48` returned nonnegative.
- Next staged split:
  - `0x100CE6DC -> UDF`
  - `0x100CE700 -> UDF`
  - `0x100CE704 -> UDF`
- Meaning:
  - `0x100CE6DC` hit: the local `[sp+0x38]` checks passed and `0x101B0DE0` returned
  - `0x100CE700` hit: `0x101B0DE0` returned negative
  - `0x100CE704` hit: the flow merged out through the local object/size/pointer checks

## 2026-04-10 22:47 JST - `0x10064F48` succeeded, but the local root-only object had zero offset/length so `0x101B0DE0` was skipped

- `teraterm_2026-04-10_224715.log` hit `ELR=...100CE704`.
- The stop state showed `X9` nonnull and `X8 = 0`, matching the `ldr w8, [x9,#0xC] ; cbz w8, #0x100CE704` branch.
- Next staged split:
  - `0x100CE7A4 -> UDF`
  - `0x100CE81C -> UDF`
  - `0x100CE884 -> UDF`
- Meaning:
  - `0x100CE7A4` hit: the optional callback path returned and `x20` becomes visible
  - `0x100CE81C` hit: `x20` survived the callback-side validation path
  - `0x100CE884` hit: `x20` stayed zero and flow fell into the local list/scan fallback

## 2026-04-10 22:50 JST - `x20` stayed zero, so the callback validation branch is dead and flow drops into the local list fallback

- `teraterm_2026-04-10_225043.log` hit `ELR=...100CE7A4`.
- `X0 = 0` at the stop, so `mov x20, x0` leaves `x20 == 0` and the later `cbz x20, #0x100CE884` path is taken.
- Next staged split:
  - `0x100CE89C -> UDF`
  - `0x100CE8F0 -> UDF`
- Meaning:
  - `0x100CE89C` hit: the local list fallback has at least one entry to scan
  - `0x100CE8F0` hit: the fallback list is empty and flow skips directly to the post-scan merge
## 2026-04-10 22:59 JST
- `teraterm_2026-04-10_225937.log` hit `ELR=...100CE89C`.
- Local list fallback is nonempty; flow entered the first-entry scan block.
- Next split: `0x100CE8A4` / `0x100CE8D4` / `0x100CE8E4`.
## 2026-04-10 23:04 JST
- `teraterm_2026-04-10_230434.log` hit `ELR=...100CE8A4`.
- Local list fallback entered the first-entry callback path.
- Next split prepared: `0x100CE8C8` / `0x100CE8D4`.
## 2026-04-10 23:08 JST
- `teraterm_2026-04-10_230851.log` hit `ELR=...100CE8D4`.
- First-entry callback returned the local `w28` sentinel and flowed to the next-entry path.
- Next split: `0x100CE8A4` / `0x100CE8E4`.
## 2026-04-10 23:11 JST
- `teraterm_2026-04-10_231202.log` hit `ELR=...100CE8A4` again.
- The list scan advanced past the first entry and did not reach merge yet.
- Next probe: `0x100CE8E4` only.
## 2026-04-10 23:15 JST
- `teraterm_2026-04-10_231513.log` hit `ELR=...100CE8E4`.
- The list scan reached merge.
- Next split: `0x100CE9A4` / `0x100CEABC`.
## 2026-04-10 23:19 JST
- `teraterm_2026-04-10_231920.log` hit `ELR=...100CEABC`.
- After merge, flow entered the negative tail cleanup.
- Next split: `0x100CEAC4` / `0x100CEAD0`.
- 	eraterm_2026-04-10_232525.log is valid against the 23:20 staging of stop_100CEAC4_or_100CEAD0_udf.
- Hit ELR=...100CEAD0.
- Meaning: the negative tail skipped the local [sp+0x28] cleanup object and entered the remaining x21/x22/x23 cleanup sequence.
- Next split prepared:  x100CEADC / 0x100CEAE4 / 0x100CEAF0 / 0x100CEAF8.
- Staging pending because the removable media is not currently visible to Windows (Disk 3 / No Media).
## 2026-04-10 23:54 JST
- `teraterm_2026-04-10_235136.log` was timestamp-valid, but the staged `BOOTAA64.stop_100CE94C_udf` image was stale.
- That stale image still had `UDF` stops at `0x100CE6A0` and `0x100CE814`, so the hit at `0x100CE6A0` was real for the staged binary but not the intended clean probe.
- Built a unique clean image `BOOTAA64.stop_100CE94C_udf.clean.EFI` and verified:
  - `0x100CE6A0` original
  - `0x100CE814` original
  - `0x100CE94C` = `UDF`
- Restaged the clean `0x100CE94C` probe to `F:` and reset the marker to `BOOTAA64.stop_100CE94C_udf.clean`.
- Next required run: any `teraterm` log after the `23:54 JST` clean staging.
## 2026-04-11 00:00 JST
- `teraterm_2026-04-10_235637.log` matched the clean `0x100CE94C` staging and hit `ELR=...100CE94C`.
- That confirms the recursive `0x100CE4E0` call returned and `mov w25, w0` completed.
- Exact status was still unreadable because the exception dump recursed again at `0x100CE94C`.
- Restaged a new unique clean probe with only `0x100CE950 = UDF` and `0x100CE94C` restored to the branch `tbnz w25,#0x1f,#0x100CE814`.
- Next required run: any log after the `00:00 JST` clean2 staging.
## 2026-04-11 00:06 JST
- `teraterm_2026-04-11_000207.log` matched the clean2 `0x100CE950` staging.
- `0x100CE950` did not fire; `BOOTAA64.EFI` instead returned with `gBS->Exit Status=Invalid Parameter`.
- That means the branch at `0x100CE94C` was taken and the recursive `0x100CE4E0` call returned a negative status.
- Restaged a new unique clean probe with only `0x100CE814 = UDF` and `0x100CE94C/0x100CE950` restored.
- Next required run: any log after the `00:06 JST` clean3 staging.
## 2026-04-11 00:18 JST
- `teraterm_2026-04-11_001554.log` matched the clean3 `0x100CE814` staging and hit `ELR=...100CE814`.
- That confirms the recursive `0x100CE4E0` return is negative and the local negative path at `0x100CE814` is actually reached.
- Exact status was still unreadable because the dump recursed again at that site.
- Restaged a new unique clean probe with only `0x100CE818 = UDF` and `0x100CE814` restored.
- Next required run: any log after the `00:18 JST` clean4 staging.
## 2026-04-11 00:28 JST
- Built and staged `BOOTAA64.cmp_100CE814_eq_C000000D.clean5`.
- Replaced `0x100CE814..0x100CE828` with a temporary compare harness:
  - `mov w8, #0xD`
  - `movk w8, #0xC000, lsl #16`
  - `cmp w25, w8`
  - `b.eq #0x100CE828`
  - `0x100CE824 = UDF`
  - `0x100CE828 = UDF`
- Current readout:
  - `0x100CE824` => not `0xC000000D`
  - `0x100CE828` => equals `0xC000000D`
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_002826.md`
## 2026-04-11 01:09 JST
- Built and staged `BOOTAA64.cmp_100CE8E4_eq_C000000D.clean6`.
- Replaced `0x100CE8E4..0x100CE8F8` with a temporary compare harness:
  - `mov w8, #0xD`
  - `movk w8, #0xC000, lsl #16`
  - `cmp w25, w8`
  - `b.eq #0x100CE8F8`
  - `0x100CE8F4 = UDF`
  - `0x100CE8F8 = UDF`
- Current readout:
  - `0x100CE8F4` => merge-site `w25` is not `0xC000000D`
  - `0x100CE8F8` => merge-site `w25` equals `0xC000000D`
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_010923.md`
## 2026-04-11 01:41 JST
- Built and staged `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- Replaced `0x100CE8C8..0x100CE8DC` with a temporary compare harness on the callback return `w0`:
  - `mov w8, #0xD`
  - `movk w8, #0xC000, lsl #16`
  - `cmp w0, w8`
  - `b.eq #0x100CE8DC`
  - `0x100CE8D8 = UDF`
  - `0x100CE8DC = UDF`
- Current readout:
  - `0x100CE8D8` => per-entry callback return is not `0xC000000D`
  - `0x100CE8DC` => per-entry callback return equals `0xC000000D`
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_014100.md`
## 2026-04-11 12:03 JST
- Built and staged `BOOTAA64.stop_100CE8B8_udf.clean8`.
- Restored the clean7 compare harness and replaced only `0x100CE8B8` with `UDF`.
- Purpose:
  - stop immediately before `blr x15` in the per-entry list callback dispatch
  - recover `x19` (current list node) and `x8`/`x15` (loaded callback target)
  - verify whether the live `0xC000000D` source is a real code callback or a data-driven trampoline/table path
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_120311.md`
## 2026-04-11 20:42 JST
- Built and staged `BOOTAA64.stop_100CE8BC_udf.clean9`.
- clean8 confirmed the path reaches `0x100CE8B8`, but the register dump there was still too noisy to recover the dispatch target directly.
- clean9 restores `0x100CE8B8` to the original imported-helper call and stops only at `0x100CE8BC`.
- Purpose:
  - let `0x102B26C0` run
  - stop immediately before the final `blr x15`
  - read the helper-resolved callback target rather than the raw pre-helper field
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_204236.md`
## 2026-04-11 20:50 JST
- Patched `ArmPkg/Library/DefaultExceptionHandlerLib/AArch64/DefaultExceptionHandler.c` in the WSL edk2 workspace.
- Change:
  - emit a compact `[A733-EXC-REG]` serial block for `X0`, `X8`, `X15`, `X19..X28`, `FP`, `LR`
  - do it before any symbol walk / stack walk / `DEBUG()`-heavy work
- Reason:
  - clean8 and clean9 both reached the desired sites, but recursive exception logging kept corrupting the later GPR dump
  - the new ordering should make the live callback target readable on the next run
- Rebuilt firmware with `build_edk2.sh` and rewrote SD with `write_sd.py`.

## 2026-04-11 clean9 and stale carrier fix
- `clean9` remained the active BOOTAA64 probe (`0x100CE8BC`) throughout the 20:52 run, but the raw firmware on SD was still being sourced from an out-of-date `sd_boot.img`.
- Rebuilt `sd_boot.img` explicitly with `make_sd_image.py`, verified the embedded build stamp/FD mtime, rewrote `PhysicalDrive3`, then restaged `BOOTAA64.stop_100CE8BC_udf.clean9` onto `F:`.
- Any interpretation of exception-register availability must use a log captured after the 20:58 rewrite.

## clean10: split inside callback target bootmgfw+0xE1210
- clean9 established that the live list-entry callback dispatch site resolves `x15` to `bootmgfw + 0xE1210` after the imported helper `0x102B26C0`.
- clean10 restores the dispatch site (`0x100CE8BC`) and instead splits inside the callback target itself:
  - `0x100E13EC` => early hardcoded `0xC0000001` validation return
  - `0x100E145C` => early validation passed and flow reached the deeper helper/global-state block

## 2026-04-11 21:29 JST
- Reverted the `clean7` compare harness and restaged `BOOTAA64.stop_100CE8B8_udf.clean8`.
- Purpose:
  - stop again at the live per-entry dispatch site `0x100CE8B8`
  - recover the later-entry node/context directly after proving a later callback returns exact `0xC000000D`
- Snapshot: `D:/Projects/porta-a733-bringup/analysis/media_snapshots/windows_media_F_20260411_213516.md`

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
- It again hit `ELR=bootmgfw+0xCE8DC`, i.e. the compare-harness equality side.
- `FP+0x18` recovered the original stack-local callback context:
  - `+00=0`, `+08=0`, `+10=0`, `+18=0xC0000001`
- The node dump remained the same later-entry descriptor cluster:
  - `+08=bootmgfw+0x2C39F0`
  - `+10=bootmgfw+0xE1168`
  - `+18=bootmgfw+0xE11C8`
  - `+20=bootmgfw+0xE1210`
  - `+28=bootmgfw+0xE1D18`
- Interpretation: compare-site stack recovery adds no new per-entry context beyond the existing sentinel payload, so the next useful split is back inside the shared callback target itself.
- Restaged `BOOTAA64.stop_100E13EC_or_100E145C.clean10`.

## 2026-04-12 01:53 JST clean10 early-return decode

- Valid log: `teraterm_2026-04-12_015325.log` against `BOOTAA64.stop_100E13EC_or_100E145C.clean10` and firmware `built at 13:33:30 on Apr 11 2026`.
- It hit `ELR=bootmgfw+0xE13EC`, the early sentinel-return block in callback target `bootmgfw+0xE1210`.
- The decoded local block is clearly malformed before any deeper helper runs:
  - `FP+0x18 +00 = 0x00000001FFFFFFFF`
  - `FP+0x18 +08 = 0x0000020000000200`
  - `FP+0x18 +10 = 0x00088E7F00002351`
  - `FP+0x18 +18 = 0x800FB6BC00000900`
- Decoding those bytes against the validation logic at `0x100E1324..0x100E13E8` shows multiple independent failures:
  - `[sp+0x21]` halfword is nonzero
  - `[sp+0x1B] = 0xFFFF`, outside accepted set `{0x0200,0x0400,0x0800,0x1000}`
  - `[sp+0x25] = 0x02`, below the accepted `0xF0/0xF8` gate
- Conclusion: this `clean10` hit is only the early `0xC0000001` reject path and is not the later callback invocation that actually returns `0xC000000D`.
- To avoid spending more runs on the wrong invocation, expanded the exception dump to print `FP+0x18..+0x38`, rebuilt raw firmware, rewrote `PhysicalDrive3`, and switched the active ESP probe back to `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.

## 2026-04-12 02:18 JST clean7 with expanded FP dump

- Valid log: `teraterm_2026-04-12_021943.log` against `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` and firmware `built at 17:04:18 on Apr 11 2026`.
- It again hit `ELR=bootmgfw+0xCE8DC`, the compare-harness equality side.
- Expanded frame-local dump now shows:
  - `FP+0x18 +00=0`
  - `FP+0x18 +08=0`
  - `FP+0x18 +10=0`
  - `FP+0x18 +18=0xC0000001`
  - `FP+0x18 +20=0`
  - `FP+0x18 +28=bootmgfw+0x2C39F0`
  - `FP+0x18 +30=0x23FFFF070`
  - `FP+0x18 +38=0x23FFFEE98`
- The node is still `X19=0x40001480` with descriptor fields `+10=0xE1168`, `+18=0xE11C8`, `+20=0xE1210`, `+28=0xE1D18`.
- Interpretation: the later `000d`-returning entry still does not differ at the compare site by anything richer than the known sentinel payload. The extra frame-local words only confirm nearby descriptor/data pointers.
- Built `BOOTAA64.stop_100E145C_only.clean12.EFI` to ignore the noisy early `0x100E13EC` reject path and stop only if some invocation of `bootmgfw+0xE1210` reaches the deeper path at `0x100E145C`.
- `clean12` staging is pending because `F:` disappeared after the latest run.

## 2026-04-12 15:58 JST clean12 miss

- Valid log: `teraterm_2026-04-12_155835.log` against `BOOTAA64.stop_100E145C_only.clean12` staged at `2026-04-12 15:36:29 JST`.
- `BOOTAA64.EFI` did start, but no `0x100E145C` trap fired.
- The image returned through `gBS->Exit(Status=Invalid Parameter)` and BDS fell back to shell.
- Conclusion: the active `000d` source is not the deeper `0x100E145C` path of `bootmgfw+0xE1210`.
- Rolled the active probe back to `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7` and rebuilt raw firmware with next-node exception tracing before restaging.
- Current media snapshot: `analysis/media_snapshots/windows_media_F_20260412_160911.md`

## 2026-04-12 16:12 JST clean7 ambiguity and clean13 pivot

- `teraterm_2026-04-12_161209.log` is valid against `windows_media_F_20260412_160911.md` / active marker `BOOTAA64.cmp_100CE8C8_eq_C000000D.clean7`.
- Disassembly of the patched `clean7` image showed the site at `0x100CE8DC` is ambiguous: it can trap on the sentinel-equality leg before the explicit `C000000D` compare.
- So `ELR=...100CE8DC` is not a clean proof of `C000000D` by itself.
- The important new observation from that log is the next-node descriptor cluster:
  - current node `0x40001480`: `+20 = bootmgfw+0xE1210`
  - next node `0x400014D0`: `+10 = bootmgfw+0xDC158`, `+18 = bootmgfw+0xDC190`, `+20 = bootmgfw+0xDC1A0`, `+28 = 0`
- Static analysis of `0x100DC1A0` on `BOOTAA64.original.EFI`:
  - it is an interior basic-block site inside `0x100DB4C0-0x100DC710`
  - exact instruction at `0x100DC1A0` is `str x9, [x0]`
- Built and staged `BOOTAA64.stop_100DC1A0_udf.clean13` with the shared base patches plus `0x100DC1A0 -> UDF`.
- Active snapshot after staging: `analysis/media_snapshots/windows_media_F_20260412_161920.md`

## 2026-04-12 16:43 JST clean13 miss and return to clean11

- `teraterm_2026-04-12_164343.log` is valid against `analysis/media_snapshots/windows_media_F_20260412_161920.md` / active marker `BOOTAA64.stop_100DC1A0_udf.clean13`.
- No trap at `0x100DC1A0` occurred; direct `BOOTAA64.EFI` still returned `EFI_INVALID_PARAMETER` and the later `ConvertPages` line is retry noise.
- Conclusion: the alternate cluster target `bootmgfw+0xDC1A0` is not the immediate live callback on this direct path, so `clean13` is not useful as the active probe.
- Updated the firmware exception handler to dump `NEXT2` in addition to `NODE` and `NEXT`, rebuilt the raw firmware, rewrote `PhysicalDrive3`, and restaged `BOOTAA64.stop_100CE8B4_udf.clean11`.
- Active snapshot after restaging: `analysis/media_snapshots/windows_media_F_20260412_165014.md`.


## 2026-04-12 17:04 JST clean14 pivot

- Source evidence from `teraterm_2026-04-12_170051.log` / active `clean11`:
  - current dispatch node `0x40001580` -> target `bootmgfw+0xE1210`
  - next node `0x400015D0` -> target `bootmgfw+0xDE1A0`
  - next-next node `0x40001620` -> target `bootmgfw+0xD8840`
- Static analysis confirmed both alternate targets are real function entries:
  - `0x100DE1A0` entry of `0x100DE1A0-0x100DEA68`
  - `0x100D8840` entry of `0x100D8840-0x100D9408`
- New active probe: `BOOTAA64.stop_100DE1A0_udf.clean14`
- Patch set:
  - base: `0x10054A60, 0x101CC428, 0x101AFA2C, 0x1003AFEC, 0x1003B134, 0x1003B2D4, 0x1003B2DC, 0x1003B2FC, 0x1003B304`
  - stop: `0x100DE1A0 -> UDF`
- Reading rule:
  - hit `0x100DE1A0`: the immediate alternate node target is live on the direct path
  - no hit and direct `BOOTAA64.EFI` still exits: the chain stays on current-node handling longer than this alternate target


## 2026-04-12 17:07 JST clean15 split

- `clean14` hit at `bootmgfw+0xDE1A0`, proving the immediate `NEXT` node callback is live.
- New active split: `BOOTAA64.stop_100DE210_or_100DE218.clean15`
- Meaning:
  - `0x100DE210` hit: first global byte gate falls into hardcoded `0xC00000BB`
  - `0x100DE218` hit: first gate passes and `0x10064B08` / deeper body becomes live


## 2026-04-12 20:53 JST clean16

- `clean15` result from `teraterm_2026-04-12_172424.log`: hit `0x100DE218`, so the first global gate passed and `0x100DE210` / hardcoded `0xC00000BB` is not live.
- New active probe: `BOOTAA64.stop_100DE224.clean16`
- Meaning:
  - stop at `0x100DE224`, immediately after `bl #0x10064B08`
  - read `X0` as the exact return status of `0x10064B08`


## 2026-04-12 20:58 JST clean17

- `clean16` result from `teraterm_2026-04-12_205729.log`: hit `0x100DE224` with `X0=0`; `0x10064B08` succeeds.
- New active split: `BOOTAA64.stop_100DE260_or_100DEA18.clean17`
- Meaning:
  - `0x100DE260` hit: local decode/validation after `0x10064B08` passes
  - `0x100DEA18` hit: local validation fails into hardcoded `0xC00000BB` report path

## 2026-04-12 21:03 JST clean18

- `clean17` result from `teraterm_2026-04-12_210107.log`: hit `0x100DEA18`, not `0x100DE260`.
- Meaning: local decode/validation after `0x10064B08` fails before the success body.
- Failure-site clue: `X8=3`, but this alone does not identify whether the failing input is `[sp+0x40]` or `[sp+0x48]`.
- New active split: `BOOTAA64.stop_100DE22C_or_100DE24C.clean18`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_210338.md`
- Meaning:
  - `0x100DE22C` hit: the `0x10064B08` return was nonnegative and the code is about to inspect the first decoded word at `[sp+0x40]`
  - `0x100DE24C` hit: the first decoded word was zero, so the code is taking the alternate path that inspects `[sp+0x48]`

## 2026-04-12 21:25 JST clean19 pending

- `clean18` result from `teraterm_2026-04-12_212527.log`: hit `0x100DE22C`.
- Meaning: the function reached the decoded-word inspection point after `0x10064B08`; the trap is before the actual `ldr w8, [sp,#0x40]`, so the decoded word is not visible yet.
- Generated pending split: `BOOTAA64.stop_100DE240_or_100DE250.clean19`
- Pending image: `build/BOOTAA64.stop_100DE240_or_100DE250.clean19.EFI`
- Pending SHA256: `E62FCF4329C142D14973F856DADBE510753C7094EF590521EEFF9C7BE74949DC`
- Staging state: staged after `F:` returned.
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_213159.md`
- Meaning after staging:
  - `0x100DE240` hit: `[sp+0x40]` was nonzero and the original decoded word should be in `X8`
  - `0x100DE250` hit: `[sp+0x40]` was zero and `[sp+0x48]` should be in `X8`

## 2026-04-12 21:35 JST clean20

- `clean19` result from `teraterm_2026-04-12_213404.log`: hit `0x100DE250` with `X8=3`.
- Meaning: `[sp+0x40] == 0`; `[sp+0x48] == 3`; validation expects `4` and therefore falls to `0x100DEA18`.
- New active probe: `BOOTAA64.bypass_100DE254_stop_100DE25C.clean20`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_213515.md`
- Patch behavior:
  - `0x100DE254 -> NOP`, temporarily bypass the `[sp+0x48] == 4` check
  - `0x100DE25C -> UDF`, stop after loading `[sp+0x54]` into `X8`
- Meaning:
  - hit `0x100DE25C`: read `X8` as `[sp+0x54]`, the next validation field

## 2026-04-12 21:38 JST clean21

- `clean20` result from `teraterm_2026-04-12_213704.log`: hit `0x100DE25C` with `X8=2`.
- Meaning: after bypassing the `[sp+0x48] == 4` check, `[sp+0x54] == 2`; original code expects zero and would still fall to `0x100DEA18`.
- Local field summary so far:
  - `[sp+0x40] == 0`
  - `[sp+0x48] == 3`, expected `4`
  - `[sp+0x54] == 2`, expected `0`
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE278.clean21`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_213838.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE278 -> UDF`
- Meaning:
  - hit `0x100DE278`: read `X0` as the return status from helper `0x10055790`

## 2026-04-12 21:41 JST clean22

- `clean21` result from `teraterm_2026-04-12_214049.log`: hit `0x100DE278` with `X0=0`.
- Meaning: after bypassing the two local field checks, helper `0x10055790` succeeds.
- Additional useful frame-local values:
  - `[sp+0x18] == 0x40002AC0`, table/list pointer for `X20`
  - `[sp+0x30] == 0x23FFFEF70`, later loaded into `X27`
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2A0.clean22`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_214148.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2A0 -> UDF`
- Meaning:
  - hit `0x100DE2A0`: read `X0` as the return status from loop helper `0x10055938`

## 2026-04-12 21:51 JST clean23

- `clean22` result from `teraterm_2026-04-12_214348.log`: hit `0x100DE2A0` with `X0=0`.
- Meaning: loop helper `0x10055938` succeeds for the first table/list entry.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2AC.clean23`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_215131.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2AC -> UDF`
- Meaning:
  - hit `0x100DE2AC`: read `X8` as the `[x9+4]` field that the original code expects to be `2`

## 2026-04-12 22:01 JST clean24

- `clean23` result from `teraterm_2026-04-12_220020.log`: hit `0x100DE2AC` with `X8=2`.
- Meaning: `[x9+4]` matches the expected descriptor field value `2`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2C4.clean24`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_220115.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2C4 -> UDF`
- Meaning:
  - hit `0x100DE2C4`: read `X0` as the return value from helper `0x10066D18`; original code expects `0x10`

## 2026-04-12 22:04 JST clean25

- `clean24` result from `teraterm_2026-04-12_220312.log`: hit `0x100DE2C4` with `X0=0`.
- Important correction: the follow-up instruction is `csinc w23,w23,wzr,ne`, so `X0 != 0x10` preserves `w23` instead of immediately setting the match flag. Treat this as a compare/match test, not a plain failure gate.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2D8.clean25`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_220434.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2D8 -> UDF`
- Meaning:
  - hit `0x100DE2D8`: read `X0` as the return value from helper `0x10056060`; check `W23` as the current match flag

## 2026-04-12 22:07 JST clean26

- `clean25` result from `teraterm_2026-04-12_220653.log`: hit `0x100DE2D8` with `X0=0`.
- Meaning: helper `0x10056060` succeeds.
- Limitation: current exception dump does not print `X23`, so branch result must be measured by stop sites rather than register value.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2DC_or_100DE2EC.clean26`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_220752.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2DC -> UDF`
  - `0x100DE2EC -> UDF`
- Meaning:
  - hit `0x100DE2DC`: `W23 == 0`, no match yet; loop advances
  - hit `0x100DE2EC`: `W23 != 0`, match found; follow-up path

## 2026-04-12 22:10 JST clean27

- `clean26` result from `teraterm_2026-04-12_221011.log`: hit `0x100DE2DC`, not `0x100DE2EC`.
- Meaning: `W23 == 0`; current entry did not match, so the loop advances.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE290_or_100DE308.clean27`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_221058.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE290 -> UDF`
  - `0x100DE308 -> UDF`
- Meaning:
  - hit `0x100DE290`: loop continues to another table/list entry
  - hit `0x100DE308`: loop exhausted without a match and loads default failure status

## 2026-04-12 22:15 JST clean28

- `clean27` result from `teraterm_2026-04-12_221422.log`: hit `0x100DE290`.
- Correction: `0x100DE290` is also the first-entry site, so this hit is ambiguous and should not be treated as proof of loop continuation.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_stop_100DE2E0_or_100DE308.clean28`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_221517.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE2E0 -> UDF`
  - `0x100DE308 -> UDF`
- Meaning:
  - hit `0x100DE2E0`: loop reached the post-increment compare; `X19/W19` should reflect the incremented entry index if printed
  - hit `0x100DE308`: loop exhausted without a match and loads default failure status

## 2026-04-12 22:20 JST clean29

- `clean28` result from `teraterm_2026-04-12_221738.log`: hit `0x100DE2E0`, not `0x100DE308`.
- `X19=1`, so the code advanced past no-match entry 0 and reached the post-increment loop compare for entry index 1.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2A0.clean29`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_222021.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE288 -> mov w19,#1`
  - `0x100DE2A0 -> UDF`
- Meaning:
  - start descriptor/list scan from entry index 1 instead of entry 0
  - hit `0x100DE2A0`: read `X0` as the helper `0x10055938` result for entry index 1

## 2026-04-12 22:24 JST clean30

- `clean29` result from `teraterm_2026-04-12_222217.log`: hit `0x100DE2A0` with `X0=0` and `X19=1`.
- Meaning: helper `0x10055938` succeeds for descriptor/list entry index 1.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_start_index1_stop_100DE2DC_or_100DE2EC.clean30`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_222407.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE288 -> mov w19,#1`
  - `0x100DE2DC -> UDF`
  - `0x100DE2EC -> UDF`
- Meaning:
  - hit `0x100DE2DC`: entry index 1 is no-match and loop advances
  - hit `0x100DE2EC`: entry index 1 matched and code enters follow-up path

## 2026-04-12 22:26 JST clean31

- `clean30` result from `teraterm_2026-04-12_222601.log`: hit `0x100DE2DC`, not `0x100DE2EC`, with `X19=1`.
- Meaning: descriptor/list entry index 1 is also no-match; the scan would continue.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_start_index2_stop_100DE2A0.clean31`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_222652.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE288 -> mov w19,#2`
  - `0x100DE2A0 -> UDF`
- Meaning:
  - start descriptor/list scan from entry index 2
  - hit `0x100DE2A0`: read `X0` as the helper `0x10055938` result for entry index 2

## 2026-04-12 22:32 JST clean32

- `clean31` result from `teraterm_2026-04-12_222858.log`: hit `0x100DE2A0` with `X0=0xC000000D` and `X19=2`.
- Meaning: descriptor/list entry index 2 is not a valid helper target. Index 0 and 1 were valid but no-match; index 2 fails the helper itself.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_stop_100DE308_or_100DE318.clean32`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_223203.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE308 -> UDF`
  - `0x100DE318 -> UDF`
- Meaning:
  - hit `0x100DE308`: after two valid no-match entries, the loop terminates with the default no-match status
  - hit `0x100DE318`: the post-cleanup status gate was passed after forcing count=2

## 2026-04-12 22:35 JST clean33

- `clean32` result from `teraterm_2026-04-12_223400.log`: hit `0x100DE308` with `X19=2`.
- Meaning: after forcing count=2, the two valid entries are no-match and the loop reaches the default no-match status path.
- Literal status at `0x100DE308` is `0xC0000225`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE31C.clean33`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_223521.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE308 -> mov w19,#0`
  - `0x100DE31C -> UDF`
- Meaning:
  - hit `0x100DE31C`: clearing the no-match status lets execution pass the `0x100DE318` negative-status gate

## 2026-04-12 22:39 JST clean34

- `clean33` result from `teraterm_2026-04-12_223709.log`: hit `0x100DE31C` with `X19=0`.
- Meaning: clearing the no-match `0xC0000225` status passes the `0x100DE318` negative-status gate.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_x27_count2_clear_100DE308_stop_100DE32C.clean34`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_223911.md`
- Patch behavior:
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE308 -> mov w19,#0`
  - `0x100DE32C -> UDF`
- Meaning:
  - hit `0x100DE32C`: read `X0` as the helper `0x1028DA30` return value

## 2026-04-12 22:42 JST clean35

- `clean34` result from `teraterm_2026-04-12_224055.log`: hit `0x100DE32C` with `X0=1`, but `X19=0`.
- Meaning: the post-no-match helper returns `1`, but clearing only the status leaves the follow-up object pointer unset.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE300.clean35`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_224211.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE300 -> UDF`
- Meaning:
  - force the entry-0 match path at `0x100DE2EC`
  - hit `0x100DE300`: read `X0` as the helper `0x10055938` return value for populating `[sp+0x38]`

## 2026-04-12 22:47 JST clean36

- `clean35` result from `teraterm_2026-04-12_224547.log`: hit `0x100DE300` with `X0=0`.
- Meaning: the forced match path helper `0x10055938` succeeds and should have populated `[sp+0x38]`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE320.clean36`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_224719.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE320 -> UDF`
- Meaning:
  - hit `0x100DE320`: read `X19` as the object pointer loaded from `[sp+0x38]`

## 2026-04-12 22:50 JST clean37

- `clean36` result from `teraterm_2026-04-12_224903.log`: hit `0x100DE320` with `X19=0x23FC514C0`.
- Meaning: the forced match path populated a valid non-null object pointer from `[sp+0x38]`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE32C.clean37`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_225032.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE32C -> UDF`
- Meaning:
  - hit `0x100DE32C`: read `X0` as helper `0x1028DA30` return value on the object-pointer-valid path

## 2026-04-12 22:54 JST clean38

- `clean37` result from `teraterm_2026-04-12_225219.log`: hit `0x100DE32C` with `X0=1` and `X19=0x23FC514C0`.
- Meaning: helper `0x1028DA30` returns `1`; the code will take the `w20 == 1` path toward the object callback.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE378.clean38`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_225408.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE378 -> UDF`
- Meaning:
  - hit `0x100DE378`: read `X15` as the upcoming `blr x15` target loaded from `[x19+8]`
  - also read `X0`/`X1` as the object pointer and second argument for the setup/callback path

## 2026-04-12 22:56 JST clean39

- `clean38` result from `teraterm_2026-04-12_225551.log`: hit `0x100DE378` with `X15=0x23FC25680` and `X0/X19=0x23FC514C0`.
- Meaning: the upcoming indirect call target is a plausible DxeCore function pointer, not an obvious bad pointer.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE380.clean39`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_225639.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE380 -> UDF`
- Meaning:
  - hit `0x100DE380`: read `X0` as the return value from the indirect `blr x15` callback

## 2026-04-12 22:59 JST clean40

- `clean39` result from `teraterm_2026-04-12_225909.log`: hit `0x100DE380` with `X0=0`.
- Meaning: the indirect callback returns success; the nearby log shows `OpenVolume ... -> Success`, so this path is plausibly opening the selected filesystem volume.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE39C.clean40`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_225954.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE39C -> UDF`
- Meaning:
  - hit `0x100DE39C`: read `X0` as the helper `0x100536E8` return value after the object callback path

## 2026-04-12 23:02 JST clean41

- `clean40` result from `teraterm_2026-04-12_230143.log`: hit `0x100DE39C` with `X0=0`.
- Meaning: helper `0x100536E8` succeeds; next original `mov w19,w0` should clear `w19` and pass the negative-status gate at `0x100DE3A0`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3A4.clean41`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_230241.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE3A4 -> UDF`
- Meaning:
  - hit `0x100DE3A4`: post-callback negative-status gate was passed and execution entered the next block

## 2026-04-12 23:05 JST clean42

- `clean41` result from `teraterm_2026-04-12_230428.log`: hit `0x100DE3A4` with `X19=0`.
- Meaning: post-callback negative-status gate passed and execution entered the next block.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE3C0_or_100DE3E8.clean42`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_230527.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE3C0 -> UDF`
  - `0x100DE3E8 -> UDF`
- Meaning:
  - hit `0x100DE3C0`: enters the counter/update path
  - hit `0x100DE3E8`: skips the counter/update path due to global state

## 2026-04-12 23:08 JST clean43

- `clean42` result from `teraterm_2026-04-12_230737.log`: hit `0x100DE3E8`, not `0x100DE3C0`.
- Meaning: the first counter/update path was skipped due to global state.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE408_or_100DE534.clean43`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_230839.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE408 -> UDF`
  - `0x100DE534 -> UDF`
- Meaning:
  - hit `0x100DE408`: global `[0x102EFDD8] == 1`, enters allocation/list scan path
  - hit `0x100DE534`: global `[0x102EFDD8] != 1`, skips that path toward no-`x20` failure handling

## 2026-04-12 23:12 JST clean44

- `clean43` result from `teraterm_2026-04-12_231139.log`: hit `0x100DE408`, not `0x100DE534`.
- Meaning: global `[0x102EFDD8] == 1`, so execution enters the allocation/list scan path.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE420.clean44`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_231230.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE420 -> UDF`
- Meaning:
  - hit `0x100DE420`: read `X9` as the global list/table pointer loaded from `[x20+#0xde0]`

## 2026-04-12 23:17 JST clean45

- `clean44` result from `teraterm_2026-04-12_231415.log`: hit `0x100DE420` with `X8=2`.
- Meaning: execution is in the allocation/list scan path, but this exception dump does not include `X9`, so the global list/table pointer itself was not directly visible.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE428_or_100DE450.clean45`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_231705.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE428 -> UDF`
  - `0x100DE450 -> UDF`
- Meaning:
  - hit `0x100DE428`: list/table pointer was nonzero and `X0` should hold the loaded entry pointer for index 2
  - hit `0x100DE450`: list/table pointer was null, so the code took the no-list path

## 2026-04-12 23:20 JST clean46

- `clean45` result from `teraterm_2026-04-12_231902.log`: hit `0x100DE428`, not `0x100DE450`, with `X0=0` and `X8=2`.
- Meaning: the global list/table pointer is non-null, but entry index 2 is null.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE42C_or_100DE460.clean46`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_232023.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE42C -> UDF`
  - `0x100DE460 -> UDF`
- Meaning:
  - hit `0x100DE42C`: a later list entry is non-null; read `X0` as the entry pointer and `X8` as the index
  - hit `0x100DE460`: list scan reached the loop-exit test; read `X0`/`X8` to see whether entries 2..6 were all null

## 2026-04-12 23:23 JST clean47

- `clean46` result from `teraterm_2026-04-12_232204.log`: hit `0x100DE460` with `X0=0` and `X8=7`.
- Meaning: list entries index 2..6 did not yield a usable entry; original code would branch to `0x100DE4B8` fallback/allocation path.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE524_or_100DE590.clean47`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260412_232335.md`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE524 -> UDF`
  - `0x100DE590 -> UDF`
- Meaning:
  - hit `0x100DE524`: fallback allocation helper `0x101DEAC8(0x90)` returned; read `X0`
  - hit `0x100DE590`: usable block acquired; read `X0` as block pointer

## 2026-04-13 02:22 JST clean48

- `clean47` result from `teraterm_2026-04-12_232923.log`: hit `0x100DE590`, not `0x100DE524`, with `X0=0x40002AD0`.
- Meaning: fallback/free-list path produced a usable block pointer; original code should derive `x20=x24+0x10` and continue to object initialization.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE564_or_100DE5A8.clean48`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_022259.md`
- SHA256: `7F53D52056CC15E929DE50EE3858758C0F66C39B28F4EC9DDF29E3E6AB418402`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE564 -> UDF`
  - `0x100DE5A8 -> UDF`
- Meaning:
  - hit `0x100DE5A8`: `x20` is non-null and object/block initialization is reached
  - hit `0x100DE564`: `x20` is null and the failure path is taken

## 2026-04-13 02:33 JST clean49

- `clean48` result from `teraterm_2026-04-13_023225.log`: hit `0x100DE5A8`, not `0x100DE564`, with `X0=0x40002AD0` and `X24=0x40002AD0`.
- Meaning: the fallback/free-list block is active and the object/block initialization path is reached.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE5FC_or_100DE728.clean49`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_023332.md`
- SHA256: `2A132FB436FD46F591F979695BC1A29A13220C8452544D6FF59ADB8C5BBDD1CB`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE5FC -> UDF`
  - `0x100DE728 -> UDF`
- Meaning:
  - hit `0x100DE5FC`: global gate enters the second/smaller block scan-allocation path
  - hit `0x100DE728`: skips that path or reaches its later fallback/finalization block

## 2026-04-13 02:51 JST clean50

- `clean49` result from `teraterm_2026-04-13_025010.log`: hit `0x100DE5FC`, not `0x100DE728`, with `X0=0x40002AD0` and `X8=0`.
- Meaning: the global gate enters the second/smaller block scan-allocation path.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE61C_or_100DE644.clean50`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_025109.md`
- SHA256: `837BF4F57A1C560DD9328ABF497B482DF28888EB587E587EDF440AD593604DA4`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE61C -> UDF`
  - `0x100DE644 -> UDF`
- Meaning:
  - hit `0x100DE61C`: second list/table pointer is non-null and index 0 entry was loaded; read `X0`
  - hit `0x100DE644`: second list/table pointer is null; no-list path

## 2026-04-13 02:55 JST clean51

- `clean50` result from `teraterm_2026-04-13_025412.log`: hit `0x100DE61C`, not `0x100DE644`, with `X0=0x40002AB0` and `X8=0`.
- Meaning: the second list/table pointer is non-null and index 0 has a non-null entry.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE658_or_100DE6AC.clean51`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_025516.md`
- SHA256: `7A6A08B8CA1F28AE1D8938D2F3F39A3007A55FF8317B0F45293220688885DFB5`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE658 -> UDF`
  - `0x100DE6AC -> UDF`
- Meaning:
  - hit `0x100DE658`: second list entry validated as usable; read `X0` as accepted entry/block pointer
  - hit `0x100DE6AC`: scan failed to produce a usable entry and falls to fallback/allocation

## 2026-04-13 07:37 JST clean52

- `clean51` result from `teraterm_2026-04-13_073611.log`: hit `0x100DE658`, not `0x100DE6AC`, with `X0=0x40002AB0` and `X8=1`.
- Meaning: second list entry `0x40002AB0` passed local validation and is accepted for helper `0x101DEA18`.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE65C_or_100DE70C.clean52`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_073757.md`
- SHA256: `1C49A665681A129512D04335F97945A17CEEA6E549A64AAC27FDBF884D1617ED`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE65C -> UDF`
  - `0x100DE70C -> UDF`
- Meaning:
  - hit `0x100DE65C`: helper `0x101DEA18` returned; read `X0`
  - hit `0x100DE70C`: helper returned non-null and later validation reached the accepted/fallback merge point; read `X0`

## 2026-04-13 07:41 JST clean53

- `clean52` result from `teraterm_2026-04-13_074008.log`: hit `0x100DE65C`, not `0x100DE70C`, with `X0=0x40002AB0`.
- Meaning: helper `0x101DEA18` returned non-null and preserved/returned the accepted entry pointer.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE694_or_100DE70C_or_100DE784.clean53`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_074125.md`
- SHA256: `32429F4D08C96AB08F60CEF65D8F36C86852DEA5071D35B37471F3C5A91875EE`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE694 -> UDF`
  - `0x100DE70C -> UDF`
  - `0x100DE784 -> UDF`
- Meaning:
  - hit `0x100DE694`: list integrity check failed and cleanup helper would run
  - hit `0x100DE70C`: accepted pointer reaches the non-split/merge path
  - hit `0x100DE784`: accepted pointer reaches the split-block path

## 2026-04-13 21:22 JST clean54

- `clean53` result from `teraterm_2026-04-13_211915.log`: hit `0x100DE70C`, not `0x100DE694` or `0x100DE784`, with `X0=0x40002AB0` and `X8=0x40002AD0`.
- Meaning: accepted pointer reaches the non-split/merge path; cleanup and split-block paths were not taken.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE75C_or_100DE7C0.clean54`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_212212.md`
- SHA256: `4D172B7A453DAA270350233EC9207D9C13B15F5D797CF2013AE6138371C89C92`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE75C -> UDF`
  - `0x100DE7C0 -> UDF`
- Meaning:
  - hit `0x100DE7C0`: `x24` is non-null and object initialization continues
  - hit `0x100DE75C`: `x24` is null and failure path is taken

## 2026-04-13 21:28 JST clean55

- `clean54` result from `teraterm_2026-04-13_212532.log`: hit `0x100DE7C0`, not `0x100DE75C`, with `X0=0x40002AB0`, `X24=0x40002AC0`, and `X8=0`.
- Meaning: `x24` is non-null and object initialization continues; immediate failure path was not taken.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE830_or_100DE990.clean55`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_212827.md`
- SHA256: `09B4F15940007C5EAF9423E4E8BC99252E1E57DCA1781A04DF363D6EDE4D018D`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE830 -> UDF`
  - `0x100DE990 -> UDF`
- Meaning:
  - hit `0x100DE830`: third scan/allocation path is entered
  - hit `0x100DE990`: third scan/allocation path is skipped

## 2026-04-13 21:32 JST clean56

- `clean55` result from `teraterm_2026-04-13_213116.log`: hit `0x100DE830`, not `0x100DE990`, with `X0=0x40002AB0`, `X24=0x40002AC0`, and `X8=0`.
- Meaning: third scan/allocation path is entered.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE84C_or_100DE874.clean56`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_213206.md`
- SHA256: `BDEA78028EF34BA9BCFC7886A8567B666189C9804CD99A0FBE281FC5B4E96FF3`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE84C -> UDF`
  - `0x100DE874 -> UDF`
- Meaning:
  - hit `0x100DE84C`: third list/table pointer is non-null and index 1 entry was loaded; read `X0`
  - hit `0x100DE874`: third list/table pointer is null; no-list path

## 2026-04-13 22:13 JST clean57

- `clean56` result from `teraterm_2026-04-13_221119.log`: hit `0x100DE84C`, not `0x100DE874`, with `X0=0`, `X8=1`, `X24=0x40002AC0`, and `X19=0x23CE62000`.
- Meaning: third list/table pointer is non-null, but index 1 entry is null; original execution would keep scanning later indexes.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE850_or_100DE884.clean57`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_221328.md`
- SHA256: `597298217E8F4A328ED88532A1DFF02DE5634A6CF7682F750BC1885BAFE8EC4F`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE850 -> UDF`
  - `0x100DE884 -> UDF`
- Meaning:
  - hit `0x100DE850`: a later third-list index produced a non-null candidate entry; read `X0` and `X8`.
  - hit `0x100DE884`: third-list scan reached the post-loop empty/fallback branch; likely no usable entry in indexes 1..6.

## 2026-04-13 22:18 JST clean58

- `clean57` result from `teraterm_2026-04-13_221526.log`: hit `0x100DE884`, not `0x100DE850`, with `X0=0`, `X8=7`, `X24=0x40002AC0`, and `X19=0x23CE62000`.
- Meaning: third-list scan exhausted indexes 1..6 without a usable candidate and is about to take the empty/fallback path.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE90C_or_100DE940.clean58`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_221804.md`
- SHA256: `D63AEFA2B7980607B8EE35929705E05BFC753ABE984A3FD06834AC07F10E981D`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE90C -> UDF`
  - `0x100DE940 -> UDF`
- Meaning:
  - hit `0x100DE90C`: existing-list block can provide the 0x40-byte allocation.
  - hit `0x100DE940`: existing-list allocation was unavailable or failed bounds checks; helper `0x101DEAC8` would be called for a 0x40-byte allocation.

## 2026-04-13 22:20 JST clean59 generated, not staged

- `clean58` result from `teraterm_2026-04-13_222041.log`: hit `0x100DE90C`, not `0x100DE940`, with `X0=0x40002B60`, `X8=0x4007EFB8`, `X24=0x40002AC0`, and `X19=0x23CE62000`.
- Meaning: existing-list allocation can provide the 0x40-byte block; fresh helper allocation was not needed.
- Generated probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE9E0_or_100DE75C.clean59`
- Staging status: staged later after `F:` was reinserted; snapshot cutoff `analysis/media_snapshots/windows_media_F_20260413_222327.md`.
- SHA256: `FF9A55F6B2B0CFABB321DC18348BEEB50D5899A47F06E9DE311D49241BF84472`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE9E0 -> UDF`
  - `0x100DE75C -> UDF`
- Meaning:
  - hit `0x100DE9E0`: helper `0x100DE0A8` returned after object initialization; read `W0`/`X0`, `X21`, and `X25`.
  - hit `0x100DE75C`: `x21` was null and the failure path was taken before object initialization.

## 2026-04-13 22:27 JST clean60

- `clean59` result from `teraterm_2026-04-13_222454.log`: hit `0x100DE9E0`, not `0x100DE75C`, with `X0=0`, `X8=0`, `X24=0x40002AC0`, and `FP18 +30=0x40002B60`.
- Meaning: helper `0x100DE0A8` returned success-looking status (`W0=0`). `X25=0` at this stop is before the `ldr x25, [sp,#0x28]` instruction, so it is not the helper output pointer yet.
- New active probe: `BOOTAA64.bypass_100DE254_100DE25C_force_w23_match_x27_count2_stop_100DE9EC_or_100DE760.clean60`
- Snapshot cutoff: `analysis/media_snapshots/windows_media_F_20260413_222702.md`
- SHA256: `ACF2D5FD09285940633AB5B3CAAB32A6850EE07AA1AD0476CAED863258D453A9`
- Patch behavior:
  - `0x100DE230 -> mov w23,#1`
  - `0x100DE254 -> NOP`
  - `0x100DE25C -> NOP`
  - `0x100DE284 -> mov x27,#2`
  - `0x100DE9EC -> UDF`
  - `0x100DE760 -> UDF`
- Meaning:
  - hit `0x100DE9EC`: helper status was non-error and execution entered object registration; read `X25` and `X21`.
  - hit `0x100DE760`: helper status was an error and execution entered cleanup.
