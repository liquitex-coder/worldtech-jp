"""翻訳品質（NFR-5）：原文参照可能・用語一貫性・長さ妥当・未翻訳は正直のテスト証人。"""
from pipeline.quality import QualityAuditor


def _art(**kw):
    base = dict(id="q1", source_url="https://x.example/a",
                title_original="Tactile sensing for humanoids",
                title_ja="ヒューマノイドの触覚センシング",
                body_original="We integrate tactile sensing into the world model.",
                body_ja="触覚センシングを世界モデルに統合する。",
                translated=True)
    base.update(kw)
    return base


def test_good_translation_passes():
    # covers: NFR-5
    row = QualityAuditor().assess(_art())
    assert row.passed is True
    assert row.has_source and row.has_original and row.glossary_ok and row.length_ok


def test_term_drift_fails_glossary():
    # covers: NFR-5
    # 原文に tactile/humanoid があるのに訳語（触覚/ヒューマノイド）が無い → 用語不一致
    row = QualityAuditor().assess(_art(title_ja="センシングの研究", body_ja="本文の訳。"))
    assert row.glossary_ok is False and row.passed is False


def test_untranslated_is_honest_not_a_defect():
    # covers: NFR-5
    row = QualityAuditor().assess(_art(translated=False, title_ja=None, body_ja=None))
    assert row.translated is False and row.passed is False   # 対象外（捏造していない）
    rep = QualityAuditor().report([_art(translated=False, title_ja=None, body_ja=None)])
    assert rep["untranslated"] == 1 and rep["quality_ratio"] is None


def test_report_counts_pass_ratio():
    # covers: NFR-5
    rep = QualityAuditor().report([_art(id="a"), _art(id="b")])
    assert rep["translated"] == 2 and rep["passed"] == 2
    assert rep["all_translated_pass"] is True and rep["quality_ratio"] == 1.0
