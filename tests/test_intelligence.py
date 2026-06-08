"""インテリジェンス substrate：採否・独立性・矛盾・導出伝播のテスト（INV-R2 / NFR-8）。"""
from pipeline.intelligence import (
    Claim,
    Confidence,
    Fact,
    Inference,
    admit_claim,
    admit_inference,
    claim_confidence,
    confidence_label,
    inference_confidence,
    is_admissible_fact,
    publishable,
    rank_channels,
    sample_inference,
)

NOW = "2026-06-08T07:00:00+09:00"


def _fact(**kw):
    base = dict(statement="s", source_url="https://press.example/x", channel="press",
                raw_excerpt="excerpt", observed_at=NOW)
    base.update(kw)
    return Fact(**base)


def test_fact_admission_requires_source_channel_excerpt():
    # covers: INV-R2
    assert is_admissible_fact(_fact())[0] is True
    assert is_admissible_fact(_fact(source_url=""))[1] == "no-source"
    assert is_admissible_fact(_fact(raw_excerpt="  "))[1] == "no-excerpt"
    assert is_admissible_fact(_fact(channel="made-up"))[1].startswith("unknown-channel")


def test_single_legal_disclosure_reaches_high():
    # covers: NFR-8  法定開示(A)は単独でも高確度
    c = Claim("大株主出現", supporting=[_fact(channel="disclosure",
                                            source_url="https://edinet.example/a")])
    assert claim_confidence(c) is Confidence.HIGH


def test_two_independent_mid_sources_reach_medium():
    # covers: NFR-8  独立2系統(C)の一致 → 中
    c = Claim("増産", supporting=[
        _fact(channel="supply_chain", source_url="https://press.example/s"),
        _fact(channel="energy", source_url="https://energy.example/e"),
    ])
    assert claim_confidence(c) is Confidence.MEDIUM


def test_syndication_is_folded_to_one_system():
    # covers: NFR-8  同一原典の焼き直しは独立性に数えない（本数でなく系統数）
    dup = [_fact(channel="press", source_url="https://press.example/x", origin="wire/1")
           for _ in range(3)]
    assert claim_confidence(Claim("噂", supporting=dup)) is Confidence.LOW


def test_credible_contradiction_lowers_confidence():
    # covers: NFR-8  信頼できる独立な反証は確度を1段下げる
    c = Claim("大株主出現",
              supporting=[_fact(channel="disclosure", source_url="https://edinet.example/a")],
              contradicting=[_fact(channel="press", source_url="https://press.example/deny")])
    assert claim_confidence(c) is Confidence.MEDIUM      # HIGH - 1段


def test_claim_without_evidence_is_not_admitted():
    # covers: INV-R2  裏付けゼロは不採用
    r = admit_claim(Claim("無根拠", supporting=[]))
    assert r.ok is False and r.reason == "no-evidence"


def test_inference_confidence_is_min_of_premises():
    # covers: NFR-8  導出の確度は前提の最弱を超えない
    inf = sample_inference()                              # 前提=高(大株主)・中(増産)
    assert inference_confidence(inf) is Confidence.MEDIUM
    r = admit_inference(inf)
    assert r.ok is True and r.confidence is Confidence.MEDIUM


def test_inference_must_be_flagged_derived():
    # covers: INV-R2  観測事実と導出を分離（公開時のラベル根拠）
    inf = sample_inference()
    inf.derived = False
    assert admit_inference(inf).reason == "not-flagged-derived"


def test_unverified_premise_breaks_the_chain():
    # covers: NFR-8  弱い前提が導出全体の天井になる
    weak = Claim("単一の弱い噂", supporting=[_fact(channel="forum",
                                              source_url="https://forum.example/x")])
    strong = Claim("開示", supporting=[_fact(channel="disclosure",
                                          source_url="https://edinet.example/a")])
    inf = Inference("導出", premises=[weak, strong])
    assert inference_confidence(inf) is Confidence.UNVERIFIED


def test_publish_gate_and_labels():
    # covers: INV-R2  公開は確度しきい値(既定=中)を要求
    assert publishable(Confidence.MEDIUM) is True
    assert publishable(Confidence.LOW) is False
    assert confidence_label(Confidence.CONFIRMED) == "確定"


def test_tasking_ranks_legal_disclosure_first():
    # covers: NFR-8  「どれを掘るか」は信頼度順（法定開示が先頭）
    ranked = rank_channels(["forum", "energy", "disclosure", "press"])
    assert ranked[0] == "disclosure" and ranked[-1] == "forum"
