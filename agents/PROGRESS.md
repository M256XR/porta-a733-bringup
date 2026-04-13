# PortaRe0 ソフトウェア開発 進捗ログ

## 現在のフェーズ
**Phase 3: PCBレイアウト完了待ち → ソフトウェア開発 準備中**

## 現在の作業箇所
- **筐体・PCB完成待ちのため QMK/TinyUSB は保留**
- **EDK2 移植（Windows ARM）を優先的に進行中**
- **現在地**: bootmgfw.efi が LoadImage/StartImage 成功 → SHA-256計算中に Synchronous Exception (EC=0x00) でクラッシュ。原因はSD DMAドライバのキャッシュ不整合（CMD18マルチブロックリードのpost-DMA D-cacheインバリデーション欠落）。修正済みFDをSD書き込み完了、実機テスト待ち。
- **最新ビルド成果物**: build/A733.fd は FD_SHA256_16=5c048df49dee17d6, BUILD_GIT=012e8a4-dirty
- **進捗**: DMA cache coherency fix + 例外ハンドラ診断強化（INSN@ELR, CPACR_EL1, SCTLR_EL1, ID_AA64ISAR0_EL1ダンプ）
- **直近の詰まりポイント**: bootmgfw.efi がSHA-256ハッシュ計算中にクラッシュ → DMAリード後のD-cacheに古いデータが残り、CPU実行時にundefined instructionとなる → SunxiSmhcDxeのpost-DMAキャッシュインバリデーションをCMD17のみからALL readコマンドに拡大して修正
- **次のタスク**: 修正FDで実機起動 → bootmgfw.efiがSHA-256チェックを通過するか確認 → BCD アクセスまで進んだら Windows インストールへ
- **注意**: FVMAIN 100%Full（圧縮後 34% なので動作は問題なし。追加ドライバが必要な場合は FV サイズ拡張か BootProbe.inf 削除を検討）
- **方針確定**: PCIe（M.2 SSD）は実機PCB完成まで保留 → SD カードへの Windows インストールを先行
- 参照: specs/windows_arm.md、analysis/UEFI_REVERSE_ENGINEERING_NOTES.md、agents/UEFI_REFERENCE_MAP.md

---

## フェーズ完了状況

### RP2040 キーボードファームウェア ⏳ 未着手
- [ ] フレームワーク選定（QMK / KMK / Pico SDK）
- [ ] キーマトリクス 63キー定義
- [ ] スライドパッド（GP27/GP28）統合
- [ ] USB HID デバイス認識確認
- [ ] LED（CHG/FULL/ACT）制御

### オーディオ ⏳ 未着手
- [ ] MAX98357A I2S スピーカー動作確認
- [ ] PCM5102A DAC + TPA6132A2 ヘッドフォン動作確認
- [ ] ALSA / PipeWire 設定

### Linux システム設定 ⏳ 未着手
- [x] Cubie A7Z 初期セットアップ（公式Debianイメージ動作確認済み）
- [ ] ディスプレイ（LS055R1SX04）設定
- [ ] USB HUB（VL812）動作確認
- [ ] M.2 SSD 認識確認

### Windows ARM（ロマン枠） 🔨 EDK2移植 進行中
- [x] リソース調査（specs/windows_arm.md に記録）
- [x] 現在のブートチェーン確認（TF-A BL31使用有無）→ boot0→TF-A BL31→BL33(EDK2)
- [ ] TF-A BL31 移植（不要・既存BL31をそのまま使用）
- [x] EDK2 SD起動・UEFI表示まで到達
- [x] EDK2 MMU初期化クラッシュ修正済み（CPACR_EL1.FPEN fix）
- [x] DXE Core起動・UEFI Shell（Shell> プロンプト・キーボード入力動作確認済み）
- [x] ACPI テーブル実機ロード確認済み（FACP/GTDT/APIC/SPCR/DSDT 全5テーブル）
- [x] SMHC0（SD）DXE ドライバ実装・DiskIoDxe/PartitionDxe/Fat 追加（Phase B コード完）
- [x] SMHC0 実機動作確認（DEBUG版で `map -r` → `fs0:` まで確認済み）
- [ ] RELEASE版クラッシュ原因切り分け
- [x] EDK2 側で `\EFI\BOOT\BOOTAA64.EFI` 優先・FV Shell フォールバックを実装
- [x] ホスト側で `BOOTAA64.EFI` / `startup.nsh` 配置用スクリプトを追加
- [ ] `fs0:` 上のブート導線整備を実機確認（`TESTA7Z.EFI` / `BOOTAA64.EFI` / `startup.nsh` 配置済み、最新 DEBUG ログ待ち）
- [ ] Windows ARM SD インストール
- [ ] Windows ARM 起動

