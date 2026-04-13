@echo -off
if exist fs1:\EFI\Microsoft\Boot\bootmgfw.efi then
  fs1:\EFI\Microsoft\Boot\bootmgfw.efi
endif
if exist fs1:\EFI\BOOT\BOOTAA64.EFI then
  echo BOOTAA64.EFI exists on fs1: but this script is not auto-launching it
endif
echo Windows installer bootmgfw.efi not found on fs1:.
