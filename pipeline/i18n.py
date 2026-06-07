"""多言語SEO（NFR-6）：hreflang 相互参照 ＋ `/en/` 英語版エディション生成。

設計（非捏造・INV-R2）：英語版は**翻訳を発明しない**。サンプル収集の一次情報は原文＝英語なので、
EN edition は **保持している原文（title_original / body_original）をそのまま掲出**する。原文を持たない
言語の自動生成はしない（持っていない英語を捏造しない）。日↔英は **hreflang で相互リンク**し、
各ページの `canonical` は自分の言語版を指す（重複コンテンツ回避・SEO）。

- `inject_hreflang(html, ja_url, en_url)`：既存 JA ページの `<link rel="canonical">` 直後に
  `hreflang=ja/en/x-default` を冪等挿入（二重挿入しない）。
- `build_en_edition(...)`：`en/index.html` と `en/articles/{id}.html` を生成（lang="en"・原文掲出）。
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlparse

from pipeline.render import (
    ARTICLES,
    CATEGORY_COLOR,
    INDEX,
    KIND_LABEL,
    NS,
    _date,
)

SITE = "https://liquitex-coder.github.io/worldtech-jp"
EN_DIR = NS / "en"
EN_ARTICLES_DIR = EN_DIR / "articles"

_MARK = "<!-- hreflang -->"


def hreflang_block(ja_url: str, en_url: str) -> str:
    """日本語版（x-default）と英語版を相互参照する alternate リンク群。"""
    return (
        f'{_MARK}\n'
        f'<link rel="alternate" hreflang="ja" href="{ja_url}">\n'
        f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{ja_url}">'
    )


def inject_hreflang(page_html: str, ja_url: str, en_url: str) -> str:
    """canonical 直後に hreflang を冪等挿入（既にあれば何もしない）。"""
    if _MARK in page_html:
        return page_html                                   # 二重挿入しない（冪等）
    needle = "<link rel=\"canonical\""
    i = page_html.find(needle)
    if i == -1:
        return page_html
    eol = page_html.find("\n", i)
    if eol == -1:
        eol = page_html.find(">", i) + 1
    block = hreflang_block(ja_url, en_url)
    return page_html[: eol + 1] + block + "\n" + page_html[eol + 1 :]


# ------------------------------------------------------------ EN edition 描画
def _en_card(a: dict) -> str:
    cat = a["category"]
    color = CATEGORY_COLOR.get(cat, "#8b93ad")
    kind = a.get("kind", "article")
    klabel = KIND_LABEL.get(kind, "Article")
    title = html.escape(a["title_original"])               # 原文＝英語（捏造しない）
    host = urlparse(a["source_url"]).netloc or a["source_url"]
    date = _date(a.get("collected_at", ""))
    href = f'articles/{a["id"]}.html'
    if a.get("image"):
        thumb = (f'<a class="thumb" href="{href}"><span class="kind-tag kind-{kind}">{klabel}</span>'
                 f'<img loading="lazy" decoding="async" src="{html.escape(a["image"])}" alt=""></a>')
    else:
        thumb = (f'<a class="thumb is-empty" href="{href}">'
                 f'<span class="kind-tag kind-{kind}">{klabel}</span></a>')
    return (
        '<article class="card">\n'
        f'  {thumb}\n'
        '  <div class="body">\n'
        '    <div class="toprow">\n'
        f'      <span class="chip"><span class="cdot" style="background:{color}"></span>{html.escape(cat)}</span>\n'
        '      <span class="badge-translate">EN · original</span>\n'
        '    </div>\n'
        f'    <h3><a href="{href}">{title}</a></h3>\n'
        f'    <div class="foot"><span class="src">source: {html.escape(host)}</span><span>· {date}</span></div>\n'
        '  </div>\n'
        '</article>'
    )


def render_en_index(articles: list[dict]) -> str:
    cards = "\n".join(_en_card(a) for a in articles) or (
        '<div class="empty-state"><div class="ico">🗞️</div><p>No articles yet.</p></div>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NewsMatome (EN) — World tech, summarized</title>
<meta name="description" content="English edition. World science / AI / tech sources, with links to the Japanese translation.">
<link rel="canonical" href="{SITE}/en/">
{hreflang_block(SITE + "/", SITE + "/en/")}
<meta property="og:type" content="website">
<meta property="og:site_name" content="NewsMatome">
<meta property="og:title" content="NewsMatome (EN)">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="ja_JP">
<link rel="preconnect" href="https://picsum.photos" crossorigin>
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="topbar"><div class="topbar-inner">
  <a class="brand" href="../index.html"><span class="dot"></span><span>NewsMatome<small>WORLD TECH</small></span></a>
  <span class="topbar-spacer"></span>
  <div class="lang-select"><a href="../index.html" title="日本語版">日本語</a><a class="on" href="#">EN</a></div>
</div></header>
<div class="wrap"><main class="feed">
  <p class="source-bar"><span class="lang">EN</span><span>Original-language edition. Each article links to its Japanese translation (hreflang).</span></p>
  <div class="cardgrid">
{cards}
  </div>
</main></div>
<footer class="footer"><div class="footer-note">© 2026 NewsMatome. Excerpts only, always linking to the original source.</div></footer>
</body>
</html>"""


