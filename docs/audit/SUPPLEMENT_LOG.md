# Auditor 自己適用ログ — NewsMatome 要件補足（meet A↔B）

決定論・LLM-free の `claim_auditor.analysis.requirement_gap.meet(A, B)` を案件定義書 A と
受け入れ定義 done B に適用した記録。Auditor は署名しない（gap は署名まで advisory・INV-R1）。

実行：`cd C:\Users\user\Claim-Auditor; PYTHONUTF8=1 python ..\news-site\docs\audit\run_supplement.py`

---

## ラウンド1 — 2026-06-07（A v0.1.0 / B v0.1.0, 初版デザイン雛形スコープ）

- **gap (抜け)** = `AC-7, FR-17, FR-18, FR-19`
  - done B が要求するが A に無い：パンくず(FR-17)・サムネ欠落プレースホルダ(FR-18)・
    空状態(FR-19)・空/欠落ロバスト性(AC-7)。
- **対応**：A §3.1 に Auditor 補足条項（provisional / proposed_by=auditor・未署名）として収録。
- core=20 / over=6（FR-11/12/16, NFR-1/2/4 を将来スコープに分離）。

## ラウンド2 — 2026-06-07（A v0.2.0 / B v0.2.0, liquitex 指示でスコープ拡大）

liquitex 指示：**多言語収集→日本語化**・**9カテゴリ**（サイエンス/AI/テクノロジー/コード/
アルゴリズム/動画/動物/自然/農業）・**案件獲得導線**を加算。

- A §3.2 拡張要件 FR-20〜FR-27、NFR-5/6、AC-8/9/10 を加算。B の Bwd も対応加算。
- **gap (抜け)** = `(none)` → **閉鎖（∅）**
- **core (確定)** = 32 アンカー：
  AC-1〜AC-10, FR-1/2/3/4/5/6/7/8/9/10/13/14/15/17/18/19/22/23/24/25/26, NFR-3
- **over (将来スコープ / advisory)** = 11 アンカー：
  FR-11(検索BE), FR-12(RSS/API収集), FR-16(広告), FR-20(多言語収集機構),
  FR-21(翻訳パイプライン), FR-27(実績ページ作り込み),
  NFR-1(速度目標), NFR-2(SEO), NFR-4(権利運用), NFR-5(翻訳品質), NFR-6(多言語SEO)
- defined=True / no_meeting=False / union_size=43

### 解釈
第一マイルストーン（デザイン雛形）の done と A が**過不足なく一致**。
多言語収集・翻訳の**実パイプライン**と収益化は正しく over（将来）へ分離され、
それらの**表示・体裁**（翻訳ラベル/出典・コード/動画・案件導線）だけが core に入っている。
＝「見た目を先に確定し、収集/翻訳は後から載せる」方針と機械的に整合。

## ラウンド3 — 2026-06-07（A v0.3.0 / B v0.3.0, 収集4型・案件3種・モダン技術メディア風）

liquitex 確定指示：収集ソース**4型**（ニュース/ブログ・論文arXiv・GitHub/コード・YouTube/動画）、
案件**3種**（受託開発・翻訳/メディア代行・広告/アフィリ）、デザイン＝**モダン技術メディア風**。

- A に **FR-28（論文記事の体裁）** 追加、**FR-16（広告→広告/アフィリ枠・体裁は第一段階）** を core 化。
  AC-9 に広告/アフィリ枠、AC-10 を「収集4型の記事体裁」へ拡張。B の Bwd に FR-16/FR-28 を加算。
- **gap (抜け)** = `(none)` → **閉鎖（∅）維持**
- **core (確定)** = 34（+FR-16, +FR-28）
- **over (将来 / advisory)** = 10：FR-11(検索BE), FR-12(RSS/API収集), FR-20(多言語収集機構),
  FR-21(翻訳パイプライン), FR-27(実績ページ作り込み), NFR-1/2/4/5/6
  ※広告/アフィリは**枠の体裁=core / 配信・計測タグ実装=over** に分離。
- defined=True / no_meeting=False / union_size=44

## ラウンド4 — 2026-06-07（A v0.4.0 / B v0.4.0, エージェント体制・面白記事・加算デフォルト運用）

liquitex 指示：①**要件の途中追加を既定運用に**（§0 加算デフォルト）②**各カテゴリに専門エージェント配置**
③**息抜き用の面白記事**（後）。

- A に §0（加算デフォルト運用）、§3.3（FR-29 エージェント体制／FR-30 バイライン表示／FR-31 面白カテゴリ）、
  NFR-7（エージェント生成物の検証）、AC-11（バイライン表示）を加算。
