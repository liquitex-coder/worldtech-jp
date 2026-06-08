# Phase K — インテリジェンス substrate（OSINT/競合情報）2026-06-08

> 加算デフォルト（§0 / INV-R4）に沿う追補。署名済み core 48 は不可侵。本 Phase は **over（advisory・未署名 draft）**。
> 確度・採否はコードが判定（決定論）、文章化のみ ML が提案（INV-R2 を踏襲）。`案件定義書.md §8` の続きとして読むこと。

## 1. このセッションで実装したもの（全て merged・公開ブランチ反映）

| 段 | 内容 | 主なファイル | PR |
|---|---|---|---|
| 運用自動化 | 毎朝07:00 JST 自動更新ワークフロー／実RSS配線／Claude翻訳アダプタ／アクセス解析(Cloudflare)＋管理ダッシュボード | `.github/workflows/daily.yml`, `pipeline/{feeds,llm_client,analytics,dashboard}.py` | #2 #3 |
| **substrate** | 事実ベース推論基盤：`Fact`/`Claim`/`Inference`/`Confidence`、Admiralty信頼度、独立性スコア（焼き直し畳み込み）、矛盾減衰、確度伝播、admission ゲート、タスキング雛形 | `pipeline/intelligence.py`, `docs/intelligence-substrate.md` | #4 |
| **A 収集** | 公開ソース(RSS/Atom)→`Fact` 写像。NFR-4 でホスト許可済みのみ採用。`intel_sources.json` 未登録ならフォールバック | `pipeline/intel_collect.py`, `pipeline/intel_sources*.json` | #5 |
| **B 記者** | substrate を消費し確度ラベル付き・出典つき記事を起草。`GroundingVerifier` が裏付けなき文を除外（非捏造）。`ANTHROPIC_API_KEY` で ML 起草、無ければ決定論投影 | `pipeline/reporter.py` | #6 |
| **C タスキング** | 「何を深掘りするか」を `価値×信頼度×コスト＋独立性` で決定（未取得チャネル優先） | `pipeline/tasking.py` | #7 |
| 接続 | `run_daily` に A→B→C を統合し `data/intel.json` 生成（publishable＝確度≥中 ＋ compliance 選別） | `pipeline/intel_pipeline.py` | #8 |
| 関係グラフ | 取引先・納品先・大株主を辺で結び、辺ごとに確度。`to_dict()` は可視化用 | `pipeline/intel_graph.py` | #9 |
| 可視化 | 公開ページ `intel.html`（確度バッジ＋出典リンク＋次タスク）。**実ソース未登録時は空状態**（デモ非公開） | `pipeline/intel_render.py`, `intel.html` | #10 |
| ナビ導線 | ニュース面トップバーに「📊 インテリジェンス」を**ビルド時に冪等注入** | `pipeline/intel_render.py`（`inject_intel_nav`） | #11 |

**テスト**：pytest **133 PASS**（substrate 11／A 6／B 6／C 6／接続 4／グラフ 5／可視化 7 等を追加）。全てオフライン・決定論・鍵不要。
**公開**：`https://liquitex-coder.github.io/worldtech-jp/intel.html`（空状態スタート）。ニュース面 `index.html` は不変。

## 2. 設計原理（この Phase の不変条件）

- **INV-R5（提案/判定の分離・新規 draft）**：**言語処理（抽出・文章化）は ML が「提案」、推論の確度と採否は「コード」が判定**。
  モデルは verdict に非ず（INV-R2 の延長）。確度はモデルに決めさせず、証拠（`Fact`）から決定論で計算する。
- **非捏造（INV-R2）**：出典（`source_url`）と原文 span（`raw_excerpt`）の無い主張は作らない／載せない。
  `intel.json` に出るのは publishable（確度≥中）かつ compliance（NFR-4）通過の項目のみ。
- **株式の扱い**：開示済みの**持分異動（取得・売却／大量保有報告書・13D・Form 4）のみ**を対象。非公開重要情報は対象外。
- **決定論**：同じ `Fact` 群なら必ず同じ結論・同じ確度（乱数なし・時刻は外部注入）。

## 3. 機能要件 追補（§3.6 として加算・未署名 draft・advisory）

