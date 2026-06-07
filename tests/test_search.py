"""全文検索（FR-11）のテスト。決定論・オフライン。"""
from pipeline.core import Orchestrator, SampleCollector
from pipeline.search import build_index, search
from pipeline.summarize import sample_summarizer
from pipeline.translate import sample_translator

NOW = "2026-06-07T07:00:00+09:00"


def _index():
    arts = Orchestrator(collector=SampleCollector(), translator=sample_translator(),
                        summarizer=sample_summarizer()).run(collected_at=NOW)
    from dataclasses import asdict
    return build_index([asdict(a) for a in arts])


def test_japanese_query_hits():
    # covers: FR-11
    idx = _index()
    res = search(idx, "触覚")
    assert res and any("ヒューマノイド" in r["title"] for r in res)   # 日本語部分一致


def test_english_query_hits_original():
    # covers: FR-11
    idx = _index()
    res = search(idx, "vector")                       # 原文（英語）にもヒット
    assert res and res[0]["category"] == "コード"


def test_empty_and_nomatch_return_empty():
    # covers: FR-11
    idx = _index()
    assert search(idx, "") == []                       # 空クエリ
    assert search(idx, "zzznomatchzzz") == []          # 無ヒット（捏造しない）


def test_ranking_is_deterministic():
    # covers: FR-11
    idx = _index()
    a = search(idx, "AI")
    b = search(idx, "AI")
    assert [r["id"] for r in a] == [r["id"] for r in b]  # 同一クエリ＝同一順
