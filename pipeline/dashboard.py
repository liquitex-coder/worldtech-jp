"""管理者ダッシュボード生成（運用可視化）。

パイプラインが出力する JSON（articles / compliance / quality / governance / feeds）を
ビルド時に集計し、静的な `admin.html` を生成する。バックエンド不要・決定論。

表示内容：
- 実行メタ（収集時刻・件数・翻訳エンジン）
- **どこのニュースを拾ったか**：出典ホスト別の件数、収集ソース型（記事/論文/コード/動画）、カテゴリ別
- 翻訳状況（翻訳済み/未翻訳・捏造していないことの可視化）
- 権利運用(NFR-4)/翻訳品質(NFR-5)/生成物検証(NFR-7) のサマリ
- 収集元フィード（feeds.json）の登録状況
- **アクセス解析（読者の所在）**：静的サイトは外部プロバイダが必要 → 接続状況と手順を表示

注意：GitHub Pages は静的配信なので admin.html も**URL を知れば誰でも閲覧可能**（ログイン無し）。
ここには公開ソースの運用情報のみを載せ、訪問者の個人データは外部プロバイダ側（ログイン保護）に置く。
"""
from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

NS = Path(__file__).resolve().parent.parent
DATA = NS / "data"
OUT = NS / "admin.html"

KIND_JA = {"article": "記事", "paper": "論文", "code": "コード", "video": "動画"}


