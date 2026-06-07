"""アクセス解析タグの注入（Cloudflare Web Analytics）。

静的サイトは訪問者ログを持てないため、外部の解析サービスのビーコンを各公開ページの
`<head>` に入れて計測する。**トークンが無ければ何も入れない**（無効化＝既定）。

トークンの渡し方（どちらでも可）：
  1. `pipeline/analytics.json` の `cloudflare_token` に貼る（`analytics.example.json` 参照）
  2. 環境変数 `CF_BEACON_TOKEN`（GitHub Actions Secret 推奨）

注入は冪等（START/END マーカーで囲み、再ビルドで二重化しない）。トークンを消せばタグも消える。
プライバシー：Cloudflare Web Analytics は Cookie 不使用・個人を追跡しない（同意バナー不要）。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

NS = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).resolve().parent / "analytics.json"

START, END = "<!-- ANALYTICS:START -->", "<!-- ANALYTICS:END -->"

# 計測対象の公開ページ（admin.html は対象外＝管理画面は計測しない）
PUBLIC_GLOBS = ["index.html", "article.html", "about.html",
                "articles/*.html", "en/index.html", "en/articles/*.html"]


def load_token() -> str:
    """環境変数 > analytics.json の順でトークンを解決（空文字なら無効）。"""
    env = os.environ.get("CF_BEACON_TOKEN")
    if env:
        return env.strip()
    try:
        return (json.loads(CONFIG.read_text(encoding="utf-8")).get("cloudflare_token") or "").strip()
    except (OSError, json.JSONDecodeError):
        return ""


def snippet(token: str) -> str:
    """Cloudflare Web Analytics の beacon タグ（トークン無しなら空）。"""
    if not token:
        return ""
    safe = token.replace('"', "")                       # 属性内 JSON を壊さない
    return (f"{START}\n"
            f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f"data-cf-beacon='{{\"token\": \"{safe}\"}}'></script>\n"
            f"{END}")


def apply(page_html: str, token: str) -> str:
    """既存の計測ブロックを除去し、トークンがあれば </head> 直前に入れ直す（冪等・可逆）。"""
    s = page_html.find(START)
    if s != -1:
        e = page_html.find(END, s)
        if e != -1:
            e += len(END)
            if page_html[e:e + 1] == "\n":               # 挿入時に足した改行も一緒に除去（可逆）
                e += 1
            page_html = page_html[:s] + page_html[e:]
    block = snippet(token)
    if not block:
        return page_html
    i = page_html.lower().rfind("</head>")
    if i == -1:
        return page_html
    return page_html[:i] + block + "\n" + page_html[i:]


def apply_to_site(token: str | None = None, root: Path = NS) -> dict:
    """全公開ページに計測タグを冪等注入（トークン空なら全ページから除去）。"""
    tok = load_token() if token is None else token
    touched = 0
    for pattern in PUBLIC_GLOBS:
        for path in sorted(root.glob(pattern)):
            html_text = path.read_text(encoding="utf-8")
            new = apply(html_text, tok)
            if new != html_text:
                path.write_text(new, encoding="utf-8")
                touched += 1
    return {"enabled": bool(tok), "pages_updated": touched}


if __name__ == "__main__":
    print("[analytics]", apply_to_site())
