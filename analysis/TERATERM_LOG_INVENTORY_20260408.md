# Tera Term Log Inventory

| File | Mode | First timestamp | Last timestamp | Key points |
| --- | --- | --- | --- | --- |
| D:/Projects/porta-a733-bringup/log/teraterm.log | vendor_linux_via_uefi | 2026-03-30 12:22:00.669 | 2026-03-30 12:39:31.148 | root=/dev/mmcblk0p3; video=HDMI-A-1:1920x1080@60e; runid=20260330-212118; sunxi-hdmi; porta-x11-direct |
| D:/Projects/PortaRe0/software/log/teraterm.log | uefi_shell_only | 2026-04-07 16:19:21.169 | 2026-04-07 16:21:39.857 | No mapping x9 |
| D:/Projects/PortaRe0/software/log/teraterm1.log | boot_exception | - | - | SyncEx x1 |
| D:/Projects/PortaRe0/software/log/teraterm2.log | uefi_only | - | - | - |
| D:/Projects/PortaRe0/software/log/teraterm3.log | windows_bootmgr | 2026-04-02 18:17:08.148 | 2026-04-02 18:25:08.800 | BCD 0xc000000d |
| D:/Projects/PortaRe0/software/log/teraterm4.log | boot_exception | - | - | SyncEx x1 |
| D:/Projects/PortaRe0/software/log/teraterm5.log | pre_uefi_only | - | - | - |
| D:/Projects/PortaRe0/software/log/teraterm6.log | boot_exception | - | - | SyncEx x1 |
| D:/Projects/PortaRe0/software/log/teraterm7.log | pre_uefi_only | - | - | - |
| D:/Projects/PortaRe0/software/log/teraterm8.log | pre_uefi_only | - | - | - |

## D:/Projects/porta-a733-bringup/log/teraterm.log

- mode: `vendor_linux_via_uefi`
- size_bytes: `1646020`
- timestamps: `2026-03-30 12:22:00.669` -> `2026-03-30 12:39:31.148`
- flags: `boot0=1 bl31=1 uefi=1 grub=1 windows=0 linux=1 vendor_hdmi=1 xdirect=1 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- kernel_root: `/dev/mmcblk0p3`
- kernel_video: `HDMI-A-1:1920x1080@60e`
- vendor_runid: `20260330-212118`
- notable_markers:
  - `L4: boot0`
  - `L53: uefi`
  - `L968: grub`
  - `L970: grub`
  - `L973: grub`
  - `L975: grub`
  - `L1061: kernel command line`
  - `L2962: [2026-03-30 12:29:58.529] [   13.704913][   T71] [drm] sunxi-hdmi: drm hdmi detect: connect`

## D:/Projects/PortaRe0/software/log/teraterm.log

- mode: `uefi_shell_only`
- size_bytes: `213961`
- timestamps: `2026-04-07 16:19:21.169` -> `2026-04-07 16:21:39.857`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=1 exception=0`
- counters: `no_mapping=9 sync_exception=0 elr=0`
- notable_markers:
  - `L4: boot0`
  - `L52: uefi`

## D:/Projects/PortaRe0/software/log/teraterm1.log

- mode: `boot_exception`
- size_bytes: `34992`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=1`
- counters: `no_mapping=0 sync_exception=1 elr=0`
- notable_markers:
  - `L4: boot0`
  - `L54: uefi`
  - `L608: synchronous exception`

## D:/Projects/PortaRe0/software/log/teraterm2.log

- mode: `uefi_only`
- size_bytes: `631284`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- notable_markers:
  - `L4: boot0`
  - `L53: uefi`
  - `L3094: boot0`
  - `L3143: uefi`
  - `L6833: boot0`
  - `L6882: uefi`

## D:/Projects/PortaRe0/software/log/teraterm3.log

- mode: `windows_bootmgr`
- size_bytes: `7406614`
- timestamps: `2026-04-02 18:17:08.148` -> `2026-04-02 18:25:08.800`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=1 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- bcd_statuses: `0xc000000d`
- bcd_files: `\EFI\Microsoft\Boot\BCD`
- notable_markers:
  - `L4: boot0`
  - `L52: uefi`
  - `L1534: windows boot manager`

## D:/Projects/PortaRe0/software/log/teraterm4.log

- mode: `boot_exception`
- size_bytes: `34820`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=1`
- counters: `no_mapping=0 sync_exception=1 elr=0`
- notable_markers:
  - `L4: boot0`
  - `L54: uefi`
  - `L604: synchronous exception`

## D:/Projects/PortaRe0/software/log/teraterm5.log

- mode: `pre_uefi_only`
- size_bytes: `4766`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=0 uefi=0 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- notable_markers:
  - `L28: boot0`

## D:/Projects/PortaRe0/software/log/teraterm6.log

- mode: `boot_exception`
- size_bytes: `34598`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=1 uefi=1 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=1`
- counters: `no_mapping=0 sync_exception=1 elr=0`
- notable_markers:
  - `L4: boot0`
  - `L54: uefi`
  - `L598: synchronous exception`

## D:/Projects/PortaRe0/software/log/teraterm7.log

- mode: `pre_uefi_only`
- size_bytes: `26109`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=0 uefi=0 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- notable_markers:
  - `L28: boot0`
  - `L75: boot0`
  - `L246: boot0`

## D:/Projects/PortaRe0/software/log/teraterm8.log

- mode: `pre_uefi_only`
- size_bytes: `14823`
- timestamps: `-` -> `-`
- flags: `boot0=1 bl31=0 uefi=0 grub=0 windows=0 linux=0 vendor_hdmi=0 xdirect=0 shell=0 exception=0`
- counters: `no_mapping=0 sync_exception=0 elr=0`
- notable_markers:
  - `L28: boot0`
  - `L132: boot0`
