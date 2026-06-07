"""権利運用ガバナンス（NFR-4）：出典必須・引用範囲・ToS/robots・翻訳明示のテスト証人。"""
from pipeline.compliance import ComplianceVerifier, screen


def _art(**kw):
    base = dict(id="c1", source_url="https://arxiv.org/abs/2606.01234",
                body_original="short excerpt.", body_ja="短い要約。",
                translated=True)
    base.update(kw)
    return base


def test_cleared_source_passes():
    # covers: NFR-4
    v = ComplianceVerifier()
    assert v.verify(_art()).ok is True                       # ToS 確認済み・引用範囲・原文併記


def test_missing_source_is_blocked():
    # covers: NFR-4
    v = ComplianceVerifier()
    r = v.verify(_art(source_url=""))
    assert r.ok is False and r.reason == "no-source"         # 出典なきものは載せない（FR-13）


def test_uncleared_domain_is_blocked():
    # covers: NFR-4
    v = ComplianceVerifier()
    r = v.verify(_art(source_url="https://unknown-blog.test/x"))
    assert r.ok is False and r.reason.startswith("source-not-cleared")  # ToS 未確認は保守的に不許可


def test_full_text_repost_is_blocked():
    # covers: NFR-4
    v = ComplianceVerifier(max_excerpt=50)
    r = v.verify(_art(body_original="x" * 200))
    assert r.ok is False and r.reason.startswith("excerpt-too-long")    # 全文転載の疑いを弾く


def test_screen_aggregates_cleared_and_blocked():
    # covers: NFR-4
    res = screen([_art(id="ok"), _art(id="bad", source_url="")])
    assert res["cleared"] == ["ok"]
    assert res["blocked"] == [{"id": "bad", "reason": "no-source"}]
    assert res["all_cleared"] is False