---

## 未解決の TBD 事項

| 項目 | 解決タイミング |
|------|--------------|
| ~~RP2040 ファームウェアフレームワーク~~ | ✅ session01で確定 |
| Linux OS ディストリビューション | Cubie A7Z 実機届いたら確認 |
| キーレイアウト（QMKレイヤー構成） | QMK開発開始時 |

---

## 直近の決定事項ログ

### 2026-04-06（session11）
- **DMA cache coherency バグ発見・修正**:
  - bootmgfw.efi が SHA-256 integrity check 中に Synchronous Exception (EC=0x00, ELR=0x23CCE6AB4) でクラッシュ
  - ESR EC=0x00 = "Unknown reason (AArch64)" だが、ELRのファイルオフセットにある命令は `CBZ X28, #+12` (0xB400007C) で完全に valid
  - **根本原因**: `SunxiSmhcDxe.c` の post-DMA D-cache invalidation が CMD17（single block read）のみに適用されていた。CMD18（multi-block read）でDMA完了後、CPU D-cache にスペキュラティブプリフェッチで読まれた古いデータが残り、bootmgfw.efi の .text セクションが壊れた状態で実行される
  - **修正**: `WriteBackInvalidateDataCacheRange(Packet->InDataBuffer, DataSize)` を全 read コマンドに適用（CMD17限定条件を除去）。CMD17ループ内のper-block DMA後にも同様のインバリデーション追加
- **例外ハンドラ診断強化** (`DefaultExceptionHandler.c`):
  - ESR decode 直後に以下をダンプする診断ブロックを追加:
    - `INSN@ELR`: ELR アドレスから読んだ実際の命令ワード（D-cache内容 vs ファイル内容の比較用）
    - `CPACR_EL1` (FPEN フィールド付き)
    - `SCTLR_EL1`
    - `ID_AA64ISAR0_EL1` (AES/SHA1/SHA2/CRC32/SHA3/SM3/SM4 各フィールドをデコード表示)
- **ビルド・SD書き込み完了**: FD_SHA256_16=5c048df49dee17d6, BUILD_GIT=012e8a4-dirty
  - SD verify SHA256 MATCH 確認済み
- **PE/COFF 解析結果** (bootmgfw.efi):
  - ImageBase=0x10000000, SectionAlignment=0x1000, EntryPoint RVA=0x3A130
  - RVA 0x3BAB4 (crash site): `CBZ X28, #+12` — valid instruction, confirming memory corruption not code issue
  - V0-V15 に SHA-256 K constants (0x428A2F98...) が入っていた = crash は SHA-256 crypto 実行中
- **次のアクション**: 実機再起動 → bootmgfw.efi が SHA-256 チェックを通過するか確認

### 2026-03-24（session10）
- **外部 EFI 切り分け用アプリ追加**: `Platform/Allwinner/A733Pkg/Application/BootProbe/BootProbe.inf`
  - `BootProbe.efi` は外部 EFI として起動されたらメッセージを出して数秒後に `EFI_SUCCESS` で戻るだけの最小アプリ
  - `build/build_edk2.sh` で `build/BootProbe.efi` も回収するよう更新
- **Boot Manager の追跡ログ強化**:
  - `PlatformBootManagerLib` の外部 EFI 起動パスで `[A733] Trying fs candidate ...`
  - `"[A733] Booting option"` / `"[A733] Boot result: %r"` を `DEBUG_ERROR` レベルで出すよう調整
- **ESP / SD 反映を更新**:
  - `python build/write_sd.py` で `PhysicalDrive3` へ再書き込みし SHA256 verify match
  - `python build/install_esp_files.py --esp S:\ --with-startup-nsh --force-startup-nsh` 実行
  - `S:\EFI\BOOT\BOOTAA64.EFI` と `S:\EFI\BOOT\TESTA7Z.EFI` はともに `build/BootProbe.efi` 由来
  - `build/BootProbe.efi` の SHA256 は `c028303fb4da21bc5f987b1d40a947ecb6b7a9f01c1dc764e1255b06ad8a6cd6`