def render_en_article(a: dict) -> str:
    cat = a["category"]
    color = CATEGORY_COLOR.get(cat, "#8b93ad")
    kind = a.get("kind", "article")
    klabel = KIND_LABEL.get(kind, "Article")
    title = html.escape(a["title_original"])               # 英語原文をそのまま（非捏造）
    body = html.escape(a["body_original"])
    src = html.escape(a["source_url"])
    date = _date(a.get("collected_at", ""))
    agent = html.escape(a.get("agent", ""))
    pub_iso = html.escape(a.get("collected_at", ""))
    en_url = f"{SITE}/en/articles/{a['id']}.html"
    ja_url = f"{SITE}/articles/{a['id']}.html"
    img = html.escape(a.get("image") or "")
    og_img = f'<meta property="og:image" content="{img}">' if img else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — NewsMatome (EN)</title>
<meta name="description" content="{title} — original-language edition. Japanese translation available.">
<link rel="canonical" href="{en_url}">
{hreflang_block(ja_url, en_url)}
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="ja_JP">
{og_img}
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"NewsArticle","headline":"{title}",
 "inLanguage":"en","datePublished":"{pub_iso}","dateModified":"{pub_iso}",
 "author":{{"@type":"Organization","name":"{agent}"}},
 "publisher":{{"@type":"Organization","name":"NewsMatome"}},
 "isBasedOn":"{src}","url":"{en_url}"}}
</script>
<link rel="stylesheet" href="../../css/style.css">
</head>
<body>
<header class="topbar"><div class="topbar-inner">
  <a class="brand" href="../../index.html"><span class="dot"></span><span>NewsMatome<small>WORLD TECH</small></span></a>
  <span class="topbar-spacer"></span>
  <div class="lang-select"><a href="../../articles/{a['id']}.html" title="日本語訳">日本語</a><a class="on" href="#">EN</a></div>
</div></header>
<div class="wrap"><article class="article">
  <div class="article-head">
    <div class="toprow"><span class="chip"><span class="cdot" style="background:{color}"></span>{html.escape(cat)}</span>
      <span class="kind-tag kind-{kind}">{klabel}</span><span class="badge-translate">EN · original</span></div>
    <h1>{title}</h1>
    <div class="article-byline"><span class="who"><span class="av-lg">{cat[0]}</span><span><b>{agent}</b></span></span><span>{date}</span></div>
  </div>
  <div class="source-bar"><span class="lang">EN</span><span>Original-language text (excerpt). 日本語訳は <a href="../../articles/{a['id']}.html">こちら</a>。 Source: <a href="{src}" rel="nofollow noopener">{src}</a></span></div>
  <div class="article-body"><p>{body}</p></div>
</article></div>
<footer class="footer"><div class="footer-note">© 2026 NewsMatome. Excerpt only — see the original source.</div></footer>
</body>
</html>"""


def build_en_edition(articles_path: Path = ARTICLES, index_path: Path = INDEX) -> dict:
    """`/en/` 英語版（hreflang 相互リンク付き）と、JA 側への hreflang 注入を行う。"""
    data = json.loads(articles_path.read_text(encoding="utf-8"))
    articles = data.get("articles", [])

    # EN edition を書き出す
    EN_ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    (EN_DIR / "index.html").write_text(render_en_index(articles), encoding="utf-8")
    for a in articles:
        (EN_ARTICLES_DIR / f'{a["id"]}.html').write_text(render_en_article(a), encoding="utf-8")

    # JA index に hreflang を冪等注入
    idx = index_path.read_text(encoding="utf-8")
    index_path.write_text(inject_hreflang(idx, SITE + "/", SITE + "/en/"), encoding="utf-8")

    # JA 個別記事に hreflang を冪等注入
    ja_dir = NS / "articles"
    injected = 0
    for a in articles:
        p = ja_dir / f'{a["id"]}.html'
        if p.exists():
            ja_url = f"{SITE}/articles/{a['id']}.html"
            en_url = f"{SITE}/en/articles/{a['id']}.html"
            p.write_text(inject_hreflang(p.read_text(encoding="utf-8"), ja_url, en_url), encoding="utf-8")
            injected += 1

    return {"en_pages": len(articles) + 1, "ja_hreflang_injected": injected + 1}


if __name__ == "__main__":
    print("[i18n]", build_en_edition())
