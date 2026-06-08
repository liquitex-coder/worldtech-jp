"""Entity 関係グラフ（②）：周辺の積み上げを「企業ノード × 関係エッジ」で可視化する。

取引先・納品先・大株主などの関係を辺で結び、**各辺の確度は substrate（claim_confidence）**で
決まる。裏付け（採用可な Fact）の無い関係は辺にしない（捏造の辺を作らない＝INV-R2）。

設計（NFR-8 / INV-R2）：辺の有無・確度はコードが判定。関係の抽出（誰と誰が取引か）は将来 ML が
「提案」し、ここで admission/confidence を通す。本モジュールは決定論で `run_daily` 未接続。
出力 `to_dict()` は将来の可視化ページ（グラフ描画）にそのまま渡せる形。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pipeline.intelligence import (
    Claim,
    Confidence,
    admit_claim,
    claim_confidence,
    confidence_label,
)

# 関係種別（辺ラベル）。周辺信号チャネルに対応する代表的な企業間関係。
RELATIONS = {"shareholder", "supplier", "customer", "partner", "subsidiary"}


@dataclass(frozen=True)
class Relation:
    """src →(relation)→ dst を主張する関係。claim が裏付け（Fact 群）と確度を持つ。"""
    src: str
    dst: str
    relation: str
    claim: Claim


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    relation: str
    confidence: Confidence
    sources: list[str]

    @property
    def confidence_label(self) -> str:
        return confidence_label(self.confidence)


@dataclass
class EntityGraph:
    """企業ノードと関係エッジの有向グラフ（辺ごとに確度・出典つき）。"""
    nodes: set[str] = field(default_factory=set)
    edges: list[Edge] = field(default_factory=list)

    def add(self, edge: Edge) -> None:
        self.nodes.add(edge.src)
        self.nodes.add(edge.dst)
        self.edges.append(edge)

    def neighbors(self, entity: str, relation: str | None = None) -> list[Edge]:
        """entity を端点に持つ辺（relation 指定で絞り込み）。"""
        return [e for e in self.edges
                if (e.src == entity or e.dst == entity)
                and (relation is None or e.relation == relation)]

    def to_dict(self) -> dict:
        """可視化/JSON 用の素直な表現（nodes / edges）。決定論順。"""
        return {
            "nodes": [{"id": n} for n in sorted(self.nodes)],
            "edges": [{
                "src": e.src, "dst": e.dst, "relation": e.relation,
                "confidence": int(e.confidence), "confidence_label": e.confidence_label,
                "sources": e.sources,
            } for e in self.edges],
        }


def build_entity_graph(relations: list[Relation], *,
                       min_confidence: Confidence = Confidence.LOW) -> EntityGraph:
    """関係群からグラフを構築。裏付けの無い/しきい値未満の関係は辺にしない（捏造しない）。"""
    g = EntityGraph()
    for r in relations:
        if r.relation not in RELATIONS:
            continue                              # 未知の関係種別は採用しない
        adm = admit_claim(r.claim)
        if not adm.ok:
            continue                              # 採用可な Fact が無い関係は辺にしない（INV-R2）
        conf = claim_confidence(r.claim)
        if int(conf) < int(min_confidence):
            continue                              # しきい値未満は描かない（既定=低以上）
        g.add(Edge(r.src, r.dst, r.relation, conf, _sources(r.claim)))
    return g


def _sources(claim: Claim) -> list[str]:
    seen: dict[str, None] = {}
    for f in claim.supporting:
        seen.setdefault(f.source_url, None)
    return list(seen)


def sample_relations(observed_at: str = "2026-06-08T07:00:00+09:00") -> list[Relation]:
    """決定論サンプル：ACME を中心にした関係（大株主・取引先）。"""
    from pipeline.intelligence import Fact

    holding = Fact("Fund-X が ACME Robotics 株を5.2%取得（大量保有報告書）",
                   "https://edinet.example/acme/holdings", "disclosure",
                   raw_excerpt="保有割合 5.2% 提出者 Fund-X", observed_at=observed_at,
                   entity="ACME Robotics")
    supply = Fact("ACME Robotics が NewParts Co と部品供給契約",
                  "https://press.example/acme-supplier", "supply_chain",
                  raw_excerpt="ACME は NewParts Co と供給契約を締結", observed_at=observed_at,
                  entity="ACME Robotics")
    return [
        Relation("Fund-X", "ACME Robotics", "shareholder",
                 Claim("Fund-X は ACME の大株主", supporting=[holding], entity="ACME Robotics")),
        Relation("ACME Robotics", "NewParts Co", "supplier",
                 Claim("ACME は NewParts Co から調達", supporting=[supply], entity="ACME Robotics")),
    ]