- **ID トークン落とし穴を再現＆修正**：B の AC-11 派生行に `FR-29` と綴ったため `meet()` が
  Bwd に取り込み FR-29 が誤って core 化。トークンを散文へ置換し再実行 → FR-29 は over へ復帰。
  （教訓：B には「required な ID」だけを綴る。実体=将来の ID を B に書かない）
- **gap (抜け)** = `(none)` → **閉鎖（∅）維持**
- **core (確定)** = 36（+FR-30 バイライン体裁, +AC-11）
- **over (将来 / advisory)** = 13：FR-11, FR-12, FR-20, FR-21, FR-27, **FR-29(エージェント体制実装)**,
  **FR-31(面白カテゴリ)**, NFR-1, NFR-2, NFR-4, NFR-5, NFR-6, **NFR-7(生成物検証)**
- defined=True / no_meeting=False / union_size=49

### 解釈
「エージェント体制」は **実装=over / バイライン体裁=core**、「面白記事」は **後＝over** に正しく分離。
加算4ラウンドで一貫して gap=∅ を維持＝§0 の加算デフォルト運用が機能している。

## ラウンド5 — 2026-06-07（A v0.5.0 / B v0.5.0, カテゴリ 9→11 拡張）

liquitex 指示：**ロボット技術**・**フィジカルAI（身体性AI）** をテーマに追加 → カテゴリ **9→11**。

- FR-23（分類軸）と FR-29（エージェント体制）の対象を 11 カテゴリへ更新、AC-8 を「11分類」に。
  **新規 ID は追加せず**（カテゴリは FR-23 の値拡張）。B 側も 9→11 表記へ同期。
- **gap (抜け)** = `(none)` → **閉鎖（∅）維持**
- **core / over とも前ラウンドから不変**：core=36 / over=13 / union_size=49。
  ＝「分類の値が増えても要件アンカー集合は不変」を Auditor が確認（ID 設計が値拡張に対し安定）。

## ラウンド6 — 2026-06-07（A v0.6.0 / B v0.6.0, アート・デザイン追加＋毎朝7時更新）

liquitex 指示：①**アート**・**デザイン** をテーマ追加 → カテゴリ **11→13**。②**情報は毎朝7時に更新**。

- FR-23/FR-29/AC-8 を 13 カテゴリへ（値拡張・新規 ID なし）。
- **FR-32（定時更新：毎朝07:00 JST に収集→翻訳→公開）** を §3.3 に加算。収集機構の運用なので **over（将来）**。
  更新日時の**表示**体裁は既存 FR-14（core）で充足。
- **gap (抜け)** = `(none)` → **閉鎖（∅）維持**
- **core (確定)** = 36（不変）／**over** = 14（**＋FR-32**）／union_size=50
- 解釈：カテゴリ2件は値拡張で集合不変。定時更新は「運用=over／更新時刻表示=core(FR-14)」に分離。

## ラウンド7 — 2026-06-07（A v0.7.0 / B v0.7.0, 2D に "AIならでは" addendum）

liquitex 指示：3D は探索モードとして後回し、**主役は 2D のまま**「人間が手作業ではできない情報処理」を
UI として足す。選択＝**4機能すべて**（意味検索・関連／3行まとめ・深度／今朝のダイジェスト・音声／対訳・質問）。

- A §3.4（FR-33〜FR-40）・NFR-8・AC-12〜AC-15 を **add-only の addendum（未署名）** で加算。
  署名済み milestone-1（FR-1..32/AC-1..11）は不可侵（INV-R4）。§署名表に addendum 用の `_未署名_` 行を追加。
- 原則 **UI体裁=core（第一段階の雛形に出す）／ 実エンジン(埋め込み/要約/TTS/RAG/リライト/整列)=over（将来）** で分離。
- **ID トークン落とし穴を再々現＆修正**：B の over 散文に `NFR-8` と綴り誤って core 化 → トークン除去で over へ復帰。
- **gap (抜け)** = `(none)` → **閉鎖（∅）維持**
- **core (確定)** = 48（+FR-33..40, +AC-12..15）／**over** = 15（+NFR-8）／union_size=63
- 解釈：AI4機能の **UI体裁は core**、**実処理は over** に正しく分離。捏造防止(NFR-8/INV-R2)はガバナンスとして over。