- **直近の実機観測**:
  - 旧ログでは `startup.nsh` 3行目の `fs0:\EFI\BOOT\TESTA7Z.EFI` で `Script Error Status: Access Denied`
  - そのため現状の失敗点は `fs0:` 認識ではなく外部 EFI 実行 (`LoadImage/StartImage`) 側
- **次のアクション**:
  - 最新 `FD_SHA256_16=b34058618f8dac16` で再起動
  - `log/teraterm.log` に `BootProbe` 文字列または `[A733] Boot result` が出るか確認

- **追加切り分け（再起動前に反映済み）**:
  - `PlatformBootManagerLib` の外部起動経路を `EfiBootManagerBoot()` から `gBS->LoadImage(TRUE, ...)` / `gBS->StartImage()` へ置き換え
  - `"[A733] PlatformBootManagerAfterConsole entered"` / `"[A733] LoadImage failed: %r"` / `"[A733] StartImage failed: %r"` を出す診断版 DEBUG に更新
  - 新しい SD 書き込み済みイメージ識別子は `FD_SHA256_16=d7c7762bb8b98fd8`

### 2026-03-24（session09）
- **DEBUG 方針をコードへ反映**: `build/build_edk2.sh` を DEBUG ビルド出力に戻し、`build/Shell.efi` も取り出すよう更新
- **UEFI ブート導線を実装**:
  - `PlatformBootManagerLib` が `\EFI\BOOT\BOOTAA64.EFI` を優先して探索・起動
  - 見つからない、または起動失敗時のみ FV 内 `Shell.efi` にフォールバック
