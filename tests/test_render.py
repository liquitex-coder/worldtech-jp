"""データ駆動描画（静的サイト生成）のテスト。articles.json → カードHTML。"""
from pipeline.render import render_card, render_cards


def _art(**kw):
    base = dict(id="sample01", category="AI", kind="article", agent="AI担当エージェント",
                title_original="Self-verifying LLMs", title_ja="自己検証するLLM",
                body_original="Original EN body.", body_ja="日本語の本文。",
                source_url="https://techcrunch.example/x", source_lang="en",
                translated=True, collected_at="2026-06-07T07:00:00+09:00", image="")
    base.update(kw)
    return base


def test_translated_card_shows_japanese_title_and_badge():
    # covers: FR-22, FR-30
    html = render_card(_art(image="https://picsum.photos/seed/x/640/360"))
    assert "自己検証するLLM" in html                     # 翻訳済みは日本語見出し
    assert "EN→JA 翻訳" in html                          # 翻訳バッジ
    assert "AI担当エージェント" in html                  # バイライン
    assert "出典: techcrunch.example" in html            # 出典ホスト


def test_imageless_card_uses_placeholder():
    # covers: FR-18
    html = render_card(_art(image=""))
    assert "thumb is-empty" in html                      # サムネ欠落→プレースホルダ
    assert "<img" not in html


def test_untranslated_card_is_honest():
    # covers: NFR-8
    html = render_card(_art(translated=False, title_ja=None))
    assert "Self-verifying LLMs" in html                 # 未翻訳は原文見出し
    assert "未翻訳" in html                               # 捏造せず未翻訳と明示


def test_empty_list_renders_empty_state():
    # covers: FR-19
    assert "empty-state" in render_cards([])             # 0件は空状態


def test_html_is_escaped():
    html = render_card(_art(title_original="<script>", title_ja=None, translated=False))
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_article_page_is_data_driven_with_original_and_ja():
    # covers: FR-5, FR-13, FR-22, FR-39
    from pipeline.render import render_article
    a = _art(id="abc123", body_original="Original EN body.", body_ja="日本語の本文。",
             image="https://picsum.photos/seed/x/640/360",
             tldr=["要点1", "要点2", "要点3"])
    other = _art(id="zzz999", title_ja="別の記事")
    page = render_article(a, [other])
    assert "<h1>自己検証するLLM</h1>" in page             # FR-5 日本語見出し
    assert 'href="https://techcrunch.example/x"' in page  # FR-13 原文出典リンク
    assert "Original EN body." in page and "日本語の本文。" in page  # FR-39 対訳（原文併記）
    assert "AI 3行まとめ" in page                          # TL;DR
    assert "別の記事" in page                              # 意味で繋ぐ関連
    assert "0件のコメント" in page                         # 空コメント状態（FR-19）


def test_code_and_video_and_paper_bodies():
    # covers: FR-24, FR-25, FR-28
    from pipeline.render import render_article
    base = dict(_art(id="k"))
    code = render_article({**base, "kind": "code"}, [])
    video = render_article({**base, "kind": "video"}, [])
    paper = render_article({**base, "kind": "paper"}, [])
    assert "codeblock" in code                            # FR-25
    assert "video-embed" in video                         # FR-24
    assert "paper-card" in paper                          # FR-28
