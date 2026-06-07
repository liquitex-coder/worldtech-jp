"""実収集アダプタ（FR-12 RSS/API 自動収集）。

RSS 2.0 / Atom を汎用に解釈し、**1つの収集器でニュース・arXiv・GitHub releases・YouTube**
を feed URL で吸収する（各 feed にカテゴリ/種別を事前割当＝決定論・捏造しない）。
解析はオフライン・決定論（stdlib xml）。取得は薄いラッパで、失敗 feed はスキップ（NFR-8）。

**運用注意（NFR-4）**：本番で実 feed を有効化する前に、各サイトの robots / 利用規約 /
引用の範囲を必ず確認すること。本文は全文転載せず要約＋原文リンクに留める。
"""
from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from pipeline.core import CATEGORIES, KINDS, RawItem

USER_AGENT = "NewsMatomeBot/0.1 (+https://newsmatome.example/bot; respects robots/ToS)"


def _local(tag: str) -> str:
    """名前空間を外したローカルタグ名（Atom の {ns}entry 等に対応）。"""
    return tag.rsplit("}", 1)[-1]


def parse_feed(xml_text: str, *, category: str, kind: str = "article",
               lang: str = "en") -> list[RawItem]:
    """RSS/Atom テキスト → RawItem 群。出典 URL とタイトルが無い項目は採用しない（NFR-8）。"""
    if category not in CATEGORIES:
        raise ValueError(f"unknown category: {category!r}")
    if kind not in KINDS:
        raise ValueError(f"unknown kind: {kind!r}")
    root = ET.fromstring(xml_text)
    items: list[RawItem] = []
    for node in (e for e in root.iter() if _local(e.tag) in ("item", "entry")):
        title = link = summary = ""
        for ch in node:
            ln = _local(ch.tag)
            if ln == "title" and ch.text:
                title = ch.text.strip()
            elif ln in ("summary", "description") and ch.text:
                summary = ch.text.strip()
            elif ln == "link":
                href = ch.get("href")
                if href:                       # Atom: <link href="...">
                    if ch.get("rel", "alternate") == "alternate" or not link:
                        link = href.strip()
                elif ch.text:                  # RSS: <link>...</link>
                    link = ch.text.strip()
        if not title or not link:              # 出典 or 題なし → 捏造せず除外
            continue
        items.append(RawItem(
            title=title, body=summary or title, source_url=link,
            source_lang=lang, category=category, kind=kind,
        ))
    return items


def fetch(url: str, timeout: float = 10.0) -> str:
    """礼儀正しい UA とタイムアウトで feed を取得（薄いラッパ）。"""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (feed URL)
        return r.read().decode("utf-8", "replace")


@dataclass(frozen=True)
class FeedConfig:
    url: str
    category: str
    kind: str = "article"
    lang: str = "en"


class RSSCollector:
    """feed 設定リストから収集。取得失敗 feed はスキップ（捏造しない）。

    `SampleCollector` と同じ `collect() -> list[RawItem]` インターフェースなので、
    Orchestrator にそのまま差し込める（UI・描画は無改修）。
    """

    def __init__(self, feeds: list[FeedConfig], fetcher=fetch):
        self.feeds = feeds
        self.fetcher = fetcher

    def collect(self) -> list[RawItem]:
        out: list[RawItem] = []
        for f in self.feeds:
            try:
                xml = self.fetcher(f.url)
            except Exception:                  # 取得失敗 → そのfeedは捏造せずスキップ
                continue
            out.extend(parse_feed(xml, category=f.category, kind=f.kind, lang=f.lang))
        return out


# 例（opt-in）。本番は robots/ToS 確認後に有効化（NFR-4）。1収集器で4ソース型を吸収。
EXAMPLE_FEEDS = [
    FeedConfig("http://export.arxiv.org/rss/cs.AI", "AI", "paper", "en"),                # 論文
    FeedConfig("http://export.arxiv.org/rss/cs.RO", "ロボット技術", "paper", "en"),       # 論文
    FeedConfig("https://github.com/pytorch/pytorch/releases.atom", "コード", "code", "en"),  # GitHub
    FeedConfig("https://www.youtube.com/feeds/videos.xml?channel_id=UCXXXX", "動画", "video", "en"),  # YouTube
]
