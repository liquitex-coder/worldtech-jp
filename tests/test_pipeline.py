"""パイプライン（over 着手）のテスト証人。

実装した over アンカー＝FR-20 収集 / FR-29 エージェント統括 / FR-32 定時バッチ /
NFR-8 非捏造ガバナンス を裏取りする。**FR-21 翻訳エンジンは未実装なので witness しない**
（実装していないものを covered と主張しない＝source_coverage の正しい使い方）。
"""
from pipeline.core import (
    CATEGORIES,
    Orchestrator,
    PassthroughTranslator,
    RawItem,
    SampleCollector,
    category_agent,
)

NOW = "2026-06-07T07:00:00+09:00"


def test_collect_yields_sourced_items():
    # covers: FR-20
    items = SampleCollector().collect()
    assert items, "収集結果が空でない"
    for it in items:
        assert it.source_url.startswith("http")     # 一次情報の出典が必ず付く
        assert it.category in CATEGORIES


def test_each_category_has_specialist_agent():
    # covers: FR-29
    for cat in CATEGORIES:
        assert category_agent(cat) == f"{cat}担当エージェント"   # 13カテゴリに専門エージェント
    try:
        category_agent("存在しない分野")
        assert False, "未知カテゴリは弾くべき"
    except ValueError:
        pass


def test_translator_does_not_fabricate_when_unconnected():
    # covers: NFR-8
    tr = PassthroughTranslator()
    assert tr.engine_name == ""                      # 未接続
    assert tr.translate("Hello world", "en") is None  # 捏造せず None（嘘の日本語を作らない）


def test_admission_rejects_sourceless_and_keeps_provenance():
    # covers: NFR-8
    orch = Orchestrator()
    bad = RawItem("t", "b", source_url="", source_lang="en", category="AI")
    assert orch._admit(bad) is False                 # 出典なしは採用しない
    arts = orch.run(collected_at=NOW)
    assert arts and all(a.source_url for a in arts)   # 全記事に出典
    assert all(a.agent.endswith("担当エージェント") for a in arts)  # バイライン付与


def test_daily_batch_untranslated_but_honest():
    # covers: FR-32, NFR-8
    arts = Orchestrator().run(collected_at=NOW)
    for a in arts:
        assert a.collected_at == NOW                  # 定時バッチの時刻が刻まれる
        assert a.translated is False                  # 翻訳未接続を正直に表現
        assert a.title_ja is None and a.body_ja is None  # 捏造なし
        assert a.body_original                        # 原文は保持（出典紐付け）
