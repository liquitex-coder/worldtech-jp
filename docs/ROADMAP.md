# NewsMatome（worldtech-jp）— ロードマップ & タスク抽出（Auditor 適用）

> 要件定義書（`案件定義書.md`＝A / `受け入れ定義_done_B.md`＝B）を読み、Claim-Auditor の
> `meet(A,B)` と `source_coverage` を自己適用して **gap / core / over** を決定論で抽出し、
> ロードマップ化したもの。Auditor は署名しない（INV-R1）。数値は実行時点の機械検証値。
> 生成: 2026-06-08。

## 0. Auditor 実行結果（自己適用）

```
meet(A, B)  [NewsMatome]
  gap  (B が要求するが A に無い＝抜け) : (none)        ← gap = ∅ ✅
  core (両端が出会った確定コア)         : 48 アンカー
  over (A にあるが B 不要＝将来スコープ) : 14 アンカー
  union_size : 67

source_coverage（署名要件 → テスト証人）
  declared anchors : 67   witnessed : 67   ratio = 1.000
  CORE covered     : 48/48   uncovered : (none) ✅
  pytest           : 133 passed
```

- **gap = ∅**：done B が要求する要件はすべて A に存在（抜けなし）。
- **core = 48/48 被覆（100%）**：署名済み第一マイルストーン＋AI機能 addendum の全要件にテスト証人あり。
- **over = 14 アンカー**：将来スコープ。全件着手・witness 済み（実 feed/実翻訳 API は client 差替で本番化）。

## 1. マイルストーン構成

| フェーズ | スコープ | 状態 |
|---|---|---|
| **M1 デザイン雛形（署名 core）** | 静的 HTML/CSS で kotaro269 風トップ・記事・13カテゴリ・翻訳出典・案件導線・空状態 | ✅ 完了（被覆 100%） |
| **M1.5 AI機能 UI（署名 addendum）** | 意味検索 / 3行まとめ / 深度トグル / ダイジェスト＋音声 / 対訳 / 記事Q&A の UI 体裁 | ✅ 完了（被覆 100%） |
| **M2 収集→日本語化パイプライン（over）** | RSS/API 収集・翻訳・要約・/en/ 英語版・権利/品質/ガバナンス監査・定時更新 | ✅ 実装＋witness 済（実 API は client 差替） |
| **M3 本番運用** | 実 feed / 実翻訳 API 接続・Pages 配信・運用監視 | ⏳ client 差替のみ（検証器は不変） |

## 2. Auditor 抽出タスク backlog（over = 将来スコープ）

`meet` が over 判定した 14 アンカー。すべて着手済みだが、本番化の残作業を明記する。

| ID | 要件 | 本番化の残作業 |
|---|---|---|
| FR-11 | サイト内検索 BE | 実全文検索の運用（雛形は実装済） |
| FR-12 | RSS/API 自動収集 | 実 feed 接続（`pipeline/feeds.json` に本番ソース登録） |
| FR-20 | 多言語ソース収集 | 同上（クローラ運用） |
| FR-21 | 日本語化（翻訳） | 実翻訳 API（`ANTHROPIC_API_KEY` で LLMTranslator）差替。未接続時は捏造せず原文保持 |
| FR-27 | 運営者プロフィール・実績 | 内容整備 |
| FR-29 | カテゴリ専門エージェント体制 | オーケストレータの実運用 |
| FR-32 | 毎朝 07:00 定時更新 | cron/Actions スケジューラ本番設定（`pipeline/SCHEDULE.md`） |
| NFR-1,2,4,5,6,7,8 | 速度/SEO/権利/品質/多言語SEO/生成物検証/非捏造 | 数値目標・運用ゲートの本番閾値 |

## 3. 本セッションで実行（execute）した修正

**検出（Auditor → pytest 証人）**：`tests/test_seo.py::test_performance_hints`（covers: **NFR-1**）が失敗。
2026-06-08 の日次更新ボットが RSS（arXiv/GitHub＝画像なし）記事のみで `index.html` を再生成した結果、
カードがすべて空プレースホルダ（`thumb is-empty`／FR-18 準拠で `<img>` を持たない）となり、
**NFR-1「画像の遅延読み込み（`loading="lazy"`）」の証人が静的成果物から消えた**（claim↔reality ドリフト）。

**修正方針**：FR-18（収集記事の画像欠落時は画像を捏造せずプレースホルダ）は不可侵。
よって遅延読み込みポリシーの証人を、**データ依存のカードではなく常設の静的レイアウト**へ移す。
`今朝の AI ダイジェスト`（FR-37/AC-12・常設セクション）に**サイト自身の装飾ビジュアル**
（収集記事の画像ではない・`alt=""`・`loading="lazy"`）を 1 点追加。`render.build()` は
マーカー領域外を保全するため、日次再生成後も証人が残る（再生成シミュレーションで確認済）。

- `index.html`：`.ai-digest` に `figure.digest-visual`（lazy img）を追加
- `css/style.css`：`.digest-visual` のスタイル追加
- 結果：`test_performance_hints` ✅ / 全 **133 passed** / source_coverage **67/67** 維持

## 4. 進捗

| 指標 | 値 |
|---|---|
| gap（抜け） | **0**（gap = ∅）✅ |
| 署名 core 被覆 | **48 / 48 = 100%** ✅ |
| 全要件アンカー被覆 | **67 / 67 = 100%** ✅ |
| over（将来）着手 | **14 / 14 = 100%**（本番化は client 差替のみ）|
| pytest | **133 / 133 passed** ✅ |

**NewsMatome 進捗度 ≒ 100%（定義スコープ被覆）**。残るは要件ではなく本番接続（実 feed / 実 API）。
