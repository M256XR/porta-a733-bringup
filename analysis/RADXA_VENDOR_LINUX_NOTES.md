# Radxa Vendor Linux Notes

## Source Artifacts

- Raw image: not committed; expected at `D:\Projects\porta-a733-bringup\roms\_work\radxa-cubie-a7z_bullseye_kde_b1.output_512.img`
- Extracted boot assets: `D:\Projects\porta-a733-bringup\roms\_work\radxa_vendor_boot`
- Vendor DTB copy: `D:\Projects\porta-a733-bringup\roms\_work\radxa_vendor_boot\sun60i-a733-cubie-a7z.dtb`
- Vendor extlinux: `D:\Projects\porta-a733-bringup\roms\_work\radxa_vendor_boot\extlinux.conf`
- Vendor kernel config: `D:\Projects\porta-a733-bringup\roms\_work\radxa_vendor_boot_verify\config-5.15.147-7-a733`

## Boot Command Line

Vendor `extlinux.conf` boots:

- Kernel: `/boot/vmlinuz-5.15.147-7-a733`
- Initrd: `/boot/initrd.img-5.15.147-7-a733`
- DTB dir: `/usr/lib/linux-image-5.15.147-7-a733/`
- Key cmdline pieces:
  - `console=ttyAS0,115200n8`
  - `rootwait`
  - `clk_ignore_unused`
  - `earlycon`
  - `console=tty1`
  - `irqchip.gicv3_pseudo_nmi=0`

## Important Config Differences

Vendor kernel is **not** the same stack as Ubuntu mainline.

- `CONFIG_AW_MMC=y`
- `CONFIG_AW_DRM=y`
- `CONFIG_AW_DRM_DE=y`
- `CONFIG_AW_DRM_TCON=y`
- `CONFIG_AW_DRM_TCON_TOP=y`
- `CONFIG_AW_DRM_HDMI_TX=y`
- `CONFIG_AW_DRM_HDMI20=y`
- `CONFIG_AW_DRM_PHY=y`

Mainline-style pieces we were using are absent:

- `# CONFIG_MMC_SUNXI is not set`
- `# CONFIG_DRM_SUN4I is not set`
- `# CONFIG_DRM_DISPLAY_CONNECTOR is not set`
- `# CONFIG_DRM_SIMPLEDRM is not set`

This means "working on vendor image" does **not** imply our Ubuntu mainline bring-up is close. The driver model is materially different.

## Vendor DTB Shape

The vendor DTB is vendor/BSP style rather than mainline/H6 style.

- DRM root:
  - `compatible = "allwinner,sunxi-drm"`
- Display engine:
  - `de@5000000`
  - `compatible = "allwinner,display-engine-v352"`
- MMC:
  - `sdmmc@4020000`
  - `compatible = "allwinner,sunxi-mmc-v5p3x"`
- CCU:
  - `ccu@2002000`
- Pinctrl:
  - `pinctrl@2000000`
- GIC:
  - `interrupt-controller@3400000`
- Timer:
  - `timer_arch`

This differs substantially from the hand-built mainline-ish DT we currently generate in `build/install_linux_installer.py`.

## Practical Takeaway

Use vendor artifacts in two ways:

1. Baseline comparison for clocks, resets, pinctrl, and node placement.
2. Optional separate UEFI boot experiment with vendor kernel/initrd/dtb, if we also prepare a matching vendor rootfs.

Do not assume that copying vendor DT nodes directly into the Ubuntu mainline path will be sufficient. The kernel driver stack differs.

