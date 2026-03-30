# PortaRe0 ソフトウェア開発 仕様書

> **このファイルはソフトウェア開発用コンテキストのサマリ。** 変更時は PROGRESS.md の決定事項ログにも必ず記録すること。

## セッション開始手順

1. `git fetch && git status` で差分確認
2. **PROGRESS.md** を読む（現在地・次のタスク・直近の決定事項）
3. このファイル（START.md）でコンテキスト確認
4. 疑問があれば関連ログ・実機ログ・コミット差分を確認
5. 終了時は **PROGRESS.md** に決定事項と次アクションを追記

> 仕様の信頼優先順位: 原文ログ > specs/* > START.md > PROGRESS.md

---

## プロジェクト概要

Cubie A7Z SBCベースのクラムシェル型ポータブルPC（Cyberdeckスタイル）のソフトウェア開発。

**ハードウェア詳細仕様は `D:\Projects\PortaRe0\Claude\CLAUDE.md` 参照**（このリポジトリ外・参照のみ）

---

## ハードウェア構成（ソフト開発に関係する部分）

| コンポーネント | 詳細 |
|--------------|------|
| SBC | Cubie A7Z（OS: Linux） |
| キーボードMCU | RP2040 × 2（keyboard / audio シート） |
| キーマトリクス | 63キー（9COL × 8ROW）+ 1N4148Wダイオード |
| スライドパッド | 3DSスライドパッド（Molex FPC / GP27,GP28） |
| オーディオ | MAX98357A（I2S スピーカー） + PCM5102A（DAC） + TPA6132A2（ヘッドフォンアンプ） |
| ディスプレイ | LS055R1SX04（5.5インチ MIPI DSI）+ HDMIコントローラ基板 |
| USB HUB | VL812-Q7（USB3.0 4ポート） |
| M.2 SSD | PCIe接続（FPC経由） |

---

## エージェントの役割と作業方針

**この `agents/` 配下のドキュメントは、セッション開始時の文脈復元と次アクションの固定に使う。**

### セッション開始時にやること
- **タスク分析・計画**: PROGRESS.mdを読み、次にやるべきことを判断する
- **実装・検証**: 現在のコードとログを確認し、必要な修正を進める
- **レビュー**: 変更差分・挙動・副作用を確認する
- **デバッグサポート**: エラーログ解析・原因特定・修正方針の判断
- **ドキュメント管理**: PROGRESS.md・specs/* の更新

### やらないこと
- ハードウェア回路図の直接編集（KiCadはハードウェア側の作業）

---

## Codex CLI 呼び出し方法

```bash
codex exec --full-auto -C "D:/Projects/PortaRe0/software" "実装指示"
```

- `--full-auto`: 確認なしで自動実行（workspace内ファイルの読み書き可）
- `-C`: 作業ディレクトリ指定（必ず `software/` を指定）
- 指示は日本語でも英語でも可

---

## ディレクトリ構成

```
software/
  src/               ← ソースコード
    keyboard/        ← RP2040 キーボードファームウェア
    audio/           ← オーディオ設定・スクリプト
    system/          ← Linux側 設定・スクリプト
  agents/
    START.md         ← このファイル
    PROGRESS.md      ← 進捗・決定事項
    specs/           ← 詳細仕様
```

---

## 開発環境

| 用途 | ツール |
|------|--------|
| RP2040 ファームウェア | TBD（QMK / Pico SDK / KMK等） |
| ビルド | TBD |
| 書き込み | BOOTSEL（UF2ドラッグ&ドロップ）|
| Linux側 | SSH or 直接操作 |

---

## 開発ワークフロー

### 通常の開発サイクル

```
1. コード修正（Codex CLI で実装）
      ↓
2. ビルド + SDイメージ生成 + 書き込み（deploy.py）
      ↓
3. 実機確認（UARTシリアルログ）
      ↓
4. 結果を PROGRESS.md に反映して次の開始点を固定
```

### ビルド〜書き込みスクリプト（build/ 配下）

| スクリプト | 役割 | 実行タイミング |
|-----------|------|---------------|
| `deploy.py` | **メインスクリプト**。ビルド→SDイメージ生成→SD書き込みを一括実行。ドライブ選択UI付き | 実機テストしたいとき |
| `build_edk2.sh` | WSL上でEDK2をビルド、`A733.fd`を`build/`にコピー | deploy.pyが内部で呼ぶ（直接呼ばない） |
| `make_sd_image.py` | `boot0dump.bin` + `A733.fd` → `sd_boot.img`を生成 | deploy.pyが内部で呼ぶ（直接呼ばない） |
| `write_boot.py` | SDカードに書き込む（PhysicalDrive3 ハードコード・非推奨） | **使わない → deploy.pyを使う** |

```bash
# フル実行（ビルド → イメージ → SD書き込み）※管理者権限必要
python build/deploy.py

# ビルドをスキップ（イメージ → SD書き込みのみ）
python build/deploy.py --skip-build

# SD書き込みのみ（既存のsd_boot.imgをそのまま書く）
python build/deploy.py --skip-image
```

### Codex CLI（実装委任）

```bash
codex exec --full-auto -C "D:/Projects/PortaRe0/software" "実装指示"
```

### セッション管理

- 終了時は `agents/PROGRESS.md` に現在地・決定事項・次アクションを追記する
