# Raspberry Pi Delta Candidates

Date: 2026-04-02

## Comparison Basis

- A733 worktree:
  - `D:\Projects\porta-a733-uefi`
  - `D:\Projects\porta-a733-bringup`
  - latest firmware stamp: `2026-04-02T02:16:33+0900`
  - latest observed stop: `D:\Projects\PortaRe0\software\log\teraterm.log`
- Raspberry Pi reference clones:
  - `D:\Projects\reference\RPi4` at `3dbcf5d0d591c4f5560778a0900e014655e70c5e`
  - `D:\Projects\reference\rpi5-uefi` at `a6135b06d661b5f11bbf4bd742b42a1919b264dc`
  - `D:\Projects\reference\RPi-Windows-Drivers` at `b19eb98bd8a354349d47b0801360f72d0a9ac04a`

## Current A733 Position

- External `BOOTAA64.EFI` loads and runs.
- `SetupMode`, `SecureBoot`, `OpenProtocol`, `GetMemoryMap`, `SetWatchdogTimer`, console `SetState` all succeed.
- Current silent stop is after `bootmgfw` issues `gRT->GetTime()`.
- `GetTime()` itself now returns successfully with a synthetic implementation.
- A/B patching shows the remaining stop is in `bootmgfw`'s runtime-service restore path, around the internal context restore block that rewrites `HCR_EL2`, `TTBR0_EL1`, `TTBR1_EL1`, `MAIR_EL1`, `TCR_EL1`, `SCTLR_EL1`, and `VBAR_EL1`.

## Ranked Delta Candidates

### 1. EFI Memory Attribute Protocol / MAT policy mismatch

Why it matters:
- `rpi5-uefi` ships a dedicated driver at `Platform/RaspberryPi/Drivers/MemoryAttributeManagerDxe`.
- That driver can uninstall `gEfiMemoryAttributeProtocolGuid` because some loaders/shims fault when they use it incorrectly.
- `rpi5-uefi/README.md` explicitly documents sync exceptions tied to the `EFI Memory Attribute Protocol`.
- A733 currently has no equivalent manager and has been doing ad-hoc MAT experiments.

Evidence:
- `D:\Projects\reference\rpi5-uefi\edk2-platforms\Platform\RaspberryPi\Drivers\MemoryAttributeManagerDxe\MemoryAttributeManagerDxe.c`
- `D:\Projects\reference\rpi5-uefi\edk2-platforms\Platform\RaspberryPi\RPi5\RPi5.dsc`
- `D:\Projects\PortaRe0\software\log\teraterm.log`

Suggested action:
- Add a minimal A733 DXE driver that can uninstall `EFI_MEMORY_ATTRIBUTE_PROTOCOL`.
- Test with protocol disabled by default, then A/B against protocol enabled.

### 2. Runtime-service return CPU/MMU context mismatch

Why it matters:
- Current `bootmgfw` reverse engineering shows the failing path is not inside `GetTime()` but in the caller-side restore code after the runtime service returns.
- The restore block touches EL and MMU state directly.
- This is consistent with a firmware contract mismatch rather than a missing pre-boot protocol.

Evidence:
- `D:\Projects\porta-a733-bringup\build\patch_bootaa64.py`
- `D:\Projects\PortaRe0\software\log\teraterm.log`
- `D:\Projects\reference\rpi5-uefi\edk2-platforms\Platform\RaspberryPi\Library\RpiRtcLib\RpiRtcLib.c`

Suggested action:
- Compare A733 runtime-driver library choices against Pi.
- Reduce non-runtime-safe side effects in runtime path.
- Instrument or gate the restore-path-adjacent code using `bootmgfw` A/B only after candidate 1 is tested.

### 3. Variable/NV-store semantics gap

Why it matters:
- Pi platforms include `VarBlockServiceDxe` and FTW-backed variable plumbing ahead of `VariableRuntimeDxe`.
- A733 currently uses `PcdEmuVariableNvModeEnable|TRUE` with no platform FVB/file-backed variable layer.
- Windows is already interacting with Secure Boot variables and `WindowsBootChainSvnCheckStatus`.

Evidence:
- `D:\Projects\reference\RPi4\edk2-platforms\Platform\RaspberryPi\Drivers\VarBlockServiceDxe\VarBlockServiceDxe.c`
- `D:\Projects\reference\rpi5-uefi\edk2-platforms\Platform\RaspberryPi\RPi5\RPi5.dsc`
- `D:\Projects\porta-a733-uefi\src\edk2\Platform\Allwinner\A733Pkg\A733Pkg.dsc`

