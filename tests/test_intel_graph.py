"""Entity 関係グラフ（②）：辺の確度・非捏造・近傍・JSON 化のテスト（決定論）。"""
from pipeline.intelligence import Claim, Confidence, Fact
from pipeline.intel_graph import (
    Relation,
    build_entity_graph,
    sample_relations,
)

NOW = "2026-06-08T07:00:00+09:00"


def _disclosure():
    return Fact("Fund-X が 5.2% 取得", "https://edinet.example/a", "disclosure",
                raw_excerpt="保有割合 5.2%", observed_at=NOW, entity="ACME")


def test_graph_builds_edges_with_substrate_confidence():
    # covers: NFR-8  辺の確度は claim_confidence（開示単独 → 高）
    g = build_entity_graph(sample_relations())
    assert {"Fund-X", "ACME Robotics", "NewParts Co"} <= g.nodes
    sh = [e for e in g.edges if e.relation == "shareholder"][0]
    assert sh.src == "Fund-X" and sh.dst == "ACME Robotics"
    assert sh.confidence is Confidence.HIGH and sh.confidence_label == "高"
    assert sh.sources == ["https://edinet.example/acme/holdings"]


def test_unfounded_relation_is_not_drawn():
    # covers: INV-R2  裏付けの無い関係は辺にしない（捏造の辺を作らない）
    bad = Relation("X", "Y", "supplier", Claim("無根拠", supporting=[]))
    g = build_entity_graph([bad])
    assert g.edges == [] and g.nodes == set()


def test_unknown_relation_type_dropped():
    # covers: NFR-8  未知の関係種別は採用しない
    rel = Relation("X", "Y", "frenemy", Claim("怪", supporting=[_disclosure()]))
    assert build_entity_graph([rel]).edges == []


def test_min_confidence_threshold_filters_weak_edges():
    # covers: NFR-8  しきい値未満（単一 forum=未確認）は描かない
    weak = Fact("噂", "https://forum.example/x", "forum",
                raw_excerpt="掲示板の噂", observed_at=NOW, entity="ACME")
    rel = Relation("ACME", "Z", "partner", Claim("提携の噂", supporting=[weak]))
    assert build_entity_graph([rel], min_confidence=Confidence.LOW).edges == []  # forum単独=未確認


def test_neighbors_and_to_dict_are_deterministic():
    # covers: NFR-8  近傍取得と JSON 化（決定論順）
    g = build_entity_graph(sample_relations())
    assert len(g.neighbors("ACME Robotics")) == 2          # 大株主と取引先の両端点
    assert len(g.neighbors("ACME Robotics", relation="supplier")) == 1
    d = g.to_dict()
    assert [n["id"] for n in d["nodes"]] == sorted(g.nodes)  # ノードはソート順
    assert d["edges"][0]["confidence_label"] in {"低", "中", "高", "確定", "未確認"}