def _load(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _stat(label: str, value, sub: str = "") -> str:
    sub_html = f'<div class="ds-sub">{html.escape(sub)}</div>' if sub else ""
    return (f'<div class="ds-card"><div class="ds-val">{html.escape(str(value))}</div>'
            f'<div class="ds-lbl">{html.escape(label)}</div>{sub_html}</div>')


def _rows(pairs: list[tuple[str, object]]) -> str:
    return "\n".join(
        f'<tr><td>{html.escape(str(k))}</td><td class="num">{html.escape(str(v))}</td></tr>'
        for k, v in pairs
    ) or '<tr><td colspan="2" class="muted">—</td></tr>'


def build_dashboard(data_dir: Path = DATA, out: Path = OUT) -> dict:
    arts_doc = _load(data_dir / "articles.json") or {}
    articles = arts_doc.get("articles", [])
    comp = _load(data_dir / "compliance-report.json") or {}
    qual = _load(data_dir / "quality-report.json") or {}
    gov = _load(data_dir / "governance-ledger.json") or {}
    feeds = _load(NS / "pipeline" / "feeds.json") or []

    generated_at = arts_doc.get("generated_at") or "—"
    engine = arts_doc.get("translation_engine") or "（未接続：原文保持）"

    hosts = Counter(urlparse(a.get("source_url", "")).netloc or "—" for a in articles)
    kinds = Counter(a.get("kind", "article") for a in articles)
    cats = Counter(a.get("category", "—") for a in articles)
    translated = sum(1 for a in articles if a.get("translated"))
    untranslated = [a for a in articles if not a.get("translated")]

    # 各セクション
    host_rows = _rows(sorted(hosts.items(), key=lambda x: (-x[1], x[0])))
    kind_rows = _rows([(KIND_JA.get(k, k), v) for k, v in
                       sorted(kinds.items(), key=lambda x: -x[1])])
    cat_rows = _rows(sorted(cats.items(), key=lambda x: (-x[1], x[0])))

    blocked = comp.get("blocked", [])
    blocked_html = ("".join(
        f'<li><code>{html.escape(b.get("id",""))}</code> — {html.escape(b.get("reason",""))}</li>'
        for b in blocked) or '<li class="muted">なし（全件クリア）</li>')

    violations = gov.get("violations", [])
    viol_html = ("".join(
        f'<li><code>{html.escape(v.get("id",""))}</code> {html.escape(v.get("claim",""))} — {html.escape(v.get("reason",""))}</li>'
        for v in violations) or '<li class="muted">なし（採用claimは全て出典紐付け）</li>')

    untrans_html = ("".join(
        f'<li><code>{html.escape(a.get("id",""))}</code> {html.escape(a.get("title_original",""))}'
        f' <span class="muted">({html.escape((a.get("source_lang") or "").upper())}・出典保持)</span></li>'
        for a in untranslated) or '<li class="muted">なし（全件 翻訳済み）</li>')

    if feeds:
        feed_html = "".join(
            f'<li><code>{html.escape(f.get("category",""))}/{html.escape(f.get("kind",""))}</code> '
            f'{html.escape(f.get("url",""))}</li>' for f in feeds if isinstance(f, dict))
        feed_note = f"{len(feeds)} 件のフィードを登録（実RSS収集 有効）"
    else:
        feed_html = ('<li class="muted">未登録 → サンプル収集で稼働中。'
                     '<code>pipeline/feeds.json</code> に登録すると実RSS収集に切替（feeds.example.json 参照）。</li>')
        feed_note = "サンプル収集"

    quality_ratio = qual.get("quality_ratio")
    gov_sound = gov.get("sound")

    return _write(out, {
        "generated_at": generated_at, "engine": engine,
        "count": len(articles), "translated": translated,
        "n_hosts": len(hosts), "feed_note": feed_note,
        "comp_cleared": len(comp.get("cleared", [])), "comp_total": comp.get("total", len(articles)),
        "comp_blocked": len(blocked), "quality_ratio": quality_ratio,
        "gov_accepted": gov.get("accepted", 0), "gov_omitted": gov.get("omitted", 0),
        "gov_sound": gov_sound,
        "host_rows": host_rows, "kind_rows": kind_rows, "cat_rows": cat_rows,
        "blocked_html": blocked_html, "viol_html": viol_html,
        "untrans_html": untrans_html, "feed_html": feed_html,
    })


def _write(out: Path, c: dict) -> dict:
    ratio = "—" if c["quality_ratio"] is None else f'{c["quality_ratio"]*100:.0f}%'
    sound = "✅ 健全" if c["gov_sound"] else "❌ 違反あり"
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>管理ダッシュボード — NewsMatome</title>
<link rel="stylesheet" href="css/style.css">
<style>
.dash{{max-width:1080px;margin:0 auto;padding:24px 18px}}
.ds-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}}
.ds-card{{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px}}
.ds-val{{font-size:26px;font-weight:800;color:#111827}}
.ds-lbl{{font-size:12px;color:#6b7280;margin-top:4px}}
.ds-sub{{font-size:11px;color:#9ca3af;margin-top:2px}}
.dash h2{{margin:26px 0 8px;font-size:16px}}
.dash table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden}}
.dash td{{padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:13px}}
.dash td.num{{text-align:right;font-variant-numeric:tabular-nums;color:#334155}}
.dash ul{{margin:8px 0;padding-left:18px;font-size:13px;line-height:1.7}}
.dash code{{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px}}
.muted{{color:#9ca3af}}
.note{{background:#fff7ed;border:1px solid #fed7aa;border-radius:10px;padding:14px;font-size:13px;line-height:1.7}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:680px){{.cols{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="topbar"><div class="topbar-inner">
  <a class="brand" href="index.html"><span class="dot"></span><span>NewsMatome<small>ADMIN</small></span></a>
  <span class="topbar-spacer"></span><a class="btn-cta" href="index.html">サイトを見る</a>
</div></header>

<div class="dash">
  <h1 style="font-size:20px;">管理ダッシュボード</h1>
  <p class="muted" style="font-size:13px;">最終実行 <b>{html.escape(c['generated_at'])}</b> ／ 翻訳エンジン: {html.escape(c['engine'])} ／ 収集元: {html.escape(c['feed_note'])}</p>

  <div class="ds-grid">
    {_stat("収集記事", c['count'])}
    {_stat("翻訳済み", f"{c['translated']}/{c['count']}")}
    {_stat("出典ホスト数", c['n_hosts'])}
    {_stat("権利クリア (NFR-4)", f"{c['comp_cleared']}/{c['comp_total']}", f"ブロック {c['comp_blocked']}")}
    {_stat("翻訳品質 (NFR-5)", ratio)}
    {_stat("生成物検証 (NFR-7)", sound, f"採用 {c['gov_accepted']} / 省略 {c['gov_omitted']}")}
  </div>

  <div class="cols">
    <div>
      <h2>どこのニュースを拾ったか（出典ホスト）</h2>
      <table>{c['host_rows']}</table>
    </div>
    <div>
      <h2>収集ソース型</h2>
      <table>{c['kind_rows']}</table>
      <h2>カテゴリ別</h2>
      <table>{c['cat_rows']}</table>
    </div>
  </div>

  <h2>未翻訳（捏造せず原文・出典のまま保持・NFR-8）</h2>
  <ul>{c['untrans_html']}</ul>

  <h2>権利運用ブロック（NFR-4）</h2>
  <ul>{c['blocked_html']}</ul>

  <h2>生成物ガバナンス違反（NFR-7）</h2>
  <ul>{c['viol_html']}</ul>

  <h2>収集元フィード</h2>
  <ul>{c['feed_html']}</ul>

  <h2>アクセス解析（読者の所在）</h2>
  <div class="note">
    GitHub Pages は静的配信のためサーバーログが無く、訪問者の所在はこのサイト単体では取得できません。
    <b>外部のアクセス解析サービス</b>（無料・プライバシー配慮の選択肢あり）を接続すると、参照元・国・ページ別の閲覧数が見られます。
    現在は <b>未接続</b>。接続後、ここに各サービスのダッシュボードへのリンク／集計を表示します。
  </div>

  <p class="muted" style="font-size:11px;margin-top:24px;">
    ※ 本ページは静的生成され URL を知れば閲覧可能です（ログイン保護なし）。公開ソースの運用情報のみを掲載しています。
  </p>
</div>
</body>
</html>"""
    out.write_text(page, encoding="utf-8")
    return {"path": str(out), "hosts": c["n_hosts"], "count": c["count"]}


if __name__ == "__main__":
    print("[dashboard]", build_dashboard())
