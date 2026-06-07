"""要約エンジン（FR-35）＋ 非捏造（NFR-8）のテスト。"""
from pipeline.core import Orchestrator
from pipeline.summarize import SummaryVerifier, sample_summarizer
from pipeline.translate import sample_translator

NOW = "2026-06-07T07:00:00+09:00"


def test_summarizer_returns_verified_bullets():
    # covers: FR-35
    s = sample_summarizer()
    tldr = s.summarize(source_url="https://arxiv.org/abs/2606.01234")
    assert 1 <= len(tldr) <= 3
    assert any("触覚" in b for b in tldr)              # 内容に即した3行


def test_unknown_source_not_fabricated():
    # covers: NFR-8
    assert sample_summarizer().summarize(source_url="https://unknown.example/x") == []


def test_verifier_rejects_too_many_or_empty_or_sourceless():
    # covers: NFR-8
    v = SummaryVerifier()
    assert v.verify(["a", "b", "c", "d"], "https://x")[0] is False   # 4行は不可
    assert v.verify([" "], "https://x")[0] is False                  # 空
    assert v.verify(["ok"], "")[0] is False                          # 出典なし
    assert v.verify(["要点1", "要点2"], "https://x")[0] is True


def test_pipeline_attaches_tldr():
    # covers: FR-35
    arts = Orchestrator(translator=sample_translator(),
                        summarizer=sample_summarizer()).run(collected_at=NOW)
    assert all(1 <= len(a.tldr) <= 3 for a in arts)    # 全記事に3行まとめ
