"""実 MT/LLM 翻訳経路（FR-21）の「提案→決定論検証→採用」をテスト。

実 API なしで検証するため、client を注入（fake）。LLM は提案者で verdict に非ず（INV-R2）：
良い提案は採用、用語ずれ提案は検証器が **拒否して None**（捏造を採用しない・NFR-8）。
"""
from pipeline.core import Orchestrator, SampleCollector
from pipeline.translate import LLMTranslator


def good_client(text, src, tgt):
    # 用語を守った正しい提案
    table = {
        "A tactile sensor for robots": "ロボットのための触覚センサー",
        "FastVec: vector search in 10 lines": "FastVec：10行で始めるベクトル検索",
    }
    return table.get(text, "（訳）" + text)


def term_drift_client(text, src, tgt):
    # 'tactile' を「触覚」と訳さない＝用語ずれ（検証器が弾くべき提案）
    return "ロボットのための接触センサー"


def raising_client(text, src, tgt):
    raise RuntimeError("API down")


def test_llm_good_proposal_is_accepted():
    # covers: FR-21
    tr = LLMTranslator(good_client)
    out = tr.translate("A tactile sensor for robots", "en", source_url="https://x")
    assert out == "ロボットのための触覚センサー"      # 検証通過で採用
    assert "触覚" in out


def test_llm_term_drift_is_rejected_not_used():
    # covers: NFR-8
    tr = LLMTranslator(term_drift_client)
    # 原文に tactile があるのに訳語「触覚」が無い → 検証器が拒否 → None（採用しない）
    assert tr.translate("A tactile sensor", "en", source_url="https://x") is None


def test_llm_api_failure_does_not_fabricate():
    # covers: NFR-8
    assert LLMTranslator(raising_client).translate("hello", "en", source_url="https://x") is None


def test_llm_engine_pluggable_into_pipeline():
    # covers: FR-21
    orch = Orchestrator(collector=SampleCollector(), translator=LLMTranslator(good_client))
    arts = orch.run(collected_at="2026-06-07T07:00:00+09:00")
    assert arts and arts[0].translation_engine == "llm"   # 実エンジン経路に差替可（UI無改修）
