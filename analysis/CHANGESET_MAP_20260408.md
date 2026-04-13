# Change Set Map (2026-04-08)

## Purpose

Claude と Codex の変更箇所、および source / generated / legacy の境界が混ざっているため、
いま調査対象として扱うべきレイヤーを固定する。

## Layer 1: Current firmware repo (`porta-a733-uefi`)

役割:
- A733 UEFI 本体
- SD / boot manager / ACPI / security / platform driver の実装

現在の未コミット変更の中心:
- `build/install_esp_files.py`
- `build/make_sd_image.py`
- `build/write_sd.py`
- `src/edk2/Platform/Allwinner/A733Pkg/Drivers/SdMmcDxe/SunxiSmhcDxe.c`
- `src/edk2/Platform/Allwinner/A733Pkg/Drivers/HeadlessGopDxe/HeadlessGopDxe.c`
- `src/edk2/Platform/Allwinner/A733Pkg/Drivers/SecurityStubDxe/A733SecurityStub.c`
- `src/edk2/Platform/Allwinner/A733Pkg/Library/PlatformBootManagerLib/PlatformBootManagerLib.c`
- `src/edk2/Platform/Allwinner/A733Pkg/Library/PlatformLib/A733Platform.c`
- `src/edk2/Platform/Allwinner/A733Pkg/AcpiTables/*`

高信頼で確認できた変更内容:
- `SunxiSmhcDxe.c`: CMD18 / CMD17 loop の post-DMA D-cache invalidation 追加
- `HeadlessGopDxe.c`: GOP trace 強化と build stamp 追加
- `A733SecurityStub.c`: build stamp 追加
- `PlatformBootManagerLib.c`: `LoadImage` / `StartImage` 直呼びから `EfiBootManagerBoot()` に変更

注意:
- ここは最も「本体動作」を変える層で、回帰の候補も多い。

## Layer 2: WSL edk2 tree (`~/edk2`)

役割:
- upstream edk2 本体に対する DXE instrumentation
- `porta-a733-uefi` repo の外側

現在の未コミット変更:
- `MdeModulePkg/Core/Dxe/DxeMain.h`
- `MdeModulePkg/Core/Dxe/Image/Image.c`
- `MdeModulePkg/Core/Dxe/Mem/Page.c`

高信頼で確認できた変更内容:
- BOOTAA64 / bootmgfw path の watch / heartbeat / protocol trace 追加
- `AllocatePages(AllocateAddress, ...)` 周辺ログ強化
- Memory map dump reset 追加
- LoadFile2 phase trace 追加

注意:
- これは diagnosis 用の別レイヤーで、`porta-a733-uefi` repo の git には乗らない。
- 「本体 repo にない修正」がここにあるため、混線しやすい。

## Layer 3: Current bring-up repo (`porta-a733-bringup`)

役割:
- bootmgfw 静的解析
- Windows / Linux installer staging
- 実験メモとログ運用

現在の未コミット変更:
- `.gitignore`
- `agents/PROGRESS.md`
- `build/analyze_bootaa64_xrefs.py`
- `build/install_windows_installer.py`
- `build/startup_fs1_windows.nsh`
- `agents/teraterm/archive_teraterm_log.ps1`
- `agents/teraterm/archive_teraterm_logs.ps1`
- `agents/teraterm/archive_teraterm_logs.cmd`
- `analysis/BOOTMGFW_LOW_PAGE_ALLOC_NOTES.md`

現在の未追跡ファイルの大半:
- `build/BOOTAA64.*.EFI`
- `build/patch_bootaa64.py`

解釈:
- `build/BOOTAA64.*.EFI` 群は source ではなく generated experiment binary。
- 調査時に参照すべきなのはスクリプトとメモであり、これらの派生 EFI は「結果物」扱いにする。

高信頼で確認できた最近の変更内容:
- `analyze_bootaa64_xrefs.py`: `--address` 単独解析と literal load 表示を追加
- `install_windows_installer.py`: `--skip-bootaa64` と Shell 直行向け startup 生成を追加
- `startup_fs1_windows.nsh`: `bootmgfw.efi` 優先、`BOOTAA64.EFI` は存在表示のみ
- `agents/teraterm/*`: Tera Term log archive 導入

## Layer 4: Legacy workspace (`PortaRe0/software`)

役割:
- 移設前の旧作業場
- 現在は archaeology 用

使い方:
- 古いログ、BCD、ISO、vendor Linux 残骸、過去スクリプトを掘る場所
- source-of-truth としては使わない

