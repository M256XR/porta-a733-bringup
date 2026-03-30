@echo -off
if exist fs1:\EFI\BOOT\BOOTAA64.EFI then
  fs1:\EFI\BOOT\BOOTAA64.EFI
endif
echo Windows installer BOOTAA64.EFI not found on fs1:.