## 署名イベント1 — 2026-06-07（milestone-1 を root 化）
人間（liquitex 本名 **liquitex**）が `analysis.signing.fill_signature_table` 経由で
milestone-1（A: FR-1..32/AC-1..11＋本書全体／B: AC-1..11）を署名 → **root 確定**。
`audit/sign.py`、SHA-256 記録 `audit/signatures.jsonl`（anchor=NEWS_MATOME_REQUIREMENTS / NEWS_MATOME_DONE_B）。

## 署名イベント2 — 2026-06-07（AI機能 addendum を root 化）
liquitexが **§3.4/§1.3 の AI機能 addendum（A: FR-33..40・NFR-8・AC-12..15／B: AC-12..15）** を署名 → **root 確定**。
`audit/sign_addendum.py`（§署名表の2行目 `_未署名_` を fill、記録は append）。
anchor=NEWS_MATOME_REQUIREMENTS_AI_ADDENDUM（sha256 caf384e1…）/ NEWS_MATOME_DONE_B_AI_ADDENDUM（sha256 5bb02616…）。

## Phase A — source_coverage 被覆検証（Engine-N, 2026-06-07）
署名要件 → テスト証人（`# covers: AC-x`）の traceability を `analysis.source_coverage.measure`
（strict_witness）で機械検証。証人＝`tests/test_acceptance.py`（雛形の構造を決定論アサート）。

- **pytest**：`tests/test_acceptance.py` 15件 **PASS**（雛形が署名 AC を満たすことを実証）。
- **source_coverage**：declared 63 / witnessed 48。
  - **CORE（署名・実装済み）48/48 被覆 ＝ 100% ✅**（未被覆 core なし）
  - **OVER（将来）15 は未被覆（期待どおり）**：FR-11/12/20/21/27/29/31/32, NFR-1/2/4/5/6/7/8
- 実行：`run_coverage.py`。＝「署名した core はすべてテストで裏取り済み／将来分は正しく空欄」を Auditor が確認。

## Phase B — over 着手：収集→翻訳パイプライン scaffold（2026-06-07）
署名 core とは別レイヤーで over（将来）を**動く形**に着手。`pipeline/`（core.py 収集/統括/翻訳, run_daily.py, SCHEDULE.md）。

- **FR-20 収集**：`SampleCollector`（実 RSS/arXiv/GitHub/YouTube の差込口）。全項目 source_url 必須。
- **FR-29 エージェント統括**：13カテゴリ→専門エージェント、`Orchestrator` が割当・admission（segment_orchestrator 流）。
- **FR-32 定時バッチ**：`python -m pipeline.run_daily` → `data/articles.json`。時刻は引数（決定論）。cron/Task Scheduler は SCHEDULE.md。
- **NFR-8 非捏造**：翻訳エンジン未接続 → `PassthroughTranslator` が **None を返し嘘の日本語を作らない**。出典なしは admission で除外。原文は保持。
- **FR-21 翻訳は未実装** → **witness しない**（実装してないものを covered と主張しない）。
- **pytest**：`tests/`（acceptance 15 ＋ pipeline 5）＝ **20 PASS**。バッチ実行：collected=5 / translated=0/5（正直）。
- **source_coverage 再計測**：witnessed 52/63（0.825）。**CORE 48/48 維持**。**OVER 被覆 0→4/15**（FR-20/FR-29/FR-32/NFR-8）。
  残 over 未被覆（将来）：FR-11/12/21/27/31, NFR-1/2/4/5/6/7。

## Phase B+ — FR-21 翻訳エンジン接続（2026-06-07）
`pipeline/translate.py`：**翻訳出力＝提案、決定論検証器を通った提案だけ採用**（INV-R2）。
- `TranslationVerifier`：出典必須・**用語グロッサリ一貫性**（hallucination→幻覚, tactile→触覚 等）・長さ常識。
- `CorpusTranslator`（engine=corpus(human-verified)）：人手検証済み対訳を参照。**未収録/検証不合格は None＝捏造しない**（NFR-8）。本番は MT/LLM 提案に置換可（同検証器を必ず通す）。
- `run_daily` がこれを接続 → **translated=5/5**。`data/articles.json` に原文＋日本語＋出典＋担当エージェントを併記（FR-22/NFR-5）。
- `tests/test_translation.py` 5件（未収録→None / 用語ずれ・出典なし→reject / 全件翻訳＋出典）。
- **pytest 計 25 PASS**。source_coverage：witnessed 53/63（0.841）。**CORE 48/48 維持**、**OVER 被覆 5/15**（+FR-21）。
  残 over 未被覆：FR-11/12/27/31, NFR-1/2/4/5/6/7。

## Phase D — ループ閉鎖：データ駆動描画＋実収集（2026-06-07）
収集→翻訳→**描画**→（実feed）が一本に繋がった。