Suggested action:
- If candidate 1 fails, add a minimal platform var block service or other persistent variable shim before revisiting `SetVariable()`-heavy paths.

### 4. Protocol surface gap versus Pi firmware

Why it matters:
- Pi firmware includes working RNG, proper RTC backend, richer config DXE, and a more complete Windows-facing setup.
- A733 still relies on a synthetic GOP, synthetic RTC behavior, and no RNG driver in firmware.

Evidence:
- `D:\Projects\reference\rpi5-uefi\README.md`
- `D:\Projects\reference\rpi5-uefi\edk2-platforms\Platform\RaspberryPi\RPi5\RPi5.dsc`
- `D:\Projects\porta-a733-uefi\src\edk2\Platform\Allwinner\A733Pkg\A733Pkg.dsc`

Suggested action:
- Treat these as second-wave tasks after the runtime-service contract is fixed.

### 5. Post-UEFI driver ecosystem gap

Why it matters:
- Pi has `RPi-Windows-Drivers` and the older `raspberrypi/windows-drivers` BSP lineage.
- A733 has no equivalent Windows driver pack yet.
- This is a later blocker, not the current one.

Evidence:
- `D:\Projects\reference\RPi-Windows-Drivers`

Suggested action:
- Defer until `winload` or later Windows phases are reached.

### 6. ACPI PCIe contract gap (`MCFG` / `PCI0`)

Why it matters:
- The current A733 ACPI set only exposes `DSDT/FADT/GTDT/MADT/SPCR`.
- There is no `MCFG`, and `DSDT` has no `PCI0` root bridge device.
- Earlier `bootmgfw` error-path work showed `0x4746434D` (`MCFG`) on the stack while the failure path was being assembled.
- Vendor DT for the Cubie A7Z exposes a PCIe RC with:
  - `reg = <0x00 0x6000000 0x00 0x480000>` (`dbi`)
  - `bus-range = <0x00 0xff>`
  - `ranges = ... 0x20000000 ... 0x01000000 ... 0x21000000 ... 0x01000000 ... 0x22000000 ... 0x06000000`

Evidence:
- `D:\Projects\porta-a733-uefi\src\edk2\Platform\Allwinner\A733Pkg\AcpiTables\AcpiTables.inf`
- `D:\Projects\porta-a733-uefi\src\edk2\Platform\Allwinner\A733Pkg\AcpiTables\Dsdt.asl`
- `D:\Projects\PortaRe0\software\roms\_work\current_F_vendor.dts`
- `D:\Projects\PortaRe0\software\analysis\ref_quartz64_uefi\edk2-rockchip\Platform\Rockchip\Rk356x\AcpiTables\Mcfg.aslc`
- `D:\Projects\PortaRe0\software\analysis\ref_quartz64_uefi\edk2-rockchip\Platform\Rockchip\Rk356x\AcpiTables\Pcie2x1.asl`

Suggested action:
- Add a minimal `Mcfg.aslc` to A733 ACPI tables.
- Add a minimal `PCI0` root bridge to `Dsdt.asl` with the vendor DT windows.
- Keep this as an ACPI-only experiment first; do not commit to a full PCI host bridge implementation until the Windows error moves.

Result on 2026-04-02:
- Implemented `MCFG` and a minimal `PCI0` ACPI root bridge in A733 firmware.
- UART confirms ACPI install sequence now includes `Table sig = MCFG` and `Table sig = DSDT` with the new build stamp `Apr  2 2026 13:52:07`.
- The visible Windows Boot Manager failure remains unchanged:
  - `File: \EFI\Microsoft\Boot\BCD`
  - `Status: 0xc000000d`
- Conclusion: missing `MCFG/PCI0` alone was not the sole blocker, but the platform ACPI contract is now less incomplete.

Follow-up on 2026-04-03:
- Re-ran the old `bootmgfw` compare trap at `0x101AFA14` with `MCFG/PCI0` now present.
- The result is unchanged from the pre-`MCFG` run:
  - `X0 = 0xC0000225`
  - `X1 = 0x15000047`
  - `X8 = 0`
- `0x15000047` maps to the official BCD library integer element `ConfigAccessPolicy`.
- Conclusion: `MCFG/PCI0` did not change this failure path. The next A/B is now on the installer `BCD` itself, not firmware ACPI alone.

## Selected Immediate Action

Implement candidate 1 first:

- Add `A733MemoryAttributeManagerDxe`
- Disable `EFI_MEMORY_ATTRIBUTE_PROTOCOL` by default through a build-time PCD
- Rebuild firmware
- Re-test current `bootmgfw` path with the same UART instrumentation
