# PortaRe0 ソフトウェア開発 セッションログ索引

## セッション別索引

| セッション | 日付 | ファイル | 主な内容 |
|-----------|------|---------|---------|
| Session00 | 2026-03-16 | （このセッションはログなし） | software/ フォルダ構成作成 |
| Session01 | 2026-03-17〜18 | 2026-03-16_Session01.txt | フレームワーク選定・任意ディストリ・Windows ARM調査・Cubie A7Z システム調査・EDK2ポート計画 |
| Session02 | 2026-03-20 | 2026-03-16_Session02.txt | EDK2 SD起動デバッグ・PEILESS_ENTRY特定・ArmConfigureMmu クラッシュ場所絞り込み |

### Session02 主要トピック行番号（2026-03-16_Session02.txt）
| トピック | 行番号 |
|---------|--------|
| PEILESS_ENTRY 特定（FV ZeroVector 解析） | L50頃 |
| MemoryInitPeiLib.c 診断プリント追加 | L300頃 |
| WSL heredoc backslash escaping 問題と対処 | L700頃 |
| ArmConfigureMmu クラッシュ確定（ログ23:22） | L1400頃 |

### Session01 主要トピック行番号（2026-03-16_Session01.txt）
| トピック | 行番号 |
|---------|--------|
| キーボード QMK 選定理由 | L40 |
| オーディオ TinyUSB 選定理由 | L57 |
| Armbian / 任意ディストリ方式 | L146 |
| Windows ARM ロードマップ | L304 |
| Allwinner A733 調査結果（SoCスペック・TF-A・EDK2状況） | L343 |
| Cubie A7Z システム調査（lsusb/lsblk/lscpu等） | L750頃 |
| ブートチェーン確認（extlinux、UEFI無効） | L950頃 |
| U-Boot mainline A733パッチ状況 | L1100頃 |
| EDK2 移植構成・参考リポジトリ分析 | L1300頃 |

---

## トピック別索引

| トピック | セッション | 備考 |
|---------|-----------|------|
| フォルダ構成 | session00 | software/Claude/ 整備 |
| RP2040 #1 フレームワーク（QMK） | session01 | specs/dev_plan.md |
| RP2040 #2 フレームワーク（TinyUSB UAC2） | session01 | specs/dev_plan.md |
| 任意ディストリ戦略（rootfs差し替え / DistroBox） | session01 | - |
| Windows ARM ロードマップ | session01 | specs/windows_arm.md |
| Cubie A7Z ブートチェーン | session01 | extlinux / UEFI無効 |
| EDK2 移植計画（RPi4参考・awwiniot流用） | session01 | specs/windows_arm.md |
| U-Boot A733 mainlineパッチ状況 | session01 | v3投稿済み・未マージ |
| PEILESS_ENTRY 特定手法（FV ZeroVector） | session02 | make_sd_image.py PEILESS_ENTRY=0x4A007550 |
| ArmConfigureMmu クラッシュ絞り込み | session02 | 次: ArmMmuLibCore.c 診断プリント |
| WSL heredoc backslash escaping 問題 | session02 | Windows側でスクリプト書いてWSL実行で解決 |
