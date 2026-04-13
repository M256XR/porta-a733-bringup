# Live Media Loader State (2026-04-08)

## Scope

This note captures what is currently mounted on `F:\` and how it relates to the local `BOOTAA64` variants.

Primary evidence:
- [windows_media_F_20260408_155028.md](D:\Projects\porta-a733-bringup\analysis\media_snapshots\windows_media_F_20260408_155028.md)
- [log.txt](D:\Projects\porta-a733-uefi\log.txt:1892)
- [codex.txt](D:\Projects\PortaRe0\software\log\codex.txt:8998)

## Current F: state

- `F:\EFI\BOOT\BOOTAA64.EFI`
  - SHA256: `5ADF7FF7B06B344113BCF637B14612DDAE09C4528B5E2D7B7109D71CB9BB5DD4`
- `F:\EFI\Microsoft\Boot\bootmgfw.efi`
  - SHA256: `5ADF7FF7B06B344113BCF637B14612DDAE09C4528B5E2D7B7109D71CB9BB5DD4`
- `F:\EFI\BOOT\BOOTAA64.PATCH.txt`
  - claims SHA256: `ECC4895294796478D3298E35AFDE3751DB48F96F378B1A7E158648B24AF47165`
- `F:\startup.nsh`
  - still auto-launches `bootmgfw.efi`
  - then auto-launches `BOOTAA64.EFI`
  - so shell retry contamination is still possible

## Key findings

### 1. The marker is stale

`BOOTAA64.PATCH.txt` says the live media should be the `ECC489...` variant, but the actual EFI files on `F:\` are `5ADF...`.

This means the marker cannot currently be trusted as the source of truth for the mounted media.

### 2. The current live loader is not a single named `patch_bootaa64.py` recipe

Comparing `F:\EFI\BOOT\BOOTAA64.EFI` against `BOOTAA64.original.EFI` shows 14 diff runs spanning 16 patch sites:

- `0x1003AFEC`
- `0x1003B3EC`
- `0x1003B4B0`
- `0x1003B974`
- `0x1003B998`
- `0x1003BA54`
- `0x1003BA58`
- `0x1003BA64`
- `0x1003BAB0`
- `0x1003BAB4`
- `0x1003BAEC`
- `0x101AFA2C`
- `0x101B572C`
- `0x101B67F4`
- `0x101CC428`
- `0x1028DC58`

The current `PATCHES` catalog in [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py) does not contain an exact recipe with this full set.

### 3. The current live loader equals Claude's `fixed` variant plus three more patches

`BOOTAA64.fixed.EFI` from the Claude-side work has SHA256:

- `315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16`

Comparing the current `F:\EFI\BOOT\BOOTAA64.EFI` against `BOOTAA64.fixed.EFI` leaves only three differences:

- `0x1003B974`
- `0x1003B998`
- `0x1003BAEC`

So the current live media is:

- Claude `fixed` 12-group patch base
- plus two later Claude branch-forcing patches
- plus one later Codex deep-stop patch

### 4. Provenance of the three extra patches is known

From [log.txt](D:\Projects\porta-a733-uefi\log.txt:4552) and nearby lines:

- `0x1003B974` was changed from `TBNZ W19,#31,...` to `NOP`
- `0x1003B998` was changed from `TBZ W19,#31,...` to `B 0x3B9BC`

From [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py:3381) and [codex.txt](D:\Projects\PortaRe0\software\log\codex.txt:3797):

- `0x1003BAEC` is the `...break_before_bootmgr_altpath_error_w19_sign_branch` deep-stop site

## Practical interpretation

The current mounted `F:\` media is a mixed artifact:

1. Claude-side 12-group SecureBoot/CI bypass patch set
2. Claude-side follow-up branch forcing at `0x1003B974` and `0x1003B998`
3. Codex-side deep-stop patch at `0x1003BAEC`

That is enough to invalidate any attempt to treat current `F:\` runs as either:

- a clean firmware-only regression, or
- a single coherent loader patch experiment

## What this means for next hardware runs

Before the next boot log is interpreted, the mounted media must be classified first.

Minimum checks:

1. archive `teraterm.log`
2. snapshot `F:\` with `snapshot_windows_media.ps1`
3. record hashes of:
   - `EFI\BOOT\BOOTAA64.EFI`
   - `EFI\Microsoft\Boot\bootmgfw.efi`
   - `EFI\BOOT\BOOTAA64.PATCH.txt`
4. record whether `startup.nsh` still auto-runs both loaders

If the goal is a clean repro, the media should be rebuilt so that:

- `BOOTAA64.PATCH.txt` matches the actual EFI binary
- `startup.nsh` does not retry into a second loader path
- the exact intended loader variant is known up front
