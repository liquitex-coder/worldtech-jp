"""実収集アダプタ（FR-12 RSS/Atom）のテスト。解析はオフライン・決定論。"""
from pipeline.collect_rss import FeedConfig, RSSCollector, parse_feed
from pipeline.core import Orchestrator

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Example News</title>
  <item><title>Room-temperature superconductor replicated</title>
    <link>https://news.example/superconductor</link>
    <description>A third party confirms part of the result.</description></item>
  <item><title>No link here, should be skipped</title>
    <description>missing link</description></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>arXiv cs.AI</title>
  <entry><title>Self-verifying language models</title>
    <link rel="alternate" href="https://arxiv.org/abs/2606.55555"/>
    <summary>We propose a self-verification loop.</summary></entry>
</feed>"""


def test_parse_rss_yields_sourced_items():
    # covers: FR-12
    items = parse_feed(RSS, category="サイエンス", kind="article", lang="en")
    assert len(items) == 1                      # link なしは除外（NFR-8）
    it = items[0]
    assert it.source_url == "https://news.example/superconductor"
    assert it.category == "サイエンス" and it.kind == "article"


def test_parse_atom_link_href():
    # covers: FR-12
    items = parse_feed(ATOM, category="AI", kind="paper", lang="en")
    assert items[0].source_url == "https://arxiv.org/abs/2606.55555"
    assert items[0].kind == "paper"


def test_collector_skips_failing_feeds_and_feeds_orchestrator():
    # covers: FR-12
    feeds = [FeedConfig("http://rss", "サイエンス"), FeedConfig("http://atom", "AI", "paper")]
    fake = {"http://rss": RSS, "http://atom": ATOM}

    def fetcher(url):
        if url not in fake:
            raise OSError("network")            # 失敗feedはスキップ
        return fake[url]

    raw = RSSCollector(feeds, fetcher=fetcher).collect()
    assert len(raw) == 2 and all(r.source_url.startswith("http") for r in raw)

    # 同じ collect() インターフェースなので Orchestrator にそのまま差し込める（UI無改修）
    arts = Orchestrator(collector=RSSCollector(feeds, fetcher=fetcher)).run(
        collected_at="2026-06-07T07:00:00+09:00")
    assert len(arts) == 2 and all(a.agent.endswith("担当エージェント") for a in arts)
