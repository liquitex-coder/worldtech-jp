"""全文検索（FR-11）：記事から検索インデックスを構築し、決定論で検索する。

静的サイト向けに `data/search-index.json` を生成（クライアントはこれを読んで絞り込み）。
日本語は分かち書き不要の部分一致、英語は原文にもヒット（原文も索引に含む）。
LLM 不使用・決定論。意味検索（FR-33）は別物（埋め込み）で、本書はキーワード全文検索。
"""
from __future__ import annotations

import json
from pathlib import Path

NS = Path(__file__).resolve().parent.parent
ARTICLES = NS / "data" / "articles.json"
INDEX_OUT = NS / "data" / "search-index.json"


def build_index(articles: list[dict]) -> list[dict]:
    """各記事を検索用ドキュメントへ。title は日本語優先、text は日英＋カテゴリ＋要約を結合。"""
    docs = []
    for a in articles:
        title = a.get("title_ja") or a.get("title_original", "")
        text = " ".join(filter(None, [
            title, a.get("title_original", ""),
            a.get("body_ja") or "", a.get("body_original", ""),
            a.get("category", ""), a.get("kind", ""),
            " ".join(a.get("tldr", []) or []),
        ]))
        docs.append({
            "id": a["id"], "title": title, "category": a.get("category", ""),
            "kind": a.get("kind", "article"),
            "url": f'articles/{a["id"]}.html', "source_url": a.get("source_url", ""),
            "text": text,
        })
    return docs


def search(index: list[dict], query: str, limit: int = 20) -> list[dict]:
    """部分一致＋頻度＋タイトル加点で順位付け。空クエリ／無ヒットは []（捏造しない）。"""
    q = (query or "").strip().lower()
    if not q:
        return []
    scored = []
    for doc in index:
        cnt = doc["text"].lower().count(q)
        if cnt == 0:
            continue
        score = cnt + (3 if q in doc["title"].lower() else 0)
        scored.append((score, doc))
    scored.sort(key=lambda t: (-t[0], t[1]["id"]))   # 決定論順（同点は id）
    return [
        {"id": d["id"], "title": d["title"], "category": d["category"],
         "url": d["url"], "score": s}
        for s, d in scored[:limit]
    ]


def build_search_index(articles_path: Path = ARTICLES, out: Path = INDEX_OUT) -> dict:
    data = json.loads(articles_path.read_text(encoding="utf-8"))
    index = build_index(data.get("articles", []))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"docs": index}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"docs": len(index), "path": str(out)}


if __name__ == "__main__":
    print("[search]", build_search_index())
