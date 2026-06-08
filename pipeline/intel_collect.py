"""実データアダプタ（A）：外部の公開ソースを Fact 化して substrate に流す。

`collect_rss.py` と同じ薄い取得＋オフライン決定論パースで、RSS/Atom エントリを
`intelligence.Fact` に写像する。各 feed に **channel と entity を事前割当**（決定論・捏造しない）。

NFR-4：`ComplianceVerifier`（権利運用ゲート）で **許可済みホストのみ採用**。未確認ホストは黙って
除外する（取り込まない）。本番で EDINET/EDGAR 等を有効化する前に、各ソースの robots/ToS/引用範囲を
確認し `compliance.ALLOWED_SOURCES` に登録すること。

`pipeline/intel_sources.json` が空/未登録なら `SampleFactCollector` にフォールバック
（サイト・CI は不変）。本モジュールは substrate を埋める入口で、`run_daily` には未接続（表示不変）。
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from pipeline.collect_rss import _local, fetch
from pipeline.compliance import ComplianceVerifier
from pipeline.intelligence import CHANNELS, Fact, is_admissible_fact, sample_facts

INTEL_SOURCES_PATH = Path(__file__).resolve().parent / "intel_sources.json"


@dataclass(frozen=True)
class IntelFeed:
    """1 つの周辺信号ソース（channel と対象 entity を事前割当）。"""
    url: str
    channel: str
    entity: str
    lang: str = "en"


def parse_facts(xml_text: str, *, channel: str, entity: str, observed_at: str,
                lang: str = "en") -> list[Fact]:
    """RSS/Atom テキスト → Fact 群。出典 URL と題が無い項目は採用しない（INV-R2）。

    raw_excerpt はソースの実 span（summary/description、無ければ title）を入れて監査痕跡を残す。
    """
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel: {channel!r}")
    root = ET.fromstring(xml_text)
    facts: list[Fact] = []
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
        fact = Fact(statement=title, source_url=link, channel=channel,
                    raw_excerpt=summary or title, observed_at=observed_at, entity=entity)
        if is_admissible_fact(fact)[0]:        # 構造的に採用可なものだけ
            facts.append(fact)
    return facts


def load_intel_sources(path: Path = INTEL_SOURCES_PATH) -> list[IntelFeed]:
    """intel_sources.json を読み、妥当な IntelFeed を返す（無効/未登録は空）。"""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    feeds: list[IntelFeed] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        channel = item.get("channel")
        entity = item.get("entity")
        if not url or not entity or channel not in CHANNELS:
            continue                            # 不正項目は除外（捏造しない）
        feeds.append(IntelFeed(url=url, channel=channel, entity=entity,
                               lang=item.get("lang", "en")))
    return feeds


class IntelCollector:
    """IntelFeed 群を Fact に収集。取得失敗 feed と未許可ホストはスキップ（NFR-4 / INV-R2）。"""

    def __init__(self, feeds: list[IntelFeed], fetcher=fetch,
                 verifier: ComplianceVerifier | None = None):
        self.feeds = feeds
        self.fetcher = fetcher
        self.verifier = verifier or ComplianceVerifier()

    def _cleared(self, fact: Fact) -> bool:
        """ホストが ToS 確認済み（引用＋出典リンク可）か（NFR-4）。"""
        article = {"source_url": fact.source_url, "body_original": fact.raw_excerpt,
                   "translated": False}
        return self.verifier.verify(article).ok

    def collect_facts(self, observed_at: str) -> list[Fact]:
        out: list[Fact] = []
        for fd in self.feeds:
            try:
                xml = self.fetcher(fd.url)
            except Exception:                   # 取得失敗 → そのfeedは捏造せずスキップ
                continue
            for f in parse_facts(xml, channel=fd.channel, entity=fd.entity,
                                 observed_at=observed_at, lang=fd.lang):
                if self._cleared(f):            # 未確認ホストは取り込まない（NFR-4）
                    out.append(f)
        return out


class SampleFactCollector:
    """オフライン・決定論のサンプル Fact 収集元（実アダプタ未登録時のフォールバック）。"""

    def collect_facts(self, observed_at: str = "2026-06-08T07:00:00+09:00") -> list[Fact]:
        return sample_facts(observed_at)


def build_intel_collector():
    """intel_sources.json が登録されていれば実収集、無ければサンプル（A の入口）。"""
    feeds = load_intel_sources()
    return (IntelCollector(feeds), True) if feeds else (SampleFactCollector(), False)
