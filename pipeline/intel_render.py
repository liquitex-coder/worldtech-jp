"""インテリジェンス可視化ページ生成：data/intel.json → intel.html（公開・別ページ）。

既存ニュース面（index.html）には記事を加えず、独立した静的ページを生成する。各 entity の観測を
**確度ラベル＋出典リンク＋次タスク**で表示する。`data/graph.json` があれば関係グラフ節も描く。
またニュース面のトップバーに intel ページへの導線を冪等注入する。

非捏造（INV-R2）：intel.json に載っているのは publishable かつ出典つきの項目のみ。本ページは
それをそのまま描くだけで、新たな主張は作らない。確度はコード算定値をラベル表示する。
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlparse

NS = Path(__file__).resolve().parent.parent
DATA = NS / "data"
INTEL_HTML = NS / "intel.html"

_CONF_CLASS = {0: "c0", 1: "c1", 2: "c2", 3: "c3", 4: "c4"}
_RELATION_JA = {"shareholder": "大株主", "supplier": "取引先", "customer": "納品先",
                "partner": "提携", "subsidiary": "子会社"}

_STYLE = """
.intel-wrap{max-width:920px;margin:0 auto;padding:28px 18px 64px}
.intel-wrap h1{font-size:26px;margin:8px 0 6px}
.intel-lead{color:#475569;line-height:1.7;margin:0 0 6px}
.intel-meta{color:#94a3b8;font-size:13px;margin:0 0 22px}
.intel-card{border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px;margin:0 0 16px;background:#fff}
.intel-top{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}
.intel-card h2{font-size:18px;margin:4px 0 10px;line-height:1.5}
.conf{font-size:12px;font-weight:700;color:#fff;border-radius:999px;padding:2px 10px}
.conf.c0{background:#94a3b8}.conf.c1{background:#64748b}.conf.c2{background:#d97706}
.conf.c3{background:#16a34a}.conf.c4{background:#2563eb}
.derived{font-size:12px;font-weight:700;color:#7c3aed;border:1px solid #ddd6fe;border-radius:999px;padding:1px 8px}
.ent{color:#0f172a;font-weight:700}
.intel-bullets{margin:0;padding-left:18px;line-height:1.8}
.intel-bullets .srcs{margin-left:6px;font-size:12px}
.intel-bullets .srcs a{color:#2563eb;text-decoration:none}
.intel-tasks{margin-top:10px;font-size:13px;color:#475569}
.intel-tasks .chip{display:inline-block;background:#f1f5f9;border-radius:999px;padding:2px 9px;margin:0 4px 4px 0}
.intel-byline{margin-top:8px;color:#94a3b8;font-size:12px}
.intel-graph{margin-top:26px}
.intel-graph h2{font-size:18px;margin:0 0 8px}
.intel-edge{padding:6px 0;border-bottom:1px dashed #e5e7eb}
.intel-edge .rel{color:#475569}
.intel-empty{color:#64748b;background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:28px;text-align:center}
.intel-foot{margin-top:28px;color:#94a3b8;font-size:12px;line-height:1.7}
"""


def _host(url: str) -> str:
    return urlparse(url).netloc or url


def _sources_html(sources: list[str]) -> str:
    links = [f'<a href="{html.escape(s)}" rel="nofollow noopener" target="_blank">'
             f'{html.escape(_host(s))}</a>' for s in sources]
    return f'<span class="srcs">出典: {" / ".join(links)}</span>' if links else ""


def _card_html(item: dict) -> str:
    conf = int(item.get("confidence", 0))
    cls = _CONF_CLASS.get(conf, "c0")
    label = html.escape(item.get("confidence_label", ""))
    derived = '<span class="derived">推論</span>' if item.get("derived") else ""
    ent = html.escape(item.get("entity", ""))
    headline = html.escape(item.get("headline", ""))
    bullets = "".join(
        f'<li>{html.escape(b.get("text", ""))} {_sources_html(b.get("sources", []))}</li>'
        for b in item.get("bullets", []))
    tasks = item.get("next_tasks", [])
    tasks_html = ""
    if tasks:
        chips = "".join(f'<span class="chip">{html.escape(t.get("channel", ""))}</span>'
                        for t in tasks)
        tasks_html = f'<div class="intel-tasks">次に掘る: {chips}</div>'
    agent = html.escape(item.get("agent", ""))
    return (
        '<article class="intel-card">\n'
        f'  <div class="intel-top"><span class="conf {cls}">確度: {label}</span>'
        f'{derived}<span class="ent">{ent}</span></div>\n'
        f'  <h2>{headline}</h2>\n'
        f'  <ul class="intel-bullets">{bullets}</ul>\n'
        f'  {tasks_html}\n'
        f'  <div class="intel-byline">{agent}</div>\n'
        '</article>'
    )


def _graph_html(graph: dict | None) -> str:
    edges = (graph or {}).get("edges", [])
    if not edges:
        return ""
    rows = []
    for e in edges:
        rel = _RELATION_JA.get(e.get("relation", ""), html.escape(e.get("relation", "")))
        rows.append(
            f'<div class="intel-edge"><span class="ent">{html.escape(e.get("src", ""))}</span> '
            f'<span class="rel">—{rel}→</span> '
            f'<span class="ent">{html.escape(e.get("dst", ""))}</span> '
            f'<span class="conf {_CONF_CLASS.get(int(e.get("confidence", 0)), "c0")}">'
            f'{html.escape(e.get("confidence_label", ""))}</span> '
            f'{_sources_html(e.get("sources", []))}</div>')
    return ('<section class="intel-graph"><h2>関係グラフ（周辺の積み上げ）</h2>'
            + "\n".join(rows) + '</section>')


def build_page(payload: dict, graph: dict | None = None) -> str:
    entities = payload.get("entities", [])
    generated = html.escape(payload.get("generated_at", "") or "-")
    engine = html.escape(payload.get("engine", "") or "deterministic")
    if entities:
        body = "\n".join(_card_html(it) for it in entities)
    else:
        body = ('<div class="intel-empty">公開できるインテリジェンス項目はまだありません。'
                'ソース登録後の収集をお待ちください。</div>')
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>インテリジェンス | NewsMatome</title>
<meta name="description" content="公開情報から出典付き・確度ラベル付きで積み上げた観測。裏付けの無い主張は載せません。">
<link rel="stylesheet" href="css/style.css">
<style>{_STYLE}</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner">
  <a class="brand" href="index.html"><span class="dot"></span><span>NewsMatome<small>INTELLIGENCE</small></span></a>
  <span class="topbar-spacer"></span>
  <a class="btn-cta" href="index.html">ニュースへ</a>
</div></header>
<main class="intel-wrap">
  <h1>インテリジェンス</h1>
  <p class="intel-lead">公開情報（法定開示・取引・電力などの周辺信号）から、<b>出典付き・確度ラベル付き</b>で積み上げた観測です。確度はコードが算定し、裏付けの無い主張は載せません。</p>
  <p class="intel-meta">更新: {generated} ／ 件数: {len(entities)} ／ エンジン: {engine}</p>
{body}
{_graph_html(graph)}
  <footer class="intel-foot">確度ラベルは 未確認 / 低 / 中 / 高 / 確定。各項目は一次情報の出典にひも付きます（INV-R2）。「株式」は開示済みの持分異動のみを対象とします。</footer>
</main>
</body>
</html>
"""


# ニュース面トップバーから intel.html への導線。ビルド時に index.html へ冪等注入する。
NAV_INTEL = (
    '<a class="nav-intel" href="intel.html" title="公開情報から積み上げた観測（出典・確度つき）" '
    'style="display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:700;'
    'color:#0ea5e9;text-decoration:none;margin-right:10px">📊 インテリジェンス</a>'
)


def inject_intel_nav(text: str) -> str:
    """トップバーの言語切替の直前に intel 導線を冪等挿入（既にあれば／アンカー無しは無変更）。"""
    if "nav-intel" in text:
        return text
    anchor = '<div class="lang-select">'
    if anchor not in text:
        return text
    return text.replace(anchor, f'{NAV_INTEL}\n    {anchor}', 1)


def _ensure_nav_link(index_path: Path) -> bool:
    """index.html に intel 導線を冪等注入（変更したら True）。"""
    if not index_path.exists():
        return False
    text = index_path.read_text(encoding="utf-8")
    injected = inject_intel_nav(text)
    if injected != text:
        index_path.write_text(injected, encoding="utf-8")
        return True
    return False


def render_intel(data_dir: Path = DATA, out: Path = INTEL_HTML) -> dict:
    """data/intel.json（＋あれば graph.json）から intel.html を生成し、ニュース面に導線を注入する。"""
    intel_path = data_dir / "intel.json"
    if not intel_path.exists():
        payload = {"generated_at": "", "count": 0, "engine": "", "entities": []}
    else:
        payload = json.loads(intel_path.read_text(encoding="utf-8"))
    graph_path = data_dir / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8")) if graph_path.exists() else None
    out.write_text(build_page(payload, graph), encoding="utf-8")
    nav = _ensure_nav_link(out.parent / "index.html")   # 同階層の index.html に導線（冪等・テスト安全）
    return {"entities": len(payload.get("entities", [])), "path": str(out), "nav_injected": nav}
