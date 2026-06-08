"""記者エージェント（B）：grounding 非捏造・確度はコード由来・導出ラベルのテスト。

ML 起草は注入 fake call で再現（オフライン・ネット不要）。
"""
from pipeline.intelligence import Claim, Confidence, Fact, sample_inference
from pipeline.reporter import (
    DeterministicReporter,
    GroundedLine,
    GroundingVerifier,
    LLMReporter,
)

NOW = "2026-06-08T07:00:00+09:00"


def _disclosure(url="https://edinet.example/a"):
    return Fact("Fund-X が 5.2% 取得", url, "disclosure",
                raw_excerpt="保有割合 5.2%", observed_at=NOW, entity="ACME Robotics")


def test_deterministic_reports_grounded_claim():
    # covers: INV-R2  Fact をそのまま出典付きで投影、確度はコード由来
    claim = Claim("ACME に大株主が出現", supporting=[_disclosure()], entity="ACME Robotics")
    brief = DeterministicReporter().report(claim)
    assert brief is not None
    assert brief.confidence is Confidence.HIGH               # 開示(A)単独 → 高
    assert brief.headline == "ACME に大株主が出現"
    assert brief.sources == ["https://edinet.example/a"]
    assert all(ln.sources for ln in brief.bullets)           # 全文に出典あり
    assert brief.agent == "ACME Robotics担当アナリスト"
    assert brief.publishable is True


def test_unfounded_claim_is_not_reported():
    # covers: INV-R2  採用可な Fact が無ければ報じない
    assert DeterministicReporter().report(Claim("無根拠", supporting=[])) is None


def test_grounding_verifier_drops_ungrounded_lines():
    # covers: INV-R2
    v = GroundingVerifier()
    allowed = {"https://edinet.example/a"}
    ok = GroundedLine("裏付けあり", ["https://edinet.example/a"])
    no_src = GroundedLine("出典なし", [])
    fabricated = GroundedLine("捏造出典", ["https://made-up.example/x"])
    assert v.filter([ok, no_src, fabricated], allowed) == [ok]


def test_llm_reporter_drops_fabricated_source_and_keeps_code_confidence():
    # covers: NFR-8  ML が捏造出典を混ぜても除外、確度はコードが決める
    claim = Claim("ACME に大株主が出現", supporting=[_disclosure()], entity="ACME Robotics")

    def fake_call(entity, facts):
        return [
            GroundedLine("Fund-X が大量保有報告書を提出した。", ["https://edinet.example/a"]),
            GroundedLine("株価は急騰する見込みだ。", ["https://made-up.example/forecast"]),  # 捏造
        ]

    brief = LLMReporter(fake_call).report(claim)
    texts = [ln.text for ln in brief.bullets]
    assert "Fund-X が大量保有報告書を提出した。" in texts
    assert all("made-up.example" not in s for ln in brief.bullets for s in ln.sources)
    assert brief.confidence is Confidence.HIGH               # LLM ではなくコード由来
    assert brief.engine == "llm"


def test_llm_failure_falls_back_to_projection():
    # covers: NFR-8  生成失敗/全滅 → 決定論投影に戻す（捏造しない）
    claim = Claim("ACME に大株主が出現", supporting=[_disclosure()], entity="ACME Robotics")

    def boom(entity, facts):
        raise RuntimeError("api down")

    brief = LLMReporter(boom).report(claim)
    assert brief is not None and brief.sources == ["https://edinet.example/a"]


def test_inference_report_is_labeled_derived():
    # covers: INV-R2  導出は推論として明示、確度は前提の最小
    brief = DeterministicReporter().report(sample_inference())
    assert brief.derived is True
    assert brief.headline.endswith("（推論）")
    assert brief.confidence is Confidence.MEDIUM             # 前提=高(大株主)・中(増産) → 中
    assert len(brief.sources) >= 2
