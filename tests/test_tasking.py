"""タスキング層（C）：価値×信頼度×コスト＋独立性ボーナスのテスト（決定論）。"""
from pipeline.intelligence import sample_facts
from pipeline.tasking import covered_channels, next_task, plan, score_task

ALL = ["disclosure", "supply_chain", "energy", "forum"]


def test_disclosure_outranks_forum():
    # covers: NFR-8  高信頼・高価値・低コストの法定開示が先頭
    ranked = plan("ACME", ["forum", "disclosure"])
    assert ranked[0].channel == "disclosure" and ranked[-1].channel == "forum"


def test_unknown_channel_is_dropped():
    # covers: NFR-8  未知チャネルは採点しない（捏造しない）
    assert score_task("ACME", "rumor-mill") is None
    assert all(s.channel in {"disclosure", "energy"}
               for s in plan("ACME", ["disclosure", "x", "energy"]))


def test_diversity_bonus_prefers_uncovered_channel():
    # covers: NFR-8  まだ取得していないチャネルを優先（独立系統を増やす）
    covered = frozenset({"supply_chain"})
    s_unc = score_task("ACME", "energy", covered=covered)          # 未取得
    s_cov = score_task("ACME", "supply_chain", covered=covered)    # 既取得
    assert s_unc.score > s_cov.score                               # 価値の高い既取得より未取得が上
    assert s_unc.covered is False and s_cov.covered is True


def test_covered_channels_derived_from_facts():
    # covers: NFR-8  既取得チャネルは Fact から導出
    cov = covered_channels(sample_facts())
    assert {"disclosure", "supply_chain", "energy"} <= cov


def test_next_task_targets_uncovered_high_value():
    # covers: NFR-8  既に開示・現場を持つなら、次は未取得の高価値チャネルへ
    covered = covered_channels(sample_facts())                     # disclosure/supply_chain/energy
    nxt = next_task("ACME", ALL + ["equity"], covered=covered)
    assert nxt.channel == "equity" and nxt.covered is False        # 未取得・高価値・低コスト


def test_plan_is_deterministic_and_stable():
    # covers: NFR-8  同じ入力→同じ順、同点は入力順を保つ
    a = [s.channel for s in plan("ACME", ALL)]
    b = [s.channel for s in plan("ACME", ALL)]
    assert a == b
    assert a[0] == "disclosure"                                    # 最高 score が先頭
