# Vendor Linux Via UEFI Baseline

## Conclusion

`D:\Projects\porta-a733-bringup\log\teraterm.log` is a successful `boot0 -> BL31 -> UEFI -> GRUB -> vendor Linux -> HDMI/Xorg` run, not a Windows run and not a direct vendor boot that bypasses UEFI.

This matters because it gives us one confirmed "UEFI can hand off to an OS and reach vendor HDMI" baseline that should stay separate from the Windows loader experiments.

## Evidence Chain

### 1. Boot ROM and UEFI are both present

- `HELLO! BOOT0 is starting!`
- `UEFI firmware (version  built at 15:35:03 on Mar 27 2026)`

This is enough to say the run went through the custom firmware path, not only vendor boot components.

### 2. GRUB launches a vendor kernel

The log includes a Linux kernel command line with:

- `BOOT_IMAGE=/vendor/vmlinuz-5.15.147-7-a733`
- `root=/dev/mmcblk0p3`
- `console=ttyAS0,115200n8`
- `video=HDMI-A-1:1920x1080@60e`
- `systemd.unit=multi-user.target`
- `porta_runid=20260330-212118`

That matches the generated GRUB config in `build/install_radxa_vendor_linux.py`.

### 3. The vendor HDMI stack is active

The same log later shows:

- `sunxi-hdmi: drm hdmi detect: connect`
- `sunxi-hdmi: drm hdmi mode set: 1920*1080`

This is vendor DRM, not the mainline/simpledrm path.

### 4. Userspace explicitly launches direct Xorg on HDMI

The repo contains a dedicated service/script pair:

- `build/vendor_porta-x11-direct.service`
- `build/vendor_porta-x11-direct.sh`

That script sends `[xdirect]` logs to UART and starts:

- `xinit /usr/bin/porta-x11-session -- /usr/bin/Xorg :0 vt1 ...`

The Tera Term log contains those `[xdirect]` markers, so the service actually ran.

## Reproduction Shape

The current bring-up repo already encodes the known-good vendor path:

- installer/stager: `build/install_radxa_vendor_linux.py`
- default profile: `xorg-direct`
- alternate profile: `graphical-x11`

Relevant behavior in the script:

- profile choices are `xorg-direct` and `graphical-x11`
- default is `xorg-direct`
- `xorg-direct` adds `systemd.unit=multi-user.target`
- it keeps `video=HDMI-A-1:1920x1080@60e`
- it installs and enables `porta-x11-direct.service`

## Practical Use

Treat this baseline as "vendor HDMI through UEFI is known to work once".

Use it for:

1. Verifying that a new UEFI change did not break generic OS handoff.
2. Comparing Windows failures against a known-good non-Windows path.
3. Comparing DTB / rootfs / boot-script assumptions against vendor Linux before changing the Ubuntu path.

Do not use it to conclude that Ubuntu mainline is close. The vendor stack is materially different; see `analysis/RADXA_VENDOR_LINUX_NOTES.md`.

## Useful Commands

Refresh the boot-log inventory:

```powershell
python D:\Projects\porta-a733-bringup\build\summarize_teraterm_boot.py --markdown --output D:\Projects\porta-a733-bringup\analysis\TERATERM_LOG_INVENTORY_20260408.md D:\Projects\porta-a733-bringup\log D:\Projects\PortaRe0\software\log
```

Summarize only the vendor baseline log:

```powershell
python D:\Projects\porta-a733-bringup\build\summarize_teraterm_boot.py D:\Projects\porta-a733-bringup\log\teraterm.log
```
