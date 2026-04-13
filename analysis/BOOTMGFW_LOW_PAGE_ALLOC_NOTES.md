# bootmgfw low-page allocation notes

## Static result

- `D:\Projects\PortaRe0\software\build\bootmgfw-win.efi` and `D:\Projects\porta-a733-bringup\build\BOOTAA64.original.EFI` are byte-identical.
- In the function containing VA `0x1003A25C`, `bootmgfw` does:
  - `ldr x8, #0x1003AB28`
  - literal value at `0x1003AB28` is `0x0000000000102000`
  - `str x8, [sp, #0x70]`
  - `mov w0, #2`
  - `mov w1, #2`
  - `mov x2, #1`
  - `add x3, sp, #0x70`
  - `ldr x8, [x8, #0x28]`
  - `blr x15`
- That call sequence matches `AllocatePages (AllocateAddress, EfiLoaderData, 1, &0x102000)`.

## Existing runtime evidence

- The memory-map dump already shows `Type=7 Start=0x102000 Pages=0x1 Attr=0xE` before the first `BOOTAA64.EFI` start.
- In the same boot session:
  - `\EFI\BOOT\BOOTAA64.EFI` starts first at `2026-04-07 16:20:21`.
  - it reaches `AllocatePages Type=2 Size=0x1 -> Success Caller=23CCCE25C` at `2026-04-07 16:20:23`.
  - the platform then falls back to `UEFI Shell`.
  - `startup.nsh` launches `\EFI\Microsoft\Boot\bootmgfw.efi`.
  - the second start hits `ConvertPages: Incompatible memory types, the pages to allocate have been allocated` and `AllocatePages Type=2 Size=0x1 -> Not Found Caller=23CB7325C`.

## Interpretation

- The `0x102000` page is not inherently unmapped.
- The page is available for the first `bootmgfw` instance and can be allocated successfully.
- The later failure is consistent with the same `bootmgfw` binary being started again after the first failed attempt already claimed that fixed page.
- This means existing logs are mixing two separate attempts:
  - automatic removable-media boot via `\EFI\BOOT\BOOTAA64.EFI`
  - shell-driven retry via `startup.nsh` and `\EFI\Microsoft\Boot\bootmgfw.efi`

## Practical consequence

- For low-page debugging, avoid a same-session retry path that runs both binaries.
- The easiest clean tests are:
  - boot `\EFI\Microsoft\Boot\bootmgfw.efi` directly from Shell with `EFI\BOOT\BOOTAA64.EFI` absent
  - or reboot between the removable-media attempt and the Shell attempt
  - or add new firmware logging and inspect the first attempt only

## Tooling changes in this repo

- `build/analyze_bootaa64_xrefs.py` now accepts `--address` without requiring string patterns and resolves ARM64 literal loads inline.
- `build/install_windows_installer.py` now supports:
  - `--skip-bootaa64` to avoid installing the removable-media path during Shell-driven bring-up
  - `--with-bootaa64-fallback` if the old `startup.nsh` fallback is still desired
- `build/startup_fs1_windows.nsh` now launches `bootmgfw.efi` directly and only reports the presence of `BOOTAA64.EFI`.

## Repro command

```powershell
python D:\Projects\porta-a733-bringup\build\analyze_bootaa64_xrefs.py `
  D:\Projects\PortaRe0\software\build\bootmgfw-win.efi `
  --address 0x1003A25C
```
