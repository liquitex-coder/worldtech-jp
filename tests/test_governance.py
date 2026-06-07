"""エージェント生成物の検証ガバナンス（NFR-7 / INV-R2）：非捏造監査台帳のテスト証人。"""
from pipeline.governance import GovernanceLedger


def _art(**kw):
    base = dict(id="g1", agent="AI担当エージェント", translation_engine="corpus(human-verified)",
                source_url="https://x.example/a", title_ja="日本語題", body_ja="日本語本文",
                tldr=["a", "b", "c"], translated=True)
    base.update(kw)
    return base


def test_accepted_claims_have_provenance_sound():
    # covers: NFR-7
    audit = GovernanceLedger().audit([_art()])
    assert audit["sound"] is True                            # 採用 claim は全て出典紐付け
    assert audit["accepted"] == 3 and audit["omitted"] == 0  # title_ja/body_ja/tldr 採用
    assert audit["violations"] == []


def test_omitted_when_not_translated_is_recorded_not_fabricated():
    # covers: NFR-7
    audit = GovernanceLedger().audit([_art(translated=False, title_ja=None, body_ja=None, tldr=[])])
    assert audit["accepted"] == 0 and audit["omitted"] == 3  # 捏造せず "出していない" を計上
    assert audit["sound"] is True                            # 採用ゼロでも不変条件は成立


def test_accepted_without_source_is_a_violation():
    # covers: NFR-7
    audit = GovernanceLedger().audit([_art(source_url="")])
    assert audit["sound"] is False                           # 出典なき採用 claim を検出
    assert any(v["reason"] == "accepted-without-provenance" for v in audit["violations"])


def test_ledger_records_engine_and_agent():
    # covers: NFR-7
    audit = GovernanceLedger().audit([_art()])
    e = audit["ledger"][0]
    assert e["agent"] == "AI担当エージェント" and e["engine"] == "corpus(human-verified)"
    assert e["source_url"] == "https://x.example/a"