| ID | 追加要件（提案） | 状態 |
|---|---|---|
| FR-43 | **事実ベース推論基盤**：`Fact/Claim/Inference/Confidence`、Admiralty 信頼度、独立性スコア、矛盾減衰、確度伝播、admission | 実装済 #4 |
| FR-44 | **実データアダプタ（A）**：公開ソース→`Fact`、NFR-4 ホスト許可。EDINET/EDGAR 等は実ホスト登録で本番化 | 実装済 #5（アダプタ雛形） |
| FR-45 | **記者エージェント（B）**：substrate 消費・確度ラベル付き・出典つき起草・grounding 非捏造・ML ゲート | 実装済 #6 |
| FR-46 | **タスキング層（C）**：価値×信頼度×コスト＋独立性で深掘り優先順位を決定 | 実装済 #7 |
| FR-47 | **周辺信号チャネル**：法定開示／取引先／納品先／電力／求人／株式(開示ベース) 等を信頼度グレード付きで定義 | 実装済 #4 |
| FR-48 | **intel パイプライン接続**：`run_daily` で `data/intel.json` 生成（ガバナンス選別） | 実装済 #8 |
| FR-49 | **Entity 関係グラフ**：企業間関係を辺で結び辺ごとに確度 | 実装済 #9 |
| FR-50 | **可視化公開ページ**：`intel.html`（確度・出典・次タスク）＋ニュース面ナビ導線。未登録時は空状態 | 実装済 #10 #11 |

> 署名（root 化）は liquitex の署名のみで成立（INV-R1）。本節は advisory のまま。

## 4. 次セッションでやること（優先度順・backlog）

### A. すぐ価値が出る（実データ化）
1. **実ソース登録**：`pipeline/intel_sources.json` に収集元を登録＋`pipeline/compliance.py` の `ALLOWED_SOURCES` に実ホスト（EDINET/EDGAR 等）を **ToS/robots 確認のうえ**追加。→ `intel.html` が実データ表示に切替。
2. **EDINET/EDGAR 構造化アダプタ**：法定開示は構造化（提出者/対象/比率/日付）なので NLP 不要で `Fact` 化できる。これを実装すると **関係グラフの実エッジ**（誰が誰の大株主か）も自動生成可能。
3. **`data/graph.json` 生成を `run_daily` に接続**：`intel_graph.build_entity_graph` の出力を書き出し、`intel_render` が既に対応している**関係グラフ節**を `intel.html` に表示。

### B. 知性を上げる
4. **記者の実 LLM 起草**：`ANTHROPIC_API_KEY`（Secret）登録で `LLMReporter` 稼働。`reporter.build_reporter` は配線済み。
5. **導出ルール（Inference 生成）**：複数 `Claim` から「誰も明言していない結論」を導く規則を実装（例：新規大株主＋増産局面→拡張投資フェーズ）。確度は前提の最小、`derived=True` で「推論」ラベル。
6. **タスキングの実ループ接続**：`next_task` が示す未取得チャネルを次サイクルで自動収集する閉ループ。

### C. 体験・到達範囲
7. **関係グラフの図形描画**：現状はリスト表示。SVG/ネットワーク図に。
8. **/en/ への intel 導線**＋`intel.html` の英語版（`i18n` の en テンプレートに追記）。
9. **関係グラフの確度フィルタ UI**（高確度のみ表示 等）。

### D. 運用（liquitex 側の操作が要るもの）
10. **Secret 登録**：`ANTHROPIC_API_KEY`（実翻訳・実記者）／`CF_BEACON_TOKEN`（Cloudflare 解析）。
11. **Workflow permissions = Read and write**（設定済みのはず。毎朝の自動 push に必須）。

## 5. 現状サマリ（2026-06-08 時点）

- **pytest 133 PASS**（全オフライン・決定論）。CORE 48/48 維持。
- `intel.html` 公開（空状態）。ニュース面に「📊 インテリジェンス」導線（ビルド時注入）。
- 確度・採否＝コード／文章化＝ML（提案）の分離を全段で維持。実データ・実 LLM は設定（ソース登録／鍵）で有効化、未設定でも決定論ベースラインで安全。
- 設計契約：`docs/intelligence-substrate.md`。
