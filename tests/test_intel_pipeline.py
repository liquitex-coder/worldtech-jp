"""インテリジェンス・パイプライン統合：ガバナンス選別・タスキング添付・決定論のテスト。

サンプルは明示的に collector を渡して使う（実ソース未登録時は公開せず空＝デモを出さない）。
index.html には触れない。
"""
import json

from pipeline.intel_collect import SampleFactCollector
from pipeline.intel_pipeline import run_intel

NOW = "2026-06-08T07:00:00+09:00"


def _sample():
    return SampleFactCollector()


def test_run_intel_publishes_only_confident_cleared_briefs(tmp_path):
    # covers: NFR-8  弱い単一ソース(中未満)は公開せず、法定開示(高)のみ出る
    res = run_intel(NOW, tmp_path, collector=_sample())
    payload = json.loads((tmp_path / "intel.json").read_text(encoding="utf-8"))
    assert res["count"] == payload["count"] == 1            # 開示のみ publishable
    item = payload["entities"][0]
    assert item["entity"] == "ACME Robotics"
    assert item["confidence_label"] == "高"                 # 開示(A)単独 → 高
    assert item["sources"] == ["https://edinet.example/acme/holdings"]
    assert all(b["sources"] for b in item["bullets"])       # 全文に出典


def test_run_intel_attaches_tasking_suggestions(tmp_path):
    # covers: NFR-8  C：既取得を踏まえ次に掘る未取得チャネルを提案（先頭は equity）
    run_intel(NOW, tmp_path, collector=_sample())
    item = json.loads((tmp_path / "intel.json").read_text(encoding="utf-8"))["entities"][0]
    channels = [t["channel"] for t in item["next_tasks"]]
    assert channels and channels[0] == "equity"             # 未取得・高価値・低コスト
    assert "disclosure" not in channels                     # 既取得は提案しない


def test_run_intel_is_deterministic(tmp_path):
    # covers: NFR-8  同じ now → 同じ intel.json
    run_intel(NOW, tmp_path / "a", collector=_sample())
    run_intel(NOW, tmp_path / "b", collector=_sample())
    assert (tmp_path / "a" / "intel.json").read_text(encoding="utf-8") == \
           (tmp_path / "b" / "intel.json").read_text(encoding="utf-8")


def test_run_intel_empty_when_no_real_sources(tmp_path):
    # covers: NFR-8  実ソース未登録（既定）は公開せず空（デモ情報を出さない）
    res = run_intel(NOW, tmp_path)                          # collector 省略＝既定
    payload = json.loads((tmp_path / "intel.json").read_text(encoding="utf-8"))
    assert res["count"] == 0 and payload["entities"] == []
