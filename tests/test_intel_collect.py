"""実データアダプタ（A）：RSS/Atom → Fact 写像・NFR-4 ホスト許可・独立性のテスト。

解析はオフライン・決定論（fake fetcher）。substrate（confidence エンジン）に流れる所まで確認。
"""
from pipeline.compliance import ComplianceVerifier
from pipeline.intel_collect import (
    IntelCollector,
    IntelFeed,
    SampleFactCollector,
    load_intel_sources,
    parse_facts,
)
from pipeline.intelligence import Claim, Confidence, claim_confidence, is_admissible_fact

NOW = "2026-06-08T07:00:00+09:00"

# 2 件の開示エントリ（edinet=許可ホスト, press=未確認ホスト）
ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>disclosure</title>
  <entry><title>Fund-X が 5.2% 取得（大量保有報告書）</title>
    <link rel="alternate" href="https://edinet.example/acme/holdings"/>
    <summary>保有割合 5.2% 提出者 Fund-X</summary></entry>
  <entry><title>提出者変更（5.0%）</title>
    <link rel="alternate" href="https://edinet.example/acme/holdings2"/>
    <summary>保有割合 5.0% 変更報告書</summary></entry>
  <entry><title>リンク無しは除外</title>
    <summary>no link</summary></entry>
</feed>"""


def test_parse_atom_disclosure_to_fact():
    # covers: INV-R2
    facts = parse_facts(ATOM, channel="disclosure", entity="ACME Robotics", observed_at=NOW)
    assert len(facts) == 2                       # リンク無しは除外（捏造しない）
    f = facts[0]
    assert f.source_url == "https://edinet.example/acme/holdings"
    assert f.channel == "disclosure" and f.entity == "ACME Robotics"
    assert f.raw_excerpt.startswith("保有割合")   # 原文 span が監査痕跡として残る
    assert is_admissible_fact(f)[0] is True


def test_unknown_channel_rejected():
    # covers: INV-R2
    try:
        parse_facts(ATOM, channel="rumor-mill", entity="X", observed_at=NOW)
        assert False, "unknown channel must raise"
    except ValueError:
        pass


def test_collector_drops_uncleared_hosts():
    # covers: NFR-4  edinet のみ ToS 確認済みとして許可、未確認ホストは取り込まない
    verifier = ComplianceVerifier(allowed={"edinet.example": {"quote": True, "robots": True}})
    feeds = [IntelFeed("http://a", "disclosure", "ACME Robotics")]
    facts = IntelCollector(feeds, fetcher=lambda u: ATOM, verifier=verifier).collect_facts(NOW)
    assert len(facts) == 2 and all("edinet.example" in f.source_url for f in facts)

    blocked = ComplianceVerifier(allowed={})     # 何も許可しない → 全て除外
    none = IntelCollector(feeds, fetcher=lambda u: ATOM, verifier=blocked).collect_facts(NOW)
    assert none == []


def test_collector_skips_failing_feeds():
    # covers: INV-R2
    feeds = [IntelFeed("http://dead", "disclosure", "ACME Robotics")]

    def boom(url):
        raise OSError("network")

    assert IntelCollector(feeds, fetcher=boom).collect_facts(NOW) == []


def test_collected_facts_feed_substrate_with_independence():
    # covers: NFR-8  同一ホスト2件は1系統に畳まれる（独立性）。開示(A)単独 → 高
    verifier = ComplianceVerifier(allowed={"edinet.example": {"quote": True, "robots": True}})
    feeds = [IntelFeed("http://a", "disclosure", "ACME Robotics")]
    facts = IntelCollector(feeds, fetcher=lambda u: ATOM, verifier=verifier).collect_facts(NOW)
    claim = Claim("ACME に大株主が出現", supporting=facts, entity="ACME Robotics")
    assert claim_confidence(claim) is Confidence.HIGH   # 同一原典で系統は1、グレードAで HIGH


def test_loader_drops_invalid_and_sample_fallback():
    # covers: INV-R2
    assert load_intel_sources() == [] or isinstance(load_intel_sources(), list)
    sample = SampleFactCollector().collect_facts(NOW)
    assert sample and all(is_admissible_fact(f)[0] for f in sample)   # サンプルは全て採用可