- **ESP 配置補助を追加**: `build/install_esp_files.py`
  - `--esp S:\` のように指定して `EFI\BOOT\BOOTAA64.EFI` を配置
  - 必要なら `startup.nsh` のテンプレートも配置可能
- **SD 反映完了**:
  - `python build/write_sd.py` で `PhysicalDrive3` へフル書き込み + SHA256 verify match
  - ESP を `S:` として割り当て、`BOOTAA64.EFI` / `startup.nsh` を配置
  - `S:\EFI\BOOT\BOOTAA64.EFI` の SHA256 は `build/Shell.efi` と一致
- **補足**: 現在の ESP には `BOOTAA64.EFI`（中身は `Shell.efi`）のみ存在し、`EFI\Microsoft\Boot\bootmgfw.efi` はまだ未配置
- **次のアクション**:
  - Windows ローダ配置後、`startup.nsh` から `fs0:\EFI\Microsoft\Boot\bootmgfw.efi` 自動起動を確認
  - その後、自動起動確認

### 2026-03-24（session08）
- **到達点更新**: DEBUG 版では `SMHC0 -> GPT -> FAT -> fs0: -> Shell` まで安定
- **RELEASE版は未解決の別問題あり**:
  - `AllocatePoolPages: failed to allocate 719611 pages`
  - `Synchronous Exception at 0xAFAFAFAFAFAFAFAF`
- **方針**: 次セッションは RELEASE 版を追わず、DEBUG 版ベースで先に進める
- **現在 SD に入っているビルド識別子**: `FD_SHA256_16=14fa086e514f1353`
- **次のアクション**: `fs0:` 上のブート導線整備
  - `EFI\BOOT\BOOTAA64.EFI`
  - 必要なら `startup.nsh`
  - 手動起動確認から自動起動へ

### 2026-03-22（session07）
- **方針転換確定**: PCIe（M.2 SSD）は実機PCBまたはM.2-PCIeアダプタ入手まで保留
- **Windows インストールターゲット = SD カード**（SMHC0経由）
- **Cubie A7Z に eMMC は存在しない**ことが判明（UFS optional slot + MicroSD のみ）
  - SMHC2 エントリを mSmhcTable から除外（初期化失敗ログ抑制）
  - EmmcDxe を FV から削除
- **追加ドライバ**: DiskIoDxe + PartitionDxe + FatPkg（SD→GPT→FAT32 EFI SP 認識に必要）
- **次のアクション**: ビルド → UEFI Shell `map -r` で SD カード認識確認

### 2026-03-21（session06）
- **ACPI テーブル実機ロード完全確認**
- **全5テーブルインストール成功**: FACP(Handle=1) / GTDT(Handle=2) / APIC(Handle=3) / SPCR(Handle=4) / DSDT(Handle=5) 全て `InstallAcpiTable = 0x0 (EFI_SUCCESS)`
- **謎だった `Error: Image at ... start failed: 00000001` の正体判明**:
  - `EFI_REQUEST_UNLOAD_IMAGE (0x0F)` を返したときに DxeCore が `Image->Status != EFI_SUCCESS` として印字する既知の挙動
  - `%r` フォーマット出力 "00000001" はこの warning status の表示、エラーではない
  - line 380 の `remove-symbol-file` で正常アンロード確認済み
- **ビルドシステム修正**:
  - `build_edk2.sh` に Platform シンボリックリンク作成を追加: `edk2/Platform → edk2-platforms/Platform`
  - edk2-platforms (PACKAGES_PATH 2番目) にあるモジュールの build 出力は `AARCH64/edk2-platforms/Platform/...` に生成されるが、GenFds は `AARCH64/Platform/...` を探す不一致を解消
- **カスタム診断ドライバ `A733AcpiPlatformDxe`**: 問題特定のため作成、そのまま本番運用に採用
  - `Platform/Allwinner/A733Pkg/Drivers/AcpiPlatformDxe/A733AcpiPlatformDxe.{c,inf}`
  - MdeModulePkg の汎用 AcpiPlatformDxe を置き換え、SerialPortLib で各ステップをデバッグプリント
- **次のアクション**: Phase B — eMMC/SD DXE ドライバ実装

### 2026-03-21（session05）
- **ACPI テーブル全テーブルビルド成功・SD image 生成完了**
- **実装完了テーブル**: FADT / MADT / GTDT / SPCR / DSDT（全5テーブル）
- **バイナリ検証**: sig/len/rev 全て正常（FACP rev=6, APIC rev=5, GTDT rev=3, SPCR rev=2, DSDT rev=2）
- **修正した問題**:
  - `ACPI_HEADER` マクロに余分な `{}` があり、`EFI_ACPI_DESCRIPTION_HEADER.Signature`（UINT32スカラー）への初期化として扱われ、Length・Revision が 0 になっていた → GenFw で MADT "APIC revision check failed"
  - Fix: マクロの外側 `{}` を削除（呼び出し側の `{ ACPI_HEADER(...) }` が `EFI_ACPI_DESCRIPTION_HEADER` 用の braces になる）
  - `AcpiTables.inf` の FILE_GUID `a733ac01-acpi-acpi-acpi-a733a733a733` に非16進文字 'p' → GenFfs エラー → `a733ac01-ac01-ac01-ac01-a733a733a733` に修正
- **ACPI テーブル構成**:
  - FADT: HW_REDUCED_ACPI | LOW_POWER_S0_IDLE_CAPABLE, PSCI SMC (not HVC), PM_PROFILE_TABLET
  - MADT: GICv3, GICD@0x3400000, GICR@0x3460000, 8CPU (A55×6 + A76×2), 各MPIDR設定
  - GTDT: 4タイマー IRQ 26/27/29/30（DTB確認済み）
  - SPCR: UART0@0x02500000, 16550_WITH_GAS, 115200bps, polling mode
  - DSDT: CPU0-7 (_HID=ACPI0007), COM0 (_HID=ARMH0011, UART0)
- **次のアクション**: SD書き込み → 実機ブートで AcpiTableDxe ロードログ確認 → eMMC/SD DXE (Phase B)

### 2026-03-21（session04）
- **UEFI Shell 完全動作達成** (`Shell>` プロンプト表示・キーボード入力OK)
- **原因と対策**:
  - `PcdShellLibAutoInitialize` が `PcdsFixedAtBuild` でなく `PcdsFeatureFlag` → 修正
  - UnicodeCollation パスが間違い → `MdeModulePkg/Universal/Disk/UnicodeCollation/EnglishDxe/EnglishDxe.inf` が正解
  - SerialDxe / ConPlatformDxe / ConSplitterDxe / TerminalDxe を FV に追加
  - `PlatformBootManagerBeforeConsole` で ConIn/ConOut/ErrOut UEFI 変数にシリアル端末デバイスパス（VenHw→UART→VT100）を登録 → BdsDxe がTerminalDxeをConSplitterDxeに接続
- **現在の構成**: SerialDxe(16550) + VT100 TerminalDxe が gST->ConOut に接続済み
- **残課題**: DXE_RUNTIME_DRIVER の Section Alignment 警告 (0x1000 vs 0x10000) → 実害なし・後回し
- **次のアクション**: Windows ARM ブートに向けた調査 or dh/memmap コマンド追加

### 2026-03-21（session03）
- **根本原因特定**: `ZeroMem(4096)` クラッシュ = `CPACR_EL1.FPEN=0b00`（NEON トラップ）
  - TF-A が BL33 を EL1 にドロップするとき CPACR_EL1 はデフォルト値（FP/NEONトラップ有効）のまま
  - `BaseMemoryLibOptDxe` が 4KB 以上の ZeroMem で NEON 命令を使用 → EL1 同期例外 → フリーズ
- **修正**: `ArmPlatformInitialize()` に `msr cpacr_el1, #0x300000`（FPEN=0b11）追加
  - `A733Platform.c` に inline asm で実装・ビルド確認済み（PeilessSec.efi に `msr cpacr_el1, x0` 0x66d0 に確認）
