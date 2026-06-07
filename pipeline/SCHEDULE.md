# 定時更新スケジュール（FR-32 — 毎朝 07:00 JST）

パイプラインを毎朝 07:00（JST）に実行し、`data/articles.json` を更新する。
**「更新日時の表示」体裁は署名 core の FR-14（実装済み）**、**定時実行の運用は over（本書）**。

## 本番（推奨）：GitHub Actions
`.github/workflows/daily.yml` が **毎朝 07:00 JST（=22:00 UTC）** に自動実行し、
収集→日本語化→描画→`main` への commit/push まで行う（GitHub Pages が自動再デプロイ）。
手動実行は Actions タブの "Run workflow"。テスト緑が公開の前提（壊れていれば公開しない）。

- **実RSS収集**：`pipeline/feeds.json` に収集元を登録すると有効化（`feeds.example.json` 参照）。空ならサンプル。
- **実翻訳**：リポジトリ Secret `ANTHROPIC_API_KEY` を登録すると Claude API 翻訳が有効化。無ければコーパス/原文保持。
  モデル既定は `claude-opus-4-8`。コスト重視は変数 `NEWSMATOME_TRANSLATE_MODEL=claude-haiku-4-5` 等で上書き可。
- いずれも未設定なら **現状のサンプル記事**で日次更新される（サイトは壊れない・NFR-8）。

## 代替：Linux / macOS（cron, UTC運用なら 22:00 UTC = 07:00 JST）
```cron
# m h dom mon dow  command
0 22 * * *  cd /path/to/news-site && /usr/bin/python -m pipeline.run_daily --now "$(TZ=Asia/Tokyo date +\%Y-\%m-\%dT07:00:00+09:00)"
```

## Windows（Task Scheduler）
```powershell
$action  = New-ScheduledTaskAction -Execute "python" -Argument "-m pipeline.run_daily" -WorkingDirectory "C:\Users\user\news-site"
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00am
Register-ScheduledTask -TaskName "NewsMatome-daily" -Action $action -Trigger $trigger
```

## 注意（NFR-8 / 権利）
- 収集は**一次情報の出典 URL 必須**（無いものは admission で除外）。
- 翻訳エンジン未接続のうちは**未翻訳のまま出典付きで出力**（嘘の日本語を生成しない）。
- 本番収集を有効化する前に、各ソースの利用規約・robots・引用範囲を確認（NFR-4）。
