"""SEO（NFR-2）・表示速度（NFR-1）のテスト証人。"""
from pathlib import Path

from pipeline.render import render_article

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ABOUT = (ROOT / "about.html").read_text(encoding="utf-8")


def _art():
    return dict(id="seo1", category="AI", kind="article", agent="AI担当エージェント",
                title_original="X", title_ja="日本語タイトル",
                body_original="EN body", body_ja="日本語本文",
                source_url="https://src.example/x", source_lang="en",
                translated=True, collected_at="2026-06-07T07:00:00+09:00",
                image="https://picsum.photos/seed/x/640/360", tldr=["a", "b", "c"])


def test_index_seo_meta():
    # covers: NFR-2
    assert 'property="og:title"' in INDEX                 # OGP
    assert 'rel="canonical"' in INDEX                     # canonical
    assert 'application/ld+json' in INDEX and '"WebSite"' in INDEX  # 構造化データ
    assert 'name="twitter:card"' in INDEX
    assert 'property="og:type"' in ABOUT


def test_article_structured_data():
    # covers: NFR-2
    page = render_article(_art(), [])
    assert '"NewsArticle"' in page                        # 記事の構造化データ
    assert 'rel="canonical"' in page
    assert 'property="og:type" content="article"' in page
    assert 'og:image' in page                             # サムネ OGP


def test_performance_hints():
    # covers: NFR-1
    assert 'loading="lazy"' in INDEX                      # 画像遅延読み込み
    assert 'rel="preconnect"' in INDEX                    # 画像CDNへ先行接続
    assert 'rel="preconnect"' in render_article(_art(), [])