- **① データ駆動描画**：`pipeline/render.py`（静的サイト生成・SEO/速度のためビルド時HTML生成）。
  `index.html` の `<!-- CARDS:START/END -->` 間に articles.json を注入。画像なし→FR-18プレースホルダ、
  翻訳済み→日本語見出し＋翻訳バッジ（FR-22）、担当バイライン・出典ホスト。`run_daily` が collect→translate→render を一気通貫実行。
  証人 `tests/test_render.py` 5件。AC-14 の index witness は記事 tldr-lg へ（一覧は要約エンジン未実装＝TL;DR出さず捏造しない）。
- **② 実収集アダプタ**：`pipeline/collect_rss.py`（RSS2.0/Atom 汎用 → ニュース/arXiv/GitHub releases/YouTube を feed URL で吸収）。
  各 feed にカテゴリ/種別を事前割当、出典・題なしは除外、取得失敗feedはスキップ（NFR-8）。`SampleCollector` と同 `collect()` で Orchestrator に無改修で差替可。
  運用前に robots/ToS/引用範囲を確認（NFR-4・SCHEDULE.md/コード注記）。証人 `tests/test_collect.py` 3件。
- **pytest 計 33 PASS**。source_coverage：witnessed 54/63（0.857）。**CORE 48/48 維持**、**OVER 被覆 6/15**（+FR-12）。
  残 over 未被覆（将来）：FR-11 検索BE / FR-27 実績ページ / FR-31 面白カテゴリ / NFR-1/2/4/5/6/7。

## Phase E — 要約生成・記事ページ生成・実LLM翻訳経路（2026-06-07, 順次）
「提案→決定論検証→採用、未知/不合格は捏造しない」を全エンジンで貫く。

- **Task1 FR-35 要約生成**：`pipeline/summarize.py`（SummaryVerifier 出典必須/1〜3行/長さ＋人手検証済み CorpusSummarizer、未収録→[]）。
  Orchestrator に組込→ `Article.tldr` 充填。render がカードに TL;DR 表示。`tests/test_summarize.py` 4件。
  ※FR-35 は署名 core（UI）で既被覆＝被覆数は不変、エンジンを実体化（一覧カードに3行まとめ復活）。
- **Task2 記事ページ生成**：`render.render_article` / `build_articles` で各記事 → `articles/{id}.html`（個別ページ）。
  カードはそこへリンク。ページに 日本語見出し・原文出典リンク・**対訳（原文EN/JA併記）**・深度トグル・種別体裁（code/video/paper）・
  質問・関連・**空コメント状態**・footer＋JS。`tests/test_render.py` に +2。実機描画確認済。
- **Task3 実 MT/LLM 翻訳経路**：`translate.LLMTranslator`（注入 client の提案を **同じ TranslationVerifier** に通す）。
  良提案→採用 / 用語ずれ・API失敗→**None（捏造を採用しない）**。`tests/test_llm_translate.py` 4件。実APIは client 差替のみ（検証器不変）。
- **pytest 計 43 PASS**。source_coverage：**CORE 48/48 維持**、**OVER 6/15**（FR-12/20/21/29/32, NFR-8）。
  ＝今回は既存アンカー裏のエンジン実体化のため被覆数は不変。残 over：FR-11/27/31, NFR-1/2/4/5/6/7。

