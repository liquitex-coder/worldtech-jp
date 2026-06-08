"""多言語SEO（NFR-6）：hreflang 相互参照 ＋ /en/ 英語版エディションのテスト証人。"""
from pipeline.i18n import (
    build_en_edition,
    inject_hreflang,
    render_en_article,
    render_en_index,
)

ART = dict(id="x1", category="AI", kind="article", agent="AI担当エージェント",
           title_original="Self-verifying LLMs cut hallucinations",
           title_ja="自己検証するLLMが幻覚を減らす",
           body_original="A line of work shows models re-checking outputs.",
           body_ja="モデルが自らの出力を再検証する研究。",
           tldr=["a", "b", "c"], source_url="https://techcrunch.example/x",
           source_lang="en", translated=True, translation_engine="corpus(human-verified)",
           collected_at="2026-06-07T07:00:00+09:00",
           image="https://picsum.photos/seed/x/640/360")


def test_hreflang_injection_is_idempotent():
    # covers: NFR-6
    page = '<head>\n<link rel="canonical" href="https://s/x">\n</head>'
    once = inject_hreflang(page, "https://s/x", "https://s/en/x")
    assert 'hreflang="ja"' in once and 'hreflang="en"' in once and 'hreflang="x-default"' in once
    twice = inject_hreflang(once, "https://s/x", "https://s/en/x")
    assert once == twice                                  # 二重挿入しない（冪等）


def test_en_article_uses_original_language_not_fabricated():
    # covers: NFR-6
    page = render_en_article(ART)
    assert '<html lang="en">' in page
    assert "Self-verifying LLMs cut hallucinations" in page   # 原文（英語）をそのまま掲出
    assert "A line of work shows models re-checking outputs." in page  # 原文本文（非捏造）
    assert 'hreflang="ja"' in page and 'hreflang="en"' in page  # 相互参照
    assert '"inLanguage":"en"' in page
    assert f'../../articles/{ART["id"]}.html' in page          # 日本語版への相互リンク


def test_en_index_links_and_hreflang():
    # covers: NFR-6
    idx = render_en_index([ART])
    assert '<html lang="en">' in idx
    assert 'rel="alternate" hreflang="ja"' in idx
    assert f'articles/{ART["id"]}.html' in idx


def test_en_index_card_container_is_styled():
    # covers: NFR-6
    # 回帰防止：EN版のカード格子は CSS で定義済みのクラスを使う（未定義 .cardgrid だと
    # 全カードが全幅化し空サムネが画面を覆い「空白」に見えるバグの再発を防ぐ）。
    import re
    from pathlib import Path
    css = (Path(__file__).resolve().parent.parent / "css" / "style.css").read_text(encoding="utf-8")
    idx = render_en_index([ART])
    assert '<div class="grid">' in idx                      # JA と同じ実証済みの格子
    assert "cardgrid" not in idx                            # 未定義クラスを使わない
    # EN index がカード格子に使う格子クラスは CSS に必ず定義がある
    assert re.search(r"\.grid\s*\{", css)                   # .grid 定義の存在を証人化


def test_build_en_edition_writes_pages(tmp_path):
    # covers: NFR-6
    import json
    from pipeline import i18n
    arts_path = tmp_path / "articles.json"
    arts_path.write_text(json.dumps({"articles": [ART]}, ensure_ascii=False), encoding="utf-8")
    index_path = tmp_path / "index.html"
    index_path.write_text('<head><link rel="canonical" href="https://s/"></head><body></body>', encoding="utf-8")
    # 出力先を tmp に向ける
    i18n.EN_DIR = tmp_path / "en"
    i18n.EN_ARTICLES_DIR = i18n.EN_DIR / "articles"
    i18n.NS = tmp_path
    (tmp_path / "articles").mkdir()
    ja = tmp_path / "articles" / f'{ART["id"]}.html'
    ja.write_text('<head><link rel="canonical" href="https://s/articles/x1.html"></head>', encoding="utf-8")
    res = build_en_edition(arts_path, index_path)
    assert (i18n.EN_DIR / "index.html").exists()
    assert (i18n.EN_ARTICLES_DIR / f'{ART["id"]}.html').exists()
    assert 'hreflang="en"' in ja.read_text(encoding="utf-8")   # JA 側に hreflang 注入
    assert res["en_pages"] == 2
