"""静的サイト生成（データ駆動描画）：articles.json → index.html のカードグリッドに注入。

SEO/速度のため**ビルド時に静的HTMLを生成**（クライアントJS描画はしない）。
`<!-- CARDS:START -->`〜`<!-- CARDS:END -->` の間を冪等に差し替える。収集元を問わず
articles.json だけを消費するので、後で実収集に差し替えても UI 改修は不要。
画像が無い記事は **FR-18 プレースホルダ**で描画。翻訳済みは日本語見出し＋翻訳バッジ（FR-22）。
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlparse

NS = Path(__file__).resolve().parent.parent
INDEX = NS / "index.html"
ARTICLES = NS / "data" / "articles.json"

START = "<!-- CARDS:START -->"
END = "<!-- CARDS:END -->"

CATEGORY_COLOR = {
    "サイエンス": "#0ea5e9", "AI": "#3b5bff", "テクノロジー": "#6366f1", "コード": "#111827",
    "アルゴリズム": "#8b5cf6", "ロボット技術": "#ef4444", "フィジカルAI": "#f97316",
    "アート": "#ec4899", "デザイン": "#14b8a6", "動画": "#e11d48", "動物": "#84cc16",
    "自然": "#16a34a", "農業": "#ca8a04",
    "日本のAI": "#e60033", "アニメ": "#fb7185", "ガジェット": "#64748b", "漫画": "#f59e0b",
    "面白": "#a855f7",   # グループ・ラベル用
}
KIND_LABEL = {"article": "Article", "paper": "Paper", "code": "Code", "video": "Video"}


def _date(iso: str) -> str:
    return (iso or "")[:10].replace("-", "/")


def render_card(a: dict) -> str:
    cat = a["category"]
    color = CATEGORY_COLOR.get(cat, "#8b93ad")
    kind = a.get("kind", "article")
    klabel = KIND_LABEL.get(kind, "Article")
    title = a["title_ja"] if a.get("translated") and a.get("title_ja") else a["title_original"]
    title = html.escape(title)
    host = urlparse(a["source_url"]).netloc or a["source_url"]
    date = _date(a.get("collected_at", ""))
    agent = html.escape(a.get("agent", ""))
    av = cat[0]
    src_lang = (a.get("source_lang", "en") or "en").upper()
    badge = (f'<span class="badge-translate">🌐 {src_lang}→JA 翻訳</span>'
             if a.get("translated")
             else f'<span class="badge-translate">🌐 {src_lang}（未翻訳）</span>')

    tldr_html = ""
    if a.get("tldr"):
        lis = "".join(f"<li>{html.escape(b)}</li>" for b in a["tldr"])
        tldr_html = (
            '\n    <div class="tldr"><span class="ai-mark">AI 3行まとめ</span>'
            f'<ul>{lis}</ul></div>'
        )

    href = f'articles/{a["id"]}.html'
    if a.get("image"):
        thumb = (f'<a class="thumb" href="{href}">'
                 f'<span class="kind-tag kind-{kind}">{klabel}</span>'
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
        f'      {badge}\n'
        '    </div>\n'
        f'    <h3><a href="{href}">{title}</a></h3>{tldr_html}\n'
        f'    <div class="byline-agent"><span class="av">{av}</span>{agent} 監修</div>\n'
        '    <div class="foot">\n'
        f'      <span class="src">出典: {html.escape(host)}</span><span>· {date}</span>\n'
        '    </div>\n'
        '  </div>\n'
        '</article>'
    )


def render_cards(articles: list[dict]) -> str:
    if not articles:
        # FR-19 空状態
        return ('<div class="empty-state"><div class="ico">🗞️</div>'
                '<p>まだ記事がありません。今朝の収集をお待ちください。</p></div>')
    return "\n".join(render_card(a) for a in articles)


def inject(index_html: str, cards_html: str) -> str:
    if START not in index_html or END not in index_html:
        raise ValueError("CARDS markers not found in index.html")
    pre, rest = index_html.split(START, 1)
    _, post = rest.split(END, 1)
    return f"{pre}{START}\n{cards_html}\n        {END}{post}"


ORDER = ["サイエンス", "AI", "テクノロジー", "コード", "アルゴリズム", "ロボット技術",
         "フィジカルAI", "アート", "デザイン", "動画", "動物", "自然", "農業"]
ARTICLES_DIR = NS / "articles"


# ナビ（暗背景）でのグロー色。コードは黒だと埋もれるのでシルバー（ターミナル質感）に上書き。
NAV_GLOW = {"コード": "#cbd5e1"}

# トップレベル構成。似たカテゴリはプルダウンで統合。
#  サイエンス＝[サイエンス, テクノロジー] / AI＝[AI, フィジカルAI, ロボット技術, 日本のAI]
#  コード＝[コード, アルゴリズム] / 面白＝[アニメ, ガジェット, 漫画]
NAV_TOP = [
    ("サイエンス", ["サイエンス", "テクノロジー"]),
    ("AI", ["AI", "フィジカルAI", "ロボット技術", "日本のAI"]),
    ("コード", ["コード", "アルゴリズム"]),
    ("アート", None), ("デザイン", None), ("動画", None),
    ("動物", None), ("自然", None), ("農業", None),
    ("面白", ["アニメ", "ガジェット", "漫画"]),
]


def _glow(cat: str) -> str:
    return NAV_GLOW.get(cat, CATEGORY_COLOR[cat])


def _nav(active: str, prefix: str) -> str:
    """カテゴリナビ（ダークグロウ・案C）。似たカテゴリはプルダウン。prefix は相対パス。"""
    out = [f'<a href="{prefix}index.html" style="--cc:#5b78ff">すべて</a>']
    for label, children in NAV_TOP:
        if children is None:
            on = ' class="active"' if label == active else ""
            out.append(f'<a href="#"{on} style="--cc:{_glow(label)}">'
                       f'<span class="cdot"></span>{label}</a>')
        else:
            trig_on = " active" if active in children else ""
            parts = []
            for c in children:
                c_on = ' class="active"' if c == active else ""
                parts.append(f'<a href="#"{c_on} style="--cc:{_glow(c)}">'
                             f'<span class="cdot"></span>{c}</a>')
            items = "".join(parts)
            out.append(
                f'<div class="catgroup"><a href="#" class="cat-trigger{trig_on}" '
                f'style="--cc:{_glow(label)}"><span class="cdot"></span>{label}'
                f'<span class="caret">▾</span></a><div class="dropdown">{items}</div></div>'
            )
    return "\n      ".join(out)


def _kind_body(a: dict, body_ja: str) -> str:
    """種別ごとの本文体裁（FR-24 動画 / FR-25 コード / FR-28 論文）。"""
    kind = a.get("kind", "article")
    src = html.escape(a["source_url"])
    if kind == "code":
        return (f'<p>{body_ja}</p>\n<div class="codeblock"><div class="cb-head">'
                f'<span>snippet</span><span class="lang">code</span></div>'
                f'<pre>// 原文リポジトリ参照: {src}\n// 全文転載はせず要点のみ紹介</pre></div>')
    if kind == "video":
        poster = html.escape(a.get("image") or "")
        img = f'<img loading="lazy" decoding="async" src="{poster}" alt="">' if poster else ""
        return (f'<figure class="video-embed"><div class="frame">{img}'
                f'<span class="play"></span></div>'
                f'<figcaption>原典動画（埋め込み）: <a href="{src}" rel="nofollow noopener">{src}</a>'
                f'</figcaption></figure><p>{body_ja}</p>')
    if kind == "paper":
        return (f'<div class="paper-card"><div class="pc-tag">PAPER</div>'
                f'<p class="abstract">{body_ja}</p>'
                f'<a href="{src}" rel="nofollow noopener">原論文を読む →</a></div>')
    return f"<p>{body_ja}</p>"


def render_article(a: dict, others: list[dict]) -> str:
    cat = a["category"]
    color = CATEGORY_COLOR.get(cat, "#8b93ad")
    kind = a.get("kind", "article")
    klabel = KIND_LABEL.get(kind, "Article")
    title = html.escape(a["title_ja"] if a.get("translated") and a.get("title_ja") else a["title_original"])
    title_orig = html.escape(a["title_original"])
    body_ja = html.escape(a["body_ja"] or a["body_original"])
    body_orig = html.escape(a["body_original"])
    src = html.escape(a["source_url"])
    date = _date(a.get("collected_at", ""))
    agent = html.escape(a.get("agent", ""))
    src_lang = (a.get("source_lang", "en") or "en").upper()

    tldr = ""
    if a.get("tldr"):
        lis = "".join(f"<li>{html.escape(b)}</li>" for b in a["tldr"])
        tldr = f'<div class="tldr tldr-lg"><span class="ai-mark">AI 3行まとめ（30秒で分かる）</span><ul>{lis}</ul></div>'

    related = "".join(
        f'<a class="r" href="{o["id"]}.html"><div class="sim">関連</div>'
        f'<div class="info"><b>{html.escape(o["title_ja"] or o["title_original"])}</b>'
        f'<div class="m">{html.escape(o["category"])}</div></div></a>'
        for o in others[:3]
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — NewsMatome</title>
<meta name="description" content="{title}（{src_lang}→JA 翻訳・出典付き）">
<link rel="stylesheet" href="../css/style.css">
</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="../index.html"><span class="dot"></span><span>NewsMatome<small>WORLD TECH, IN JAPANESE</small></span></a>
    <span class="update-badge">⟳ 毎朝7時更新</span>
    <span class="topbar-spacer"></span>
    <label class="search semantic"><span class="lead">✦</span><input type="text" placeholder="意味で探す"></label>
    <div class="lang-select"><a class="on" href="#">日本語</a><a href="#" title="English edition（準備中・/en/）">EN</a></div>
    <a class="btn-cta" href="../about.html#contact">お仕事のご依頼</a>
  </div>
  <nav class="catnav"><div class="catnav-inner">
      {_nav(cat, "../")}
  </div></nav>
</header>

<div class="wrap">
  <div class="breadcrumb"><a href="../index.html">ホーム</a><span class="sep">›</span><a href="#">{html.escape(cat)}</a><span class="sep">›</span><span>{title}</span></div>
  <article class="article">
    <div class="article-head">
      <div class="toprow">
        <span class="chip"><span class="cdot" style="background:{color}"></span>{html.escape(cat)}</span>
        <span class="kind-tag kind-{kind}">{klabel}</span>
        <span class="badge-translate">🌐 {src_lang}→JA 翻訳</span>
      </div>
      <h1>{title}</h1>
      <div class="article-byline">
        <span class="who"><span class="av-lg">{cat[0]}</span><span><b>{agent}</b>収集・日本語化・監修</span></span>
        <span>公開 {date} 07:00</span><span>· 更新 {date}</span>
      </div>
    </div>
    {tldr}
    <div class="depth">
      <span class="lbl"><span class="ai-mark">読む深さ</span></span>
      <div class="seg" id="depthSeg"><button data-d="easy">やさしく</button><button data-d="normal" class="on">標準</button><button data-d="expert">専門</button></div>
      <span class="lbl" id="depthNote">— 標準の文章で表示中</span>
    </div>
    <div class="source-bar"><span class="lang">{src_lang} → JA</span>
      <span>海外の一次情報を翻訳・要約。原文：<a href="{src}" rel="nofollow noopener">{title_orig}</a>。引用は範囲に留め、原文を併記します。</span></div>
    <div class="parallel-toggle"><span class="switch-ui" id="parallelSwitch" role="switch" aria-checked="false"></span><span class="ai-mark">対訳ビュー</span><span class="muted">原文を併記</span></div>
    <div class="parallel" id="parallelView" style="display:none;">
      <div class="col src"><span class="tag">ORIGINAL · {src_lang}</span>{body_orig}</div>
      <div class="col"><span class="tag">日本語訳 · JA</span>{body_ja}</div>
    </div>
    <div class="article-body">
      {_kind_body(a, body_ja)}
    </div>
    <div class="source-bar" style="margin-top:30px;"><span class="lang">出典</span><span>原文：<a href="{src}" rel="nofollow noopener">{src}</a>。本記事は収集→日本語化パイプラインの自動生成です。</span></div>
    <div class="share"><a class="x" href="#">X でシェア</a><a class="fb" href="#">Facebook</a><a class="line" href="#">LINE</a><a class="hatena" href="#">はてブ</a></div>
    <div class="ask"><div class="ahead"><span class="ai-mark"></span><b>この記事に質問する</b><span class="muted" style="font-size:11px;">本文に基づき回答・出典明示（推測しません）</span></div>
      <div class="abody"><div class="qrow"><input id="askInput" type="text" placeholder="例：要点は？"><button class="send" id="askSend">質問</button></div>
        <div class="ans" id="askAns" style="display:none;">本文・出典に基づいて回答します<span class="cite">¶ 本文</span>。本文に無い内容は「分かりません」と答え、捏造しません（NFR-8）。</div></div></div>
    <div class="ai-related"><h3><span class="ai-mark"></span>意味が近い記事</h3><div class="sub">内容の意味で関連付け（言語横断）。</div>{related}</div>
    <section class="comments"><h2>コメント</h2><div class="cnt">0件のコメント</div>
      <div class="empty-state"><div class="ico">💬</div><p>まだコメントはありません。最初のコメントを投稿しましょう。</p></div>
      <form class="comment-form" onsubmit="return false;"><textarea placeholder="コメントを投稿（雛形のため送信は無効）"></textarea><button type="submit">コメントする</button></form></section>
  </article>
</div>
<footer class="footer"><div class="footer-note">© 2026 NewsMatome. 海外記事は引用の範囲で紹介し、必ず原文出典へリンク。翻訳・要約は各分野の専門エージェントが担当し原文を併記。<div class="legal">本ページは収集→日本語化パイプラインの自動生成（サンプル）です。</div></div></footer>
<script>
(function(){{var seg=document.getElementById('depthSeg'),note=document.getElementById('depthNote'),body=document.querySelector('.article-body');
var msg={{easy:'— やさしい言葉で表示中',normal:'— 標準の文章で表示中',expert:'— 専門レベルで表示中'}};
seg.addEventListener('click',function(e){{var b=e.target.closest('button');if(!b)return;[].forEach.call(seg.children,function(x){{x.classList.remove('on');}});b.classList.add('on');note.textContent=msg[b.dataset.d];}});}})();
(function(){{var sw=document.getElementById('parallelSwitch'),pv=document.getElementById('parallelView');sw.addEventListener('click',function(){{var on=sw.classList.toggle('on');sw.setAttribute('aria-checked',on);pv.style.display=on?'grid':'none';}});}})();
(function(){{var ans=document.getElementById('askAns');document.getElementById('askSend').addEventListener('click',function(){{ans.style.display='block';}});}})();
document.querySelectorAll('.cat-trigger').forEach(function(t){{t.addEventListener('click',function(e){{e.preventDefault();var g=t.closest('.catgroup'),was=g.classList.contains('open');document.querySelectorAll('.catgroup.open').forEach(function(x){{x.classList.remove('open');}});if(!was)g.classList.add('open');}});}});
document.addEventListener('click',function(e){{if(!e.target.closest('.catgroup'))document.querySelectorAll('.catgroup.open').forEach(function(x){{x.classList.remove('open');}});}});
</script>
</body>
</html>"""


def build_articles(articles: list[dict], out_dir: Path = ARTICLES_DIR) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, a in enumerate(articles):
        others = articles[:i] + articles[i + 1:]
        (out_dir / f'{a["id"]}.html').write_text(render_article(a, others), encoding="utf-8")
    return len(articles)


def build(articles_path: Path = ARTICLES, index_path: Path = INDEX) -> dict:
    data = json.loads(articles_path.read_text(encoding="utf-8"))
    articles = data.get("articles", [])
    cards = render_cards(articles)
    out = inject(index_path.read_text(encoding="utf-8"), cards)
    index_path.write_text(out, encoding="utf-8")
    n_pages = build_articles(articles)
    return {"rendered": len(articles), "pages": n_pages, "index": str(index_path)}


if __name__ == "__main__":
    print("[render]", build())
