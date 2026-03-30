# EDK2 移植ドキュメント — Allwinner A733 (Cubie A7Z)

> 最終更新: 2026-03-21（session04）
> ステータス: **UEFI Shell 完全動作済み**

---

## 目次

1. [ブートチェーン全体像](#1-ブートチェーン全体像)
2. [ここまでの手順（再現手順書）](#2-ここまでの手順再現手順書)
3. [ビルド手順](#3-ビルド手順)
4. [ファイル構成と各ファイルの役割](#4-ファイル構成と各ファイルの役割)
5. [確認済みハードウェア情報](#5-確認済みハードウェア情報)
6. [今後のロードマップ](#6-今後のロードマップ)
7. [既知の問題・TODO](#7-既知の問題todo)
8. [デバッグTips](#8-デバッグtips)

---

## 1. ブートチェーン全体像

```
電源ON
  │
  ▼
boot0 (Allwinner SPL) — eMMC内蔵・変更不可
  │  DDR初期化済み、SDカードから sunxi-package を 0x4A000000 にロード
  │
  ▼
TF-A BL31 (EL3, 0x48000000) — eMMC内蔵・変更不可
  │  PSCI 1.0 / SMC方式
  │  BL33 (EDK2) を EL1 にドロップ
  │
  ▼
EDK2 PeilessSec (SEC phase, EL1, 0x4A000000)
  │  MMU初期化
  │  LZMA解凍 → FVMAIN
  │
  ▼
EDK2 DXE Core (0x7FCC9000 付近)
  │  各DXEドライバロード
  │
  ▼
BdsDxe → PlatformBootManagerLib
  │  ConOut変数設定 → TerminalDxe接続
  │
  ▼
UEFI Shell (Shell> プロンプト) ← ★現在地
  │
  ▼
（将来）Windows ARM
```

### FD メモリレイアウト

```
0x4A000000 + 0x000000: ARM64 B命令スタブ (4KB)
                        ← boot0がジャンプ、PeilessSecエントリに分岐
0x4A000000 + 0x001000: FVMAIN_COMPACT (PeilessSec + LZMA圧縮FVMAIN)
合計: 1160KB (0x128000) — sunxi-package u-bootスロット 0x12B9DC に収まる
```

---

## 2. ここまでの手順（再現手順書）

### Step 0: 前提確認（session01, 2026-03-17）

- Cubie A7Z の TF-A BL31 が eMMC に内蔵されて動作中であることを確認
- boot0 → TF-A BL31 → U-Boot というブートチェーンを確認
- **U-Boot を EDK2 に差し替えるだけでよい** (TF-A 自体の移植は不要)

### Step 1: EDK2 Platform Package 新規作成（session02, 2026-03-20）

`src/edk2/Platform/Allwinner/A733Pkg/` を一から作成。

ポイント:
- ビルドツールは `GCC5` ではなく `-t GCC` を使う (`GCC5` は tools_def.txt 3.06 で削除済み)
- DSC のパスは **相対パス** で渡す（絶対パスだと `NormFile()` がパスを破壊するバグあり）

```bash
# NG: 絶対パス
-p /home/linux/edk2/Platform/Allwinner/A733Pkg/A733Pkg.dsc

# OK: 相対パス (PACKAGES_PATH 起点)
-p Platform/Allwinner/A733Pkg/A733Pkg.dsc
```

### Step 2: CPACR_EL1.FPEN 修正（session03, 2026-03-21）

**症状**: PeilessSec の MMU 初期化中に `ZeroMem` でフリーズ
**原因**: TF-A が BL33 を EL1 にドロップする際、`CPACR_EL1.FPEN=0b00`（リセット後デフォルト）のまま。
FP/NEON 命令が EL1 同期例外を起こす。
`BaseMemoryLibOptDxe` は 64 バイト以上の `ZeroMem` で NEON 命令 (`stp q0, q0`) を使用するため即クラッシュ。

**修正**: `ArmPlatformInitialize()` の先頭で FPEN を有効化:
```c
// CPACR_EL1.FPEN = 0b11 → EL1/EL0 で FP/NEON を許可
__asm__ volatile ("msr cpacr_el1, %0" :: "r" ((UINTN)0x00300000));
```

**補足**: SEC フェーズ (`LibraryClasses.common.SEC`) では念のためスカラー版 `BaseMemoryLib` を使用し、NEON 依存を完全回避している。

### Step 3: DXE Core 起動（session03, 2026-03-21）

必要な DXE ドライバを `.fdf` に追加してロードされることを確認:
- `PcdDxe`, `CpuDxe`, `ArmGicDxe`, `TimerDxe`
- `SecurityStubDxe`, `Metronome`, `WatchdogTimer`
- `BdsDxe`, `RuntimeDxe`, `VariableRuntimeDxe`（エミュレーションモード）

### Step 4: UEFI Shell 起動（session04, 2026-03-21）

#### 問題1: PcdShellLibAutoInitialize が効かない

**症状**: `ShellLibConstructor` で `ASSERT_EFI_ERROR`
**原因**: `PcdShellLibAutoInitialize` は `ShellPkg.dec` で `PcdsFeatureFlag` (BOOLEAN) として宣言されている。`<PcdsFixedAtBuild>` セクションに書いても無視される。

**修正**:
```dsc
ShellPkg/Application/Shell/Shell.inf {
  <PcdsFeatureFlag>                      # ← ここが重要
    gEfiShellPkgTokenSpaceGuid.PcdShellLibAutoInitialize|FALSE
}
```

#### 問題2: UnicodeCollation が見つからない

**症状**: `ShellCommandLibConstructor` → `CommandInit()` → `LocateProtocol(gEfiUnicodeCollation2ProtocolGuid)` 失敗 → `EFI_DEVICE_ERROR`
**修正**: 正しいパスのドライバを追加:
```dsc
# NG: 存在しない
MdeModulePkg/Universal/UnicodeCollationEnglishDxe/...

# OK: 正しいパス
MdeModulePkg/Universal/Disk/UnicodeCollation/EnglishDxe/EnglishDxe.inf
```

#### 問題3: gST->ConOut = NULL でクラッシュ

**症状**: Shell.efi のライブラリコンストラクタ内で PC=0 にジャンプしてクラッシュ
**原因**: `gST->ConOut` が NULL。Shell 内部で `ConOut->ClearScreen()` を呼ぶため。
**修正**: コンソールドライバを FV に追加:
```fdf
INF MdeModulePkg/Universal/SerialDxe/SerialDxe.inf
INF MdeModulePkg/Universal/Console/ConPlatformDxe/ConPlatformDxe.inf
INF MdeModulePkg/Universal/Console/ConSplitterDxe/ConSplitterDxe.inf
INF MdeModulePkg/Universal/Console/TerminalDxe/TerminalDxe.inf
```

#### 問題4: Shell プロンプトが表示されない

**症状**: Shell は起動しているが TeraTerm に何も出力されない
**原因**:
- `ConOut` UEFI 変数が空 → ConPlatformDxe が TerminalDxe ハンドルに `ConsoleOutDeviceGuid` をインストールしない → ConSplitterDxe が TerminalDxe の SimpleTextOut に接続しない → `gST->ConOut` は仮想ハンドルのまま実デバイス無し

**修正**: `PlatformBootManagerBeforeConsole()` で ConOut 変数を設定する:
```c
// VenHw(EDKII_SERIAL_PORT_LIB_VENDOR_GUID)/UART(115200,8N1)/VT100 のデバイスパスを登録
CopyGuid(&mSerialConsole.TermType.Guid, &gEfiVT100Guid);
EfiBootManagerUpdateConsoleVariable(ConIn,  &mSerialConsole, NULL);
EfiBootManagerUpdateConsoleVariable(ConOut, &mSerialConsole, NULL);
EfiBootManagerUpdateConsoleVariable(ErrOut, &mSerialConsole, NULL);
```

BdsDxe が `PlatformBootManagerBeforeConsole()` 呼出後にコンソール接続処理を行うため、この時点で変数が入っていれば SerialDxe → TerminalDxe → ConSplitterDxe が正しく繋がる。

**結果**: `Shell>` プロンプト表示・キーボード入力・コマンド実行 ✅

---

## 3. ビルド手順

### 前提環境

| 項目 | 内容 |
|------|------|
| ホスト OS | Windows 11 + WSL2 (Ubuntu) |
| ツールチェーン | `aarch64-linux-gnu-gcc` (GCC) |
| EDK2 | `/home/linux/edk2` |
| EDK2-Platforms | `/home/linux/edk2-platforms` |
| プラットフォームコード | `D:/Projects/PortaRe0/software/src/edk2/Platform/` (WSL: `/mnt/d/...`) |

### ビルド手順

```bash
# 1. WSL 経由でビルド
wsl.exe bash -c "bash /mnt/d/Projects/PortaRe0/software/build/build_edk2.sh 2>&1 | tail -30"

# ビルド成功時: A733.fd が build/ にコピーされる
```

### SD イメージ作成

```bash
# Windows Python で実行（make_sd_image.py は Windows パスを使用）
python3 D:/Projects/PortaRe0/software/build/make_sd_image.py
```

処理内容:
1. `boot0dump.bin` (eMMC dump、TF-A + sunxi-package) をロード
2. sunxi-package 内の U-Boot スロットを `A733.fd` で上書き
3. FVMAIN_COMPACT 先頭の ZeroVector B 命令からエントリポイントを自動検出してスタブをパッチ
4. `sd_boot.img` (16MB) を書き出し

### SD カードへの書き込み

```powershell
# Win32DiskImager または Rufus で sd_boot.img を SD カードに書き込む
# または WSL から:
# sudo dd if=sd_boot.img of=/dev/sdX bs=1M status=progress
```

### build_edk2.sh の注意点

```bash
# DSC は必ず相対パスで渡す
-p Platform/Allwinner/A733Pkg/A733Pkg.dsc   # OK
-p /home/linux/edk2/Platform/...             # NG (NormFile バグ)

# ツールチェーン名
-t GCC    # OK (現行)
-t GCC5   # NG (tools_def.txt 3.06 で削除済み)

# PeilessSec.c を毎回 touch してビルドタイムスタンプを更新
touch /home/linux/edk2/ArmPlatformPkg/PeilessSec/PeilessSec.c
```

---

## 4. ファイル構成と各ファイルの役割

```
src/edk2/Platform/Allwinner/A733Pkg/
├── A733Pkg.dec                          # パッケージ宣言（GUID定義等）
├── A733Pkg.dsc                          # ビルド定義（ライブラリ・ドライバ一覧・PCD）
├── A733Pkg.fdf                          # フラッシュイメージレイアウト定義
├── AcpiTables/
│   ├── AcpiTables.inf                   # ACPIテーブルのビルド定義（現在コメントアウト）
│   ├── Madt.aslc                        # MADT: GICv3・8コアCPU定義
│   └── Gtdt.aslc                        # GTDT: ARMタイマーIRQ定義
└── Library/
    ├── PlatformLib/
    │   ├── PlatformLib.inf
    │   ├── A733Platform.c               # ArmPlatformLib実装（メイン）
    │   └── AArch64/A733Helper.S         # アセンブリヘルパー
    └── PlatformBootManagerLib/
        ├── PlatformBootManagerLib.inf
        └── PlatformBootManagerLib.c     # BDS起動管理（コンソール設定・Shell起動）

build/
├── build_edk2.sh                        # EDK2ビルドスクリプト（WSL上で実行）
├── make_sd_image.py                     # SDイメージ作成スクリプト（Windows Python）
├── A733.fd                              # ビルド成果物（FDイメージ）
└── sd_boot.img                          # SDカード書き込み用イメージ
```

### A733Pkg.dsc — 主要 PCD

| PCD | 値 | 説明 |
|-----|-----|------|
| `PcdGicDistributorBase` | `0x03400000` | GICv3 GICD |
| `PcdGicRedistributorsBase` | `0x03460000` | GICv3 GICR |
| `PcdSystemMemoryBase` | `0x40000000` | DRAM 開始 |
| `PcdSystemMemorySize` | `0x40000000` | DRAM サイズ (1GB) |
| `PcdFdBaseAddress` | `0x4A000000` | EDK2 FD 配置アドレス |
| `PcdSerialRegisterBase` | `0x02500000` | UART0 レジスタ |
| `PcdSerialClockRate` | `24000000` | UART クロック (HOSC 24MHz) |
| `PcdUartDefaultBaudRate` | `115200` | シリアルボーレート |
| `PcdCoreCount` | `8` | CPU コア数 |
| `PcdEmuVariableNvModeEnable` | `TRUE` | 変数ストレージをRAMエミュレーション |

### A733Platform.c — 動作説明

```
ArmPlatformInitialize()
  └─ CPACR_EL1.FPEN = 0b11 を設定 (FP/NEON有効化)
     ※ TF-AがEL1にドロップ後、FP/NEONがデフォルトでトラップされるため必須

ArmPlatformGetVirtualMemoryMap()
  └─ メモリマップを返す:
     [0] 0x40000000, 1GB, WriteBack キャッシュ可能 (DRAM)
     [1] 0x00000000, 256MB, Device メモリ (ペリフェラル)
     ※ boot0でDDR初期化済みのため初期化コードは不要

ArmPlatformGetPlatformPpiList()
  └─ 8コアのMPIDRテーブルを返す (A55×6: 0x000-0x500, A76×2: 0x600-0x700)
```

### PlatformBootManagerLib.c — 動作説明

```
PlatformBootManagerBeforeConsole()  [BdsDxeがコンソール接続する前に呼ばれる]
  └─ SerialDxeデバイスパス (VenHw/UART/VT100) を ConIn/ConOut/ErrOut 変数に登録
     → BdsDxeがこの変数を読んでTerminalDxeをSerialDxeに接続
     → ConSplitterDxeが実シリアル端末をgST->ConOutに集約

PlatformBootManagerAfterConsole()  [コンソール接続後に呼ばれる]
  └─ EfiBootManagerConnectAll() でストレージ等を全接続
  └─ FV内のShell.efi (GUID: 7C04A583-...) を見つけてブート
```

### A733Pkg.fdf — FVレイアウト

```
[FD.A733]
  0x000: 4KB スタブ (make_sd_image.py が B命令をパッチ)
  0x1000: FVMAIN_COMPACT (合計 0x127000)

[FV.FVMAIN_COMPACT]
  PeilessSec.efi (SEC/PrePi、FV先頭に必須)
  └─ FILE FV_IMAGE: LZMA圧縮されたFVMAIN
       └─ [FV.FVMAIN]: 全DXEドライバ + Shell
```

### Madt.aslc / Gtdt.aslc — ACPIテーブル（現在無効）

```
Madt.aslc: GICv3構成
  - GICD: 0x3400000
  - GICR: 0x3460000 (stride 0x20000 × 8コア)
  - 8コア: MPIDR 0x0000-0x0700

Gtdt.aslc: ARMタイマー
  - IRQ 29 (Secure Physical), 30 (NS Physical), 27 (Virtual), 26 (EL2)
  - DTBから確認済みの正確な値
```

Windows ARM 起動には有効化が必要 → DSC/FDF の `#AcpiTables` コメントを外す

---

## 5. 確認済みハードウェア情報

| 項目 | 値 | 確認方法 |
|------|-----|---------|
| CPU | Cortex-A76 × 2 + Cortex-A55 × 6 | DTB |
| RAM | LPDDR4 1024MB | boot0ログ |
| GIC | GICv3 | DTB |
| GICD | `0x03400000` | DTB |
| GICR | `0x03460000` | DTB |
| UART0 | `0x02500000`, 16550互換, HOSC 24MHz | DTB |
| ARMタイマー IRQ | 29 / 30 / 27 / 26 | DTB |
| PSCI | 1.0 / SMC方式 | DTB |
| TF-A BL31 | boot0内蔵・EL3で動作 | 起動ログ |
| TF-A バージョン | v2.5(debug):5fc237a6a (2025-02-26) | 起動ログ |

---

## 6. 今後のロードマップ

### Phase A — ACPI テーブル完成（Windows ARM の前提条件）

Windows ARM は ACPI 必須。現在 MADT・GTDT は作成済みだが無効化中。

| テーブル | 状態 | 優先度 | 内容 |
|---------|------|--------|------|
| MADT | 作成済み・無効 | 高 | 有効化するだけ |
| GTDT | 作成済み・無効 | 高 | 有効化するだけ |
| FADT | **未作成** | 高 | 電源管理フラグ・PSCI宣言 |
| DSDT | **未作成** | 高 | CPU・UART・eMMCデバイス記述 |
| SPCR | **未作成** | 高 | シリアルコンソール宣言（Windows必須）|
| PPTT | **未作成** | 中 | CPU トポロジ (big.LITTLE 構成) |
| CSRT | **未作成** | 低 | システムリソース（DMA等）|

作業内容:
1. `AcpiTableDxe` を DSC/FDF に追加
2. `AcpiTables.inf` のコメントアウトを外す
3. FADT / DSDT / SPCR を新規作成

### Phase B — eMMC/SD ドライバ（Windows インストール先の確保）

Windows インストール先となる eMMC を UEFI から認識させる。

```
必要: SunXI SDMMC DXE ドライバ
参考: awwiniot/UEFI-aw1689 の Sunxi SDMMCドライバ
      linux/drivers/mmc/host/sunxi-mmc.c (レジスタ仕様の参考)
```

A733 の SDMMC レジスタは Allwinner H616 と近い可能性あり。調査が必要。

### Phase C — Windows ARM インストール試行

- Secure Boot 無効（UEFI 変数で設定）
- UUPdump または MSDN から Windows ARM ISO 取得
- Rufus で起動 USB 作成 → VL812 USB HUB 経由で接続
- インストーラー起動確認

---

## 7. 既知の問題・TODO

### Image Section Alignment 警告（低優先）

```
!!!!!!!!  Image Section Alignment(0x1000) does not match Required Alignment (0x10000)  !!!!!!!!
```

`DXE_RUNTIME_DRIVER` モジュール群に出る警告。実際の動作は問題なし。
`ProtectUefiImage` が画像プロパティを作れないが、メモリ保護が効かないだけ。
**対処**: FDF に `ALIGN = 0x10000` を `DXE_RUNTIME_DRIVER` ルールに追加すれば消える。後回しで可。

### Variable ストレージが RAM エミュレーション

```
Variable driver will work at emulated non-volatile variable mode!
```

NV フラッシュ (SPI) ドライバが未実装のため UEFI 変数は再起動で消える。
ConOut 変数等は毎回 `PlatformBootManagerBeforeConsole` で設定し直しているので現時点では問題なし。
将来的に Windows が変数を書き込む場合は対処が必要。

### GetMpCoreInfo の MPIDR が不完全

`A733Platform.c` の `mA733CoreInfoTable` が 4 コア定義になっている（コメントに 4 コアと書いてある）が、実際は 8 コア。PcdCoreCount=8 と矛盾している。現状は CPU1 でシングル動作なので問題ないが、マルチコア使用時に修正が必要。

### UEFI Shell の使えないコマンド

`memmap`, `dh` 等は `UefiShellDebug1CommandsLib` が必要で未追加。
追加方法:
```dsc
ShellPkg/Application/Shell/Shell.inf {
  <LibraryClasses>
    NULL|ShellPkg/Library/UefiShellDebug1CommandsLib/UefiShellDebug1CommandsLib.inf
```

---

## 8. デバッグ Tips

### シリアルログの読み方

```
[A733] xxx         ← Platform固有のデバッグ出力 (DbgStr or DEBUG())
Loading driver ... ← DXEコアがドライバをロード中
InstallProtocol... ← プロトコルのインストール（ドライバ起動の証拠）
[Bds] Entry...     ← BdsDxeが起動 (DXE完了のサイン)
UEFI Interactive Shell v2.2  ← Shell正常起動
Shell>             ← 入力待ち
```

### クラッシュ場所の特定

AutoGen.c の行番号から特定:
```
/home/linux/edk2/Build/A733/DEBUG_GCC/AARCH64/<module>/DEBUG/AutoGen.c
```
`ASSERT_EFI_ERROR` がどのコンストラクタで止まったかが分かる。

### 逆アセンブルによるデバッグ

```bash
# DLL ファイルを逆アセンブル
aarch64-linux-gnu-objdump -d Shell.dll | less

# 特定アドレス付近を確認（LRレジスタ値から逆算）
aarch64-linux-gnu-objdump -d Shell.dll | grep -A 10 "7c00:"
```

### コンソールが出ない場合のチェックリスト

1. `[A733] PlatformBootManagerBeforeConsole: registering serial console` が出るか
2. `Terminal - Mode 0, Column = 80, Row = 25` が出るか（TerminalDxe接続の証拠）
3. `InstallProtocolInterface: 387477C1-...` (SimpleTextIn) が出るか
4. `[A733] PlatformBootManagerAfterConsole` が出るか

---

*このドキュメントは session04 時点の内容。更新時は上部の日付と PROGRESS.md の決定事項ログを同時に更新すること。*
