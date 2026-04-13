# Windows Media Snapshot

- root: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e
- captured_at: 2026-04-08 16:07:23

## EFI\BOOT\BOOTAA64.EFI

- status: present
- full_path: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\BOOT\BOOTAA64.EFI
- length: 3030944
- last_write_time: 2026-04-06 21:32:22
- sha256: 315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16

## EFI\Microsoft\Boot\bootmgfw.efi

- status: present
- full_path: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\Microsoft\Boot\bootmgfw.efi
- length: 3030944
- last_write_time: 2026-04-06 21:32:22
- sha256: 315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16

## EFI\BOOT\BOOTAA64.PATCH.txt

- status: present
- full_path: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\BOOT\BOOTAA64.PATCH.txt
- length: 209
- last_write_time: 2026-04-08 16:07:23
- sha256: C4CA00F4A29C911787C6F50CE7CBD13564E0764E9A9DFA007E79D7592C5E9508
- preview:

~~~text
BOOTAA64_PATCH=prep_test
BOOTAA64_SHA256=315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16
PATCH_VAS=0x1003BA54,0x1003BAB4
SOURCE_EFI=D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI
~~~

## startup.nsh

- status: present
- full_path: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\startup.nsh
- length: 1299
- last_write_time: 2026-04-08 16:07:23
- sha256: 88B2893A7797F0DD0C7B0B4BC4C9ABF503B842F4066941FF21C63F3D2E4A1EB3
- preview:

~~~text
@echo -off
map -r
if exist \EFI\Microsoft\Boot\bootmgfw.efi then
  \EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist \EFI\BOOT\BOOTAA64.EFI then
  echo BOOTAA64.EFI exists on the current volume but startup.nsh is not auto-launching it
endif
if exist fs0:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs0:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs1:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs1:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs2:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs2:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs3:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs3:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs4:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs4:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs5:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs5:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs6:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs6:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs7:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs7:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs8:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs8:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs9:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs9:\EFI\Microsoft\Boot\bootmgfw.efi
endif
echo Windows loader not found on current volume or fs0:fs9:.
~~~

## EFI\Microsoft\Boot\BCD

- status: present
- full_path: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\Microsoft\Boot\BCD
- length: 7
- last_write_time: 2026-04-08 16:07:22
- sha256: E7F639FC897E5D3215BA43DE07428CDEFFE5EE76BAF90ABB8BAB366B07C2F7CB

## BOOTAA64 Classification

~~~text
# BOOTAA64 State

- target: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\BOOT\BOOTAA64.EFI
- sha256: 315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16
- length: 3030944
- original: D:\Projects\porta-a733-bringup\build\BOOTAA64.original.EFI
- original_sha256: 3DCA6D137E7B61E231969D693D9FB86E590DEA066931E686D40221F72D74AC8E
- matches_original: no
- fixed: D:\Projects\porta-a733-bringup\build\BOOTAA64.fixed.EFI
- fixed_sha256: 315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16
- matches_fixed: yes
- marker: C:\Users\yuu\AppData\Local\Temp\prep_run_test_a0fb2fdd5b5745c08e51be9eb0b9183e\EFI\BOOT\BOOTAA64.PATCH.txt
- marker_patch: prep_test
- marker_claimed_hash: 315FBD1FDF8358CB9C6D5A3EE0213C2FB6FAA470C22192F638E08836A96C0E16
- marker_hash_matches_target: yes
- marker_patch_vas: 0x1003BA54,0x1003BAB4

## Diff vs Original
- diff_runs: 11
- file 0x03A3EC-0x03A3EF len=4 va=0x1003AFEC sec=.text
- file 0x03A7EC-0x03A7EF len=4 va=0x1003B3EC sec=.text
- file 0x03A8B0-0x03A8B3 len=4 va=0x1003B4B0 sec=.text
- file 0x03AE54-0x03AE5B len=8 va=0x1003BA54 sec=.text
- file 0x03AE64-0x03AE67 len=4 va=0x1003BA64 sec=.text
- file 0x03AEB0-0x03AEB7 len=8 va=0x1003BAB0 sec=.text
- file 0x1AEE2D-0x1AEE2F len=3 va=0x101AFA2D sec=.text
- file 0x1B4B2C-0x1B4B2F len=4 va=0x101B572C sec=.text
- file 0x1B5BF4-0x1B5BF7 len=4 va=0x101B67F4 sec=.text
- file 0x1CB829-0x1CB82B len=3 va=0x101CC429 sec=.text
- file 0x28D058-0x28D05A len=3 va=0x1028DC58 sec=.text

## Diff vs Fixed
- diff_runs: 0

## Known Patch Sites Changed
- count: 13
- 0x1003AFEC=1f2003d5
- 0x1003B3EC=0b000014
- 0x1003B4B0=0a000014
- 0x1003BA54=1f2003d5
- 0x1003BA58=1f2003d5
- 0x1003BA64=1f2003d5
- 0x1003BAB0=1f2003d5
- 0x1003BAB4=1f2003d5
- 0x101AFA2C=f5031f2a
- 0x101B572C=e0031f2a
- 0x101B67F4=e0031f2a
- 0x101CC428=e0031f2a
- 0x1028DC58=1f2003d5

## Largest Matching Recipe Subsets
- 5 sites: skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428_bypass_configaccesspolicy_error_path
- 4 sites: skip_setvar_all_callers_nop_vbar_restore_skip_null_callback_101cc428
- 2 sites: skip_setvar_all_callers
- 1 sites: skip_setvar_gate_caller
~~~

## Summary

- BOOTAA64.EFI and bootmgfw.efi hashes match
- BOOTAA64.PATCH.txt is present

