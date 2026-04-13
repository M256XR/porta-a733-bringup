# Codex Transcript Findings (2026-04-08)

## Scope

Source:
- `D:\Projects\PortaRe0\software\log\codex.txt`

Generated raw extraction:
- `D:\Projects\porta-a733-bringup\analysis\CODEX_PATCH_TIMELINE_FROM_LOG.md`

This note keeps only the findings that materially change how current logs should be interpreted.

## Findings

### 1. Apr 3-6 logs are not "clean Windows loader" runs

`codex.txt` shows repeated live-media replacement of both:
- `F:\EFI\BOOT\BOOTAA64.EFI`
- `F:\EFI\Microsoft\Boot\bootmgfw.efi`

Examples:
- `codex.txt:8247`
- `codex.txt:7864`
- `codex.txt:7936`

Meaning:
- Many `teraterm.log` runs from this period are observations of patched Windows loaders, not only UEFI changes.

### 2. `0x1003BA6C` was explicitly identified as a `No mapping` regression

Transcript statement:
- `codex.txt:8517`

Relevant patch recipe:
- [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py:3802)

This recipe:
- NOPs reporting helper 1
- NOPs screen helper
- then breaks immediately after the x22 cleanup helper returns (`0x1003BA6C`)

Meaning:
- When `No mapping` appears in this phase, a patched loader-side cleanup path is a first-class suspect.

### 3. A safer recipe was added by NOPing the cleanup helper itself

Transcript statements:
- `codex.txt:8660`
- `codex.txt:8661`
- `codex.txt:8998`

Relevant patch recipe:
- [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py:3862)

This safer recipe:
- keeps reporting helper 1 NOP
- keeps screen helper NOP
- additionally NOPs the x22 cleanup helper call at `0x1003BA64`
- then breaks at `0x1003BA68`

Meaning:
- Codex already found one loader-side cleanup call whose presence correlated with the `No mapping` regression.

### 4. An even later safer recipe also NOPed the global cleanup helper

Transcript statement:
- `codex.txt:8998`

Relevant patch recipe:
- [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py:3927)

This recipe:
- NOPs `0x1003BA54`
- NOPs `0x1003BA58`
- NOPs `0x1003BA64`
- NOPs `0x1003BAB0`
- breaks at `0x1003BAB4`

Meaning:
- The investigation had already moved beyond the first cleanup helper and into later alt-path cleanup/gating.

### 5. Reverting to an older stable deep-stop recipe reportedly removed `No mapping`

Transcript statement:
- `codex.txt:6642`

Meaning:
- The transcript claims `No mapping` disappeared after moving back to an older, known-good deep-stop variant.
- This strongly argues against treating every `No mapping` as a firmware-only regression.

### 6. Boot path problems and deep loader patches were both active at once

Transcript statement:
- `codex.txt:5321`
- `codex.txt:5322`
- `codex.txt:5323`

Meaning:
- In at least one run:
  - `EfiBootManagerBoot()` launched `BOOTAA64.EFI` and got `No mapping`
  - Shell then found `bootmgfw.efi` and that also returned `No mapping`
  - `BOOTAA64.EFI` was retried again
- So some logs are contaminated by both:
  - patched loader behavior
  - launch-path / shell fallback / retry behavior

### 7. `EfiBootManagerBoot()` change is part of the current story

Transcript statements:
- `codex.txt:4823`
- `codex.txt:4881`
- `codex.txt:4905`
- `codex.txt:5072`

Current source:
- [PlatformBootManagerLib.c](D:\Projects\porta-a733-uefi\src\edk2\Platform\Allwinner\A733Pkg\Library\PlatformBootManagerLib\PlatformBootManagerLib.c:392)

Meaning:
- The current firmware path using `EfiBootManagerBoot()` is not background noise. It was intentionally changed during the same investigation window while `No mapping` was being chased.

## Practical interpretation

The current investigation must keep these three causes separate:

1. firmware-side regression in `porta-a733-uefi`
2. loader-side regression from patched `BOOTAA64.EFI` / `bootmgfw.efi`
3. launch-path contamination from removable boot + `startup.nsh` retry

## Working priority

1. Verify whether live media is running original or patched Windows loaders
2. Verify whether the run is single-start or shell retry contaminated
3. Only then compare UEFI firmware builds for a genuine firmware regression
