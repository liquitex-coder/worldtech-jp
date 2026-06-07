"""受け入れテスト — 署名済み AC/FR に対するテスト証人（source coverage 用）。

静的デザイン雛形（index.html / article.html / css/style.css）が、署名された
第一マイルストーン＋AI機能 addendum の受け入れ基準を満たすことを検証する。
各テストの ``# covers:`` 行が Claim-Auditor の source_coverage に拾われる証人マーカー
（署名要件 → テスト の traceability）。実行＝決定論・ネット不要（文字列/構造アサート）。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ARTICLE = (ROOT / "article.html").read_text(encoding="utf-8")
CSS = (ROOT / "css" / "style.css").read_text(encoding="utf-8")

CATS13 = ["サイエンス", "AI", "テクノロジー", "コード", "アルゴリズム", "ロボット技術",
          "フィジカルAI", "アート", "デザイン", "動画", "動物", "自然", "農業"]


def test_ac1_top_card_list_nav_breadcrumb():
    # covers: AC-1, FR-1, FR-2, FR-10, FR-14, FR-17, FR-23
    assert 'class="card"' in INDEX                      # FR-1 サムネ付きカード一覧
    assert 'class="chip"' in INDEX                      # FR-2 カテゴリラベル
    assert 'class="catnav"' in INDEX                    # FR-10 グローバルナビ
    assert "breadcrumb" in INDEX                        # FR-17 パンくず
    assert "2026/06/07" in INDEX                        # FR-14 投稿日/新着
    assert all(c in INDEX for c in CATS13)              # FR-23 13カテゴリ


def test_ac2_article_body_thumb_source_share():
    # covers: AC-2, FR-5, FR-7, FR-13, FR-22
    assert "article-body" in ARTICLE                    # FR-5 本文
    assert "article-figure" in ARTICLE                  # 大サムネ
    assert "source-bar" in ARTICLE and "原文" in ARTICLE  # FR-13 出典リンク
    assert "EN → JA" in ARTICLE                         # FR-22 翻訳ラベル
    assert 'class="share"' in ARTICLE                   # FR-7 SNSシェア


def test_ac3_sidebar_widgets():
    # covers: AC-3, FR-3, FR-4, FR-15
    assert "catlist" in INDEX                           # FR-3 カテゴリ別件数
    assert "ranklist" in INDEX                          # FR-4 人気ランキング
    assert 'class="tags"' in INDEX                      # FR-15 タグクラウド


def test_ac4_comments():
    # covers: AC-4, FR-6
    assert "comments" in ARTICLE and "comment-form" in ARTICLE  # FR-6 コメント欄＋投稿フォーム


def test_ac5_responsive():
    # covers: AC-5, FR-9, NFR-3
    assert "@media (max-width: 680px)" in CSS           # FR-9 スマホ幅
    assert "@media (max-width: 940px)" in CSS           # NFR-3 モバイルファースト（段階的1カラム化）


def test_ac6_nav_pagination_share():
    # covers: AC-6, FR-8, FR-10, FR-7
    assert "pagination" in INDEX                        # FR-8 ページネーション
    assert "catnav" in INDEX                            # FR-10 グローバルナビ
    assert 'class="share"' in ARTICLE                   # FR-7 シェア導線


def test_ac7_placeholder_and_empty_state():
    # covers: AC-7, FR-18, FR-19
    assert "is-empty" in INDEX                          # FR-18 サムネ欠落プレースホルダ
    assert ".empty-state" in CSS                        # FR-19 空状態（ゼロ件）


def test_ac8_translation_attribution_13cat():
    # covers: AC-8, FR-13, FR-22, FR-23
    assert "badge-translate" in INDEX                   # FR-22 翻訳ラベル
    assert "出典" in INDEX or "原文" in ARTICLE          # FR-13 出典明示
    assert all(c in INDEX for c in CATS13)              # FR-23 13分類


def test_ac9_lead_cta_and_ad_slot():
    # covers: AC-9, FR-26, FR-16
    assert "cta-card" in INDEX and "お仕事のご依頼" in INDEX  # FR-26 案件導線CTA
    assert 'class="ad"' in INDEX                        # FR-16 広告/アフィリ枠


def test_ac10_four_content_types():
    # covers: AC-10, FR-24, FR-25, FR-28
    assert "video-embed" in ARTICLE                     # FR-24 動画埋め込み
    assert "codeblock" in ARTICLE                       # FR-25 コードブロック
    assert "paper-card" in ARTICLE                      # FR-28 論文要約


def test_ac11_agent_byline():
    # covers: AC-11, FR-30
    assert "byline-agent" in INDEX                      # FR-30 エージェント・バイライン（一覧）
    assert "article-byline" in ARTICLE and "エージェント" in ARTICLE


def test_ac12_morning_digest_and_audio():
    # covers: AC-12, FR-37, FR-38
    assert "ai-digest" in INDEX                         # FR-37 今朝のAIダイジェスト
    assert "聴く" in INDEX                               # FR-38 聴くニュース（音声）


def test_ac13_semantic_search_and_related():
    # covers: AC-13, FR-33, FR-34
    assert "search semantic" in INDEX                   # FR-33 意味検索
    assert "ai-related" in ARTICLE                      # FR-34 意味で繋ぐ関連記事


def test_ac14_tldr_and_depth_toggle():
    # covers: AC-14, FR-35, FR-36
    # AC-14 は「カード／記事に」TL;DR。記事ページの tldr-lg を証人とする
    # （一覧カードは収集データ駆動で、要約エンジン未実装のうちは TL;DR を出さない＝捏造しない）。
    assert "tldr-lg" in ARTICLE                         # FR-35 AI 3行まとめ（記事）
    assert "depthSeg" in ARTICLE                        # FR-36 深度トグル


def test_ac15_parallel_view_and_ask():
    # covers: AC-15, FR-39, FR-40
    assert "parallel" in ARTICLE                        # FR-39 対訳ビュー
    assert 'class="ask"' in ARTICLE and "この記事に質問" in ARTICLE  # FR-40 記事に質問
