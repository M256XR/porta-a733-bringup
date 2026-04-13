# Automation Tooling (2026-04-08)

## Added scripts

- [classify_bootaa64_state.py](D:\Projects\porta-a733-bringup\build\classify_bootaa64_state.py)
  - classifies a mounted `BOOTAA64.EFI` against:
    - `BOOTAA64.original.EFI`
    - `BOOTAA64.fixed.EFI`
    - `BOOTAA64.PATCH.txt`
    - known patch sites from [patch_bootaa64.py](D:\Projects\porta-a733-bringup\build\patch_bootaa64.py)
- [snapshot_windows_media.ps1](D:\Projects\porta-a733-bringup\build\snapshot_windows_media.ps1)
  - now includes:
    - file hashes
    - marker preview
    - startup preview
    - `BOOTAA64` classification
    - marker-hash mismatch detection
- [stage_windows_loader_variant.py](D:\Projects\porta-a733-bringup\build\stage_windows_loader_variant.py)
  - stages one chosen EFI to:
    - `EFI\BOOT\BOOTAA64.EFI`
    - `EFI\Microsoft\Boot\bootmgfw.efi`
    - `EFI\BOOT\BOOTAA64.PATCH.txt`
    - `startup.nsh`
- [prepare_windows_debug_run.ps1](D:\Projects\porta-a733-bringup\build\prepare_windows_debug_run.ps1)
  - orchestration:
    - archive Tera Term logs
    - pre-stage media snapshot
    - optional loader staging
    - post-stage media snapshot

## Current practical use

### 1. Classify the currently mounted media

```powershell
python D:\Projects\porta-a733-bringup\build\classify_bootaa64_state.py F:\EFI\BOOT\BOOTAA64.EFI --marker F:\EFI\BOOT\BOOTAA64.PATCH.txt
```

### 2. Snapshot the current mounted media

```powershell
powershell -ExecutionPolicy Bypass -File D:\Projects\porta-a733-bringup\build\snapshot_windows_media.ps1 -Root F:\
```

### 3. Stage a known variant and keep marker/startup in sync

```powershell
python D:\Projects\porta-a733-bringup\build\stage_windows_loader_variant.py ^
  --target-root F:\ ^
  --source-efi D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI ^
  --patch-name claude_fixed ^
  --startup-mode bootmgfw_only
```

### 4. Archive + snapshot + stage + snapshot in one run

```powershell
powershell -ExecutionPolicy Bypass -File D:\Projects\porta-a733-bringup\build\prepare_windows_debug_run.ps1 ^
  -TargetRoot F:\ ^
  -StageSourceEfi D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI ^
  -PatchName claude_fixed ^
  -StartupMode bootmgfw_only
```

## Why this exists

The current live `F:\` media is a mixed artifact and the marker file is stale.

That means any future log needs:

1. archived serial log
2. exact mounted media snapshot
3. exact staged loader hash
4. exact startup policy

These scripts make that state explicit instead of relying on memory.
