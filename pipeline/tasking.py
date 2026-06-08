"""タスキング層（C）：「何を深掘りするか」を期待情報価値×信頼度×コストで決める。

intelligence.rank_channels（信頼度のみの雛形）を置き換える本実装。**決定論・監査可能**で、
どのチャネルを次に掘るかを score で順位付けする。score の核は3軸：

    score = (base_value + diversity_bonus) * reliability_weight / cost

- reliability_weight：Admiralty グレード（法定開示=A 最上位）を 0–1 へ写像（intelligence と同源）。
- base_value：そのチャネルが一般にどれだけ情報を生むかの事前値（forum は低、disclosure は高）。
- diversity_bonus：**まだ取得していないチャネル**を優先（独立系統を増やす＝周辺の積み上げ）。
- cost：相対収集コスト（構造化された開示は安く、現場系は高い）。

設計原則（NFR-8）：決定の確度や採否は substrate（コード）が持ち、ここは**収集の優先順位**だけを
決める。将来 base_value を ML で予測する場合も「提案」に留め、ランキングは監査可能なまま保つ。
本モジュールは `run_daily` 未接続（表示不変）。
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.intelligence import CHANNELS, _GRADE_RANK, is_admissible_fact

# チャネル別の事前情報価値（信頼度とは別軸：forum は不確実だが時に価値、開示は確実で高価値）。
BASE_VALUE: dict[str, float] = {
    "disclosure": 5.0, "equity": 5.0, "filings": 4.0,
    "supply_chain": 4.0, "energy": 3.0, "hiring": 3.0,
    "official": 2.0, "press": 2.0, "forum": 2.0,
}

# 相対収集コスト（構造化・公開された法定開示は安い／現場系は高い）。
DEFAULT_COSTS: dict[str, float] = {
    "disclosure": 1.0, "equity": 1.0, "filings": 1.0, "forum": 1.0,
    "official": 1.0, "press": 2.0, "hiring": 2.0,
    "supply_chain": 3.0, "energy": 3.0,
}

# 未取得チャネルを掘ると独立系統が増える（周辺の積み上げ）→ 価値ボーナス。
DIVERSITY_BONUS = 2.0


def reliability_weight(channel: str) -> float:
    """チャネルの Admiralty 信頼度を 0–1 の重みへ（intelligence と同じ序列）。"""
    return _GRADE_RANK.get(CHANNELS.get(channel, "F"), 0) / _GRADE_RANK["A"]


@dataclass(frozen=True)
class TaskScore:
    """1 つの収集タスク候補（entity×channel）の採点。reason は監査用。"""
    entity: str
    channel: str
    value: float
    reliability: float
    cost: float
    score: float
    covered: bool

    @property
    def reason(self) -> str:
        tag = "既取得" if self.covered else "未取得(独立性+)"
        return (f"value={self.value:.1f} rel={self.reliability:.2f} "
                f"cost={self.cost:.1f} [{tag}]")


def covered_channels(facts: list) -> set[str]:
    """既に Fact を得ているチャネル集合（採用可なもののみ）。"""
    return {f.channel for f in facts if is_admissible_fact(f)[0]}


def score_task(entity: str, channel: str, *, covered: frozenset[str] = frozenset(),
               costs: dict[str, float] | None = None) -> TaskScore | None:
    """1 チャネルを採点。未知チャネルは None（捏造しない）。"""
    if channel not in CHANNELS:
        return None
    cost_map = costs or DEFAULT_COSTS
    is_covered = channel in covered
    value = BASE_VALUE.get(channel, 1.0) + (0.0 if is_covered else DIVERSITY_BONUS)
    rel = reliability_weight(channel)
    cost = cost_map.get(channel, 1.0)
    score = value * rel / cost if cost else 0.0
    return TaskScore(entity, channel, value, rel, cost, score, is_covered)


def plan(entity: str, channels: list[str], *, covered: frozenset[str] = frozenset(),
         costs: dict[str, float] | None = None) -> list[TaskScore]:
    """掘る順を score 降順で返す（決定論・同点は入力順を保つ安定ソート）。"""
    scored = [s for c in channels if (s := score_task(entity, c, covered=covered, costs=costs))]
    return sorted(scored, key=lambda s: -s.score)


def next_task(entity: str, channels: list[str], *, covered: frozenset[str] = frozenset(),
              costs: dict[str, float] | None = None) -> TaskScore | None:
    """次に掘るべき最優先タスク（無ければ None）。"""
    ranked = plan(entity, channels, covered=covered, costs=costs)
    return ranked[0] if ranked else None