## Phase F — コードのグロー強化＋FR-11 全文検索（2026-06-07）
- **デザイン修正**：ナビの「コード」が黒(#111827)で暗背景に埋もれていた → **ナビ専用にシルバー#cbd5e1**（ターミナル質感）で上書き。
  ドット発光を二重 box-shadow で全体強化（hoverでさらに）。カードの黒コードチップは不変。`_nav` に NAV_GLOW 上書き。
  受け入れテストの「13カテゴリ」判定を `--cc:var(--c-` 個数→**13カテゴリ名の存在**へ（実装非依存・要件忠実）。
- **FR-11 全文検索**：`pipeline/search.py`（build_index/search＝部分一致＋頻度＋タイトル加点・決定論、空/無ヒット→[]）。
  `data/search-index.json` を run_daily で生成（クライアント絞り込み用）。日本語部分一致＋英語は原文ヒット。意味検索(FR-33)とは別。
  `tests/test_search.py` 4件。**pytest 計 47 PASS**。source_coverage：**CORE 48/48 維持**、**OVER 7/15**（+FR-11）。
  残 over：FR-27 実績ページ / FR-31 面白カテゴリ / NFR-1/2/4/5/6/7。

## Phase G — カテゴリナビのプルダウン・グループ化（2026-06-07）
liquitex 指示：似たカテゴリをプルダウンでまとめる。**AI ▾（AI/フィジカルAI）**・**コード ▾（コード/アルゴリズム）**。

- 13カテゴリは**全て保持**（ドロップダウン内に格納）→ FR-23（13分類）は維持・要件ID不変。FR-10 ナビの表層刷新。
- CSS：`.catgroup`/`.dropdown`（hover/focus-within/.open で開く・透明ブリッジでホバー継続）。
  `.catnav-inner` を `overflow:visible`＋`flex-wrap:wrap` に（ドロップダウン非クリップのため）。
- markup：index.html / article.html / `render._nav`(NAV_TOP 構成) の3箇所をグループ化。タッチ用に `.cat-trigger` クリックトグル JS を3ページへ。
- 受け入れテスト：13カテゴリ名は全て存在（ドロップダウン項目含む）→ **pytest 47 PASS 維持**。CORE 48/48・OVER 7/15 変化なし（UI刷新のため）。
- 実機検証：AI▾/コード▾ 表示、ドロップダウン display:flex・トリガー直下(gap6px・左揃え)・クリック開閉 OK。

## Phase H — FR-27 運営者プロフィール・実績ページ（2026-06-07）
案件獲得の信頼土台。`about.html`（サービス3種＝受託開発/翻訳・メディア運用代行/記事広告、実績サマリ stat-card、
ケース、運営者プロフィール liquitex、お問い合わせフォーム #contact）。グループ化ナビ・footer 共通。
topbar/サイドバー/生成記事の CTA「お仕事のご依頼」を `about.html#contact` へ結線。CSS に about セクション追加。
`tests/test_about.py` 2件。**pytest 49 PASS**。source_coverage：**CORE 48/48 維持**、**OVER 8/15**（+FR-27）。
残 over：FR-31 面白カテゴリ / NFR-1/2/4/5/6/7。実機 eval 確認済（hero/サービス3/stats/profile/contact）。

## Phase I — カテゴリ再編・新カテゴリ・言語選択・面白カテゴリ（2026-06-07）
liquitex 指示：ロボット技術→AIへ統合、日本のAI追加、テクノロジー→サイエンスへ統合、言語選択追加、面白＝[アニメ/ガジェット/漫画]。
英語版は **別サイトにせず `/en/` サブディレクトリ＋hreflang を推奨**（SEO・ドメイン評価集約）と回答。

- **A §3.5 addendum（未署名）**：FR-41 カテゴリ再編・拡張／FR-42 言語選択／AC-16・AC-17。署名13カテゴリ(FR-23)は不可侵で全存続（add-only, INV-R4）。FR-31(面白)を over→着手。
- **ナビ統合（プルダウン）**：サイエンス[+テクノロジー] / AI[+フィジカルAI,ロボット技術,**日本のAI**] / コード[+アルゴリズム] / **面白[アニメ,ガジェット,漫画]**。
  index/article/about の静的ナビ＋`render._nav`＋色(CATEGORY_COLOR/CSS vars 同期)。言語選択UI（日本語/EN, `/en/`は将来）をヘッダー4箇所に。
- **meet(A,B)**：gap=∅（FR-31/41/42・AC-16/17 が core 入り）。
- **source_coverage**：CORE 48/48 維持。**OVER 9/15**（+FR-31）。残 over=**NFR-1/2/4/5/6/7 のみ**。新 addendum FR-41/42・AC-16/17 は witness 済（未署名）。
- `tests/test_nav.py` 5件。**pytest 54 PASS**。eval 確認：top-level 11＋AI/サイエンス/コード/面白 ドロップダウン、言語選択。

## Phase C — デザイン/機能の調整（2026-06-07）
- **モバイル品質点検**：index（ダークグロウナビ・今朝のAIダイジェスト・カード）／article（TL;DR・深度トグル・
  対訳ビュー・記事に質問・関連）を 375px で検査 → **横溢れゼロ・1カラム化・ナビ横スクロール正常**＝崩れなし（修正不要）。
- **軽量化**：全 `<img>` に `loading="lazy" decoding="async"` を付与（NFR-1 方向の体感速度向上）。
- テスト：再実行 20 PASS（壊れなし）。

## 現在の確定状態 — INV-R1
A・B とも **signed**。core 48 アンカー（milestone-1＋AI addendum）が **root**。over 15 は将来スコープ（未署名・advisory）。
Auditor／Claude は署名を捏造しない（署名はliquitexの決定を機械転記したもの）。署名済み条項は不可侵（add-only, INV-R4）。
