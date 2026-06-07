"""実RSS収集のフィード設定ローダ（FR-12 / FR-20）。

`pipeline/feeds.json` に収集元を登録すると、`run_daily` が `SampleCollector` の代わりに
実 RSS/Atom を読む `RSSCollector` に切り替わる。**未登録（空）なら現状のサンプルにフォールバック**
するので、設定するまで挙動は変わらない。

運用注意（NFR-4）：登録前に各サイトの robots / 利用規約 / 引用範囲を必ず確認すること。
本文は全文転載せず要約＋原文リンクに留める（compliance.py の権利ゲートも併せて通る）。
不正なカテゴリ/種別の項目は黙って除外する（捏造の温床を断つ）。
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.collect_rss import FeedConfig
from pipeline.core import CATEGORIES, KINDS

FEEDS_PATH = Path(__file__).resolve().parent / "feeds.json"


def load_feeds(path: Path = FEEDS_PATH) -> list[FeedConfig]:
    """feeds.json を読み、妥当な FeedConfig のリストを返す（無効/未登録は空）。"""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    feeds: list[FeedConfig] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        category = item.get("category")
        kind = item.get("kind", "article")
        lang = item.get("lang", "en")
        if not url or category not in CATEGORIES or kind not in KINDS:
            continue                                    # 不正項目は除外（捏造しない）
        feeds.append(FeedConfig(url=url, category=category, kind=kind, lang=lang))
    return feeds