- **ビルド問題の教訓**:
  - `GCC5` は tools_def.txt 3.06 で削除済み → `-t GCC` を使うこと
  - `-p` に絶対パスを渡すと `NormFile()` がパスを破壊する（WORKSPACE prefix string strip バグ）
    → `-p Platform/Allwinner/A733Pkg/A733Pkg.dsc`（相対パス）で渡すこと
  - ビルドスクリプト: `build/build_edk2.sh` に手順を記録済み
- 新ビルド FD: `build/A733.fd` / SD image: `build/sd_boot.img`（PEILESS_ENTRY=0x4a007748）
- **次のアクション**: SD書き込み → URR ZeroMem done 確認 → ArmEnableMmu確認 → DXE Core起動へ

### 2026-03-20（session02）
- EDK2 SD起動: PEILESS_ENTRY を FV ZeroVector から正確に特定する手法を確立
- PEILESS_ENTRY = `0x4A007550`（FV_base 0x4A001000 + B_offset 0x6550）
- クラッシュ場所を `ArmConfigureMmu()` 内部に絞り込み完了
  - `[A733] InitMmu: calling ArmConfigureMmu` まで出力 → その後ハング
  - FillTranslationTable か ArmEnableMmu かは未特定
- 診断プリント追加済みファイル:
  - `ArmPlatformPkg/MemoryInitPei/MemoryInitPeiLib.c` に DbgStr2 + InitMmu前後のプリント
  - `Platform/Allwinner/A733Pkg/Library/PlatformLib/A733Platform.c` に GetVirtualMemoryMap 診断
- `make_sd_image.py` の backslash escaping 問題発見: WSL越しのheredocで `\\r` が CR になる
  → Windows側でPythonスクリプトを書いてWSLで実行する方式で解決
- **次のアクション**: `ArmMmuLibCore.c` の `ArmConfigureMmu()` に診断プリントを追加して FillTranslationTable vs ArmEnableMmu を特定する

### 2026-03-17〜18（session01）
- フレームワーク確定: RP2040 #1 → **QMK**、RP2040 #2 → **Pico SDK + TinyUSB（UAC2）**
- 開発計画: `specs/dev_plan.md` に詳細まとめ
- **方針転換**: 筐体未完成のため QMK/TinyUSB は保留 → EDK2 移植を優先
- Cubie A7Z システム調査: ブートチェーン = SPL→U-Boot（UEFI無効）→extlinux→Linux
- U-Boot ビルド日: 2024-03-20 / カーネル: 5.15.147-7-a733 / RAM: 1GB
- アイドル消費電力: 3〜5W（ヒートシンクのみで触れないレベルに熱くなる）
- Windows ARM 調査完了: `specs/windows_arm.md` に知見・リソース・ロードマップ・EDK2構成を記録
- EDK2参考実装確認済み: RPi4 EDK2 / awwiniot/UEFI-aw1689（AXP PMICドライバ流用可）
- U-Boot A733 mainlineパッチ: v3投稿済み・未マージ（v2026.07以降見込み）→ 待たずにBSPで進める
- **次のアクション**: Cubie A7Z でGIC/TF-A情報収集（調査5.txt 未取得）→ TF-A BL31 ポート開始

### 2026-03-16（session00）
- software/ フォルダ・Claude サブディレクトリ構成を作成
- ハードウェア側 Claude/ と同様の管理体制をソフトウェア開発用に整備