今回確認したこと:
- `UEFI_MOVED.txt` により、現行 repo は `porta-a733-uefi` / `porta-a733-bringup`
- recovered `teraterm3.log` は 2026-04-02 時点で BCD error (`0xc000000d`) まで進んでいる
- 現在の `teraterm.log` は 2026-04-07 build で `No mapping` により BCD 前で停止
- `software/build/install_windows_installer.py` など一部 helper は current bring-up repo から同期済み

注意:
- ここにある同名スクリプトは legacy copy の可能性がある
- `software` 側で作業を継続すると source が再び混ざる

## Timeline that matters

### 2026-04-02 (`software/log/teraterm3.log`)

- firmware build time: `13:52:07 on Apr 2 2026`
- `\EFI\BOOT\BOOTAA64.EFI` 起動
- `CurrentPolicy` / `CiPolicyIDs` まで進行
- `File: \EFI\Microsoft\Boot\BCD`
- `Status: 0xc000000d`
- `startup.nsh` / `Shell>` の痕跡は回収ログ中に見当たらない

意味:
- この時点では Windows Boot Manager が BCD エラー画面まで進んでいた
- 少なくとも current log よりは二重起動の混入が少ない可能性が高い

### 2026-04-07 (`software/log/teraterm.log`)

- firmware build time: `07:03:10 on Apr 7 2026`
- 1回目の `\EFI\BOOT\BOOTAA64.EFI` 起動では `AllocatePages(Type=2, Size=0x1)` 成功
- その後 Shell / `startup.nsh` を経由して `\EFI\Microsoft\Boot\bootmgfw.efi` を再起動
- 2回目に `ConvertPages: Incompatible memory types` / `No mapping`
- BCD 行に到達していない

意味:
- いま見えている `0x102000` 失敗は「二重起動で再要求した副作用」を含む
- 2026-04-02 から 2026-04-07 の間で、少なくとも boot path は変わっている
- ログ表現も変化しており、`2026-04-02` 側は `LoadImage failed`、`2026-04-07` 側は `EfiBootManagerBoot failed`

## What `software/log/codex.txt` proves

- `codex.txt` は partial transcript だが、2026-04-03 から 2026-04-06 にかけて live media 上の
  `F:\EFI\BOOT\BOOTAA64.EFI` と `F:\EFI\Microsoft\Boot\bootmgfw.efi` を同一 patched variant に
  繰り返し差し替えていたことを示している
- つまりこの期間の実機ログは「元の Windows loader の素の挙動」ではなく、patch 済み variant の結果が強く混ざる
- `BOOTAA64.PATCH.txt` が live media 上の patch marker として運用されていた
- BCD 側も hidden element / policy 関連の実験をしている

確認できた重要点:

1. live media の `BOOTAA64.EFI` と `bootmgfw.efi` は lockstep で更新されていた
2. 2026-04-06 時点では `0x1003BA6C` 版が `No mapping` regression を起こしたと記録されている
3. その後 `cleanup helper` を飛ばす safer 版に切り替えると `No mapping` は消えたと記録されている
4. 同 transcript 中に `Status: 0xc0000098` も現れており、BCD 系の stop point 実験が続いていた

意味:

- Apr 3-6 の `teraterm.log` は source / live media / marker の整合を毎回確認しながら patch 実験していた
- したがって Apr 7 の `No mapping` を見る時は、「UEFI regression」だけでなく「patched Windows loader の副作用」
  を常に候補に入れる必要がある

関連メモ:
- `analysis/CODEX_PATCH_TIMELINE_FROM_LOG.md`
- `analysis/CODEX_TRANSCRIPT_FINDINGS_20260408.md`

## Practical rules for further investigation

1. `porta-a733-uefi` は本体変更のみ見る
2. `~/edk2` は diagnosis patch として別扱いにする
3. `porta-a733-bringup/build/BOOTAA64.*.EFI` は generated binary として扱う
4. `PortaRe0/software` は発掘用のみ。新規 source 編集の場にしない
5. 比較の基準ログは `software/log/teraterm3.log` と current `software/log/teraterm.log`

## Current regression candidates

1. `PlatformBootManagerLib.c` の boot path 変更
2. removable boot と `startup.nsh` による二重起動
3. SD DMA cache coherency 修正の副作用または build 差
4. `HeadlessGopDxe` / `SecurityStubDxe` は current worktree で大きく触られているが、Apr 2 の到達ログにも存在するため Apr2→Apr7 退化の主犯候補としては優先度低め
5. media contents (`BOOTAA64.EFI`, `BCD`, startup script) の差
