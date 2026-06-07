"""翻訳エンジン（FR-21）＋ 非捏造検証（NFR-8 / INV-R2）のテスト証人。"""
from pipeline.core import Orchestrator
from pipeline.translate import (
    SAMPLE_CORPUS,
    CorpusTranslator,
    TranslationVerifier,
    sample_translator,
)

NOW = "2026-06-07T07:00:00+09:00"


def test_translation_accepts_verified_corpus():
    # covers: FR-21
    tr = sample_translator()
    assert tr.engine_name == "corpus(human-verified)"
    ja = tr.translate("Self-verifying LLMs cut hallucinations", "en",
                      source_url="https://x.example")
    assert ja == "自己検証するLLMが幻覚を減らす"        # 検証を通った人手訳を採用
    assert "幻覚" in ja                                  # 用語一貫性（hallucination→幻覚）


def test_unknown_text_is_not_fabricated():
    # covers: NFR-8
    tr = sample_translator()
    assert tr.translate("Some unseen English sentence.", "en",
                        source_url="https://x.example") is None   # 未収録→捏造しない


def test_verifier_rejects_term_drift_and_sourceless():
    # covers: NFR-8
    v = TranslationVerifier()
    ok, _ = v.verify("A tactile sensor", "ある接触センサー", "https://x")  # 触覚なし→ずれ
    assert ok is False
    ok2, _ = v.verify("hello", "こんにちは", "")          # 出典なし
    assert ok2 is False
    ok3, why = v.verify("Tactile sensing", "触覚センシング", "https://x")
    assert ok3 is True and why == "ok"


def test_pipeline_translates_all_samples_with_provenance():
    # covers: FR-21, NFR-8
    arts = Orchestrator(translator=sample_translator()).run(collected_at=NOW)
    assert arts
    for a in arts:
        assert a.translated is True                      # 全件 翻訳済み（検証通過）
        assert a.title_ja and a.body_ja                  # 日本語が入る
        assert a.body_original                           # 原文は併記（FR-22/NFR-5）
        assert a.source_url and a.translation_engine == "corpus(human-verified)"


def test_corpus_entries_pass_their_own_verifier():
    # covers: NFR-8
    v = TranslationVerifier()
    for src, ja in SAMPLE_CORPUS.items():
        ok, why = v.verify(src, ja, "https://x.example")
        assert ok, f"corpus entry failed verify: {src!r} -> {why}"
