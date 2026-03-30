# Windows ARM on Cubie A7Z（Allwinner A733）

> 調査日: 2026-03-17（session01）
> ステータス: Linux公式イメージ動作確認済み / 環境整備待ち

---

## 目標

Cubie A7Z（Allwinner A733）上で Windows ARM を起動させる。
ロマン枠・時間無制限。実用性より「動いた」がゴール。

---

## SoC スペック（Allwinner A733）

| 項目 | 詳細 |
|------|------|
| CPU | Cortex-A76 × 2 + Cortex-A55 × 6（big.LITTLE、最大2.0GHz）|
| GPU | Imagination BXM-4-64 |
| NPU | 3 TOPS |
| プロセス | 12nm |
| メモリ | LPDDR4/4X/5、最大16GiB |
| ストレージ | UFS 3.0、eMMC 5.1 |
| 発売 | 2024年 |

---

## 利用可能なリソース

| リソース | URL | 備考 |
|---------|-----|------|
| Radxa 公式ドキュメント | https://docs.radxa.com/en/cubie/a7z | |
| Radxa BSP カーネル（Linux 5.15） | https://github.com/radxa/kernel `allwinner-aiot-linux-5.15` | |
| Radxa U-Boot | https://github.com/radxa/u-boot `cubie-aiot-v1.4.6` | |
| Allwinner 公式 SDK（Tina5.0） | https://gitlab.com/tina5.0_aiot | NDA不要・A733データシート含む |
| U-Boot mainline パッチ（v2） | https://lists.denx.de/pipermail/u-boot/2025-November/603430.html | [PATCH 00/11] 未マージ |
| Armbian 対応議論 | https://forum.armbian.com/topic/56130-radxa-cubie-a7aa7z-allwinner-a733/ | |
| Arch Linux ARM for A733 | https://github.com/hqu-little-boy/archlinuxarm-a733 | A7A向けだがA7Zも近い |
| radxa-build（ビルドシステム） | https://github.com/radxa-build/radxa-a733 | |
| linux-sunxi.org A733 | https://linux-sunxi.org/A733 | |

---

## ブートロードマップ

```
現在のブートチェーン（BSP）:
  SPL → [TF-A BL31？] → U-Boot → Linux

目標のブートチェーン:
  SPL → TF-A BL31 → EDK2（UEFI） → Windows ARM
```

---

## 作業ステップ

### Step 1: Linux 起動確認 ✅
- Radxa 公式 Debian イメージで動作確認済み

### Step 2: 現在のブートチェーン確認 ⏳
TF-A BL31 がすでに使われているか確認する。

```bash
# U-Boot起動ログを確認（BL31の文字があればTF-A使用中）
# または
cat /sys/firmware/devicetree/base/firmware/arm-trusted-firmware/compatible 2>/dev/null
strings /dev/mmcblk0 | grep -i "bl31\|trusted" | head -20
```

- **BL31あり** → Step 4（EDK2移植）へ直接進める
- **BL31なし** → Step 3（TF-A移植）が必要

### Step 3: TF-A BL31 を A733 に移植
- 参考: TF-A mainline の H616/A100 実装（`plat/allwinner/`）
- Allwinner SDK（Tina5.0）のデータシートでレジスタマップを確認
- EL3セキュアモニタが動けばOK

### Step 4: EDK2 を A733 向けに移植
- 参考1: RPi4 向け EDK2（https://github.com/pftf/RPi4）
- 参考2: 2017年の A64 向け断片実装（https://github.com/awwiniot/UEFI-aw1689）
- UEFI Shell 起動が最初のマイルストーン

### Step 5: Windows ARM インストール
- WoA Installer（https://worproject.com/）または DISM で展開
- この時点では「起動する」だけが目標

### Step 6: ドライバ対応（長期）
- USB / eMMC → 起動に必須
- GPU（Imagination BXM）→ Windows ドライバ要確認、長期戦

---

## 現状のブートチェーン（調査済み）

