# 定時更新スケジュール（FR-32 — 毎朝 07:00 JST）

パイプラインを毎朝 07:00（JST）に実行し、`data/articles.json` を更新する。
**「更新日時の表示」体裁は署名 core の FR-14（実装済み）**、**定時実行の運用は over（本書）**。

## Linux / macOS（cron, UTC運用なら 22:00 UTC = 07:00 JST）
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
