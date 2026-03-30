# PortaRe0 ソフトウェア セッション終了処理

「終了処理して」と言われたら以下を自動で実行すること。

---

## 手順

1. **セッション原文を保存**
   ```
   python software/Claude/extract_session.py
   ```
   → `software/Claude/chat_logs/原文/YYYY-MM-DD_SessionNN.txt` に保存される

2. **PROGRESS.md 更新**（原文保存後に実施）
   - 「現在の作業箇所」を今日の作業内容に合わせて更新
   - 「直近の決定事項ログ」に今日の日付とセッション番号で決定事項を追記

3. **index.md 更新**（原文ファイルのL行番号を参照しながら）
   - `software/Claude/chat_logs/原文/index.md` に今回のセッションを追記
   - 主要トピックのL行番号はおおよその目安でOK

4. **ドキュメント更新確認**
   - 以下のファイルに今回の変更を反映すべきか確認する：
     - `software/Claude/CLAUDE.md` / `specs/*`（仕様変更・確定事項があった場合）
     - `software/Claude/PROGRESS.md`（進捗状況）

5. **session_close.py 実行**（上記がすべて完了してから）
   ```
   python software/Claude/session_close.py "Docs: sessionNN終了処理・PROGRESS/index更新"
   ```
   → PROGRESS.md の古いログを archive/ に移動（直近4件残す）
   → git add -A + commit + push