```
boot0(Allwinner SPL) → TF-A BL31（eMMC内蔵） → U-Boot（2024-03-20ビルド、UEFI無効）→ extlinux.conf → Linux
```

- TF-A BL31 はAllwinnerのboot0に埋め込まれ動作確認済み（eMMC文字列・PSCI smc確認）
- PSCI 1.0 / SMC方式 / CPU enable-method: psci
- `/boot/efi/` パーティションは存在するが空・未使用
- U-Boot に EFI/ACPI 文字列なし → UEFI 完全無効
- **TF-A移植は不要** → EDK2移植（BL33差し替え）に直接進める

---

## EDK2 移植に必要なコンポーネント（調査済み）

### 参考リポジトリ
| リポジトリ | 用途 |
|-----------|------|
| https://github.com/pftf/RPi4 | ブートフロー・FDF構造・ACPIテーブル記述方法 |
| https://github.com/awwiniot/UEFI-aw1689 | Allwinner固有実装（AXP PMIC・SMC・GICアドレス）|
| https://github.com/tianocore/edk2-platforms | ARM標準ライブラリ・DXEドライバ群 |

### 流用可能なコンポーネント
| コンポーネント | 流用元 | 備考 |
|--------------|--------|------|
| AXP PMIC ドライバ | awwiniot SunxiPlatformPkg | A733のPMICがAXP系なら流用可 |
| ACPI GTDT テーブル | 任意のARM SBC | IRQ 29/30/27/26 は全ARM共通 |
| DXEコアドライバ（CPU/GIC/Timer） | ArmPkg標準 | そのまま使用 |
| SerialPortLib | BaseSerialPortLib16550 | Allwinner UARTは16550互換 |

### 自作が必要なコンポーネント
- `ArmPlatformLib`（A733メモリマップ・固有初期化）
- `ResetSystemLib`（PMIC経由リセット）
- ~~TF-A BL31 A733ポート~~ → **不要**（boot0に内蔵済み）
- ACPI MADT（GICv3構成、アドレス確認済み）
- ACPI DSDT（UART/GPIO/eMMCデバイス記述）

### 最小ACPIテーブルセット（Windows ARM必須）
FADT + MADT + GTDT + DSDT

---

## A733 確認済みハードウェア情報（2026-03-19 調査5）

| 項目 | 値 |
|------|-----|
| GIC バージョン | **GICv3** |
| GIC Distributor | **0x3400000** |
| GIC Redistributor | **0x3460000** |
| ARMタイマー IRQ | **29, 30, 27, 26**（ARM標準） |
| PSCI バージョン | 1.0 / SMC方式 |
| PMIC | AXP系 / I2Cアドレス0x36 / twi@7083000 |
| TF-A BL31 | boot0内蔵・動作確認済み |

## 実装ステップ（更新版）

```
Step 1: A733 DTS から GIC/タイマーアドレス確認 ✅
Step 2: TF-A BL31 を A733 向けにポート ✅ 不要（boot0内蔵）
Step 3: EDK2 Platform Package 新規作成 ✅
Step 4: UART DEBUG() ログ取得 ✅ (session02)
Step 5: UEFI Shell 起動 ✅ (session04) ← 現在地
Step 6: ACPI テーブル完成（FADT/DSDT/SPCR追加）← 次のステップ
Step 7: eMMC/SD DXE ドライバ移植
Step 8: Windows ARM 起動
```

詳細な手順・ファイル構成・デバッグTipsは `specs/edk2_porting.md` を参照。

---

## 注意事項

- **GPU ドライバ**: Imagination BXM-4-64 の Windows ドライバが存在しない可能性が高い。「起動する」と「実用的に動く」は別問題。
- **Allwinner SDK は主に中国語ドキュメント**
- **U-Boot mainline A733パッチ**: v3投稿済み（2026-01-13）だが未マージ。v2026.07以降見込み。EDK2移植はマージ待ちせずBSPベースで進める。
- **DDR初期化**: SPL/ベンダーboot0が処理済みのためEDK2側では不要。
