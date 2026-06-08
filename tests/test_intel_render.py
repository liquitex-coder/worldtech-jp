"""インテリジェンス可視化ページ：確度ラベル・出典リンク・空状態・エスケープ・決定論のテスト。"""
import json

from pipeline.intel_render import build_page, render_intel

PAYLOAD = {
    "generated_at": "2026-06-08T07:00:00+09:00", "count": 1, "engine": "",
    "entities": [{
        "entity": "ACME Robotics", "headline": "Fund-X が 5.2% 取得",
        "confidence": 3, "confidence_label": "高", "derived": False,
        "agent": "ACME Robotics担当アナリスト", "engine": "",
        "bullets": [{"text": "大量保有報告書を提出", "sources": ["https://edinet.example/a"]}],
        "sources": ["https://edinet.example/a"],
        "next_tasks": [{"channel": "equity", "score": 7.0, "reason": "r"}],
    }],
}


def test_page_renders_brief_with_confidence_and_sources():
    # covers: INV-R2  確度ラベルと出典リンクを表示
    page = build_page(PAYLOAD)
    assert "確度: 高" in page
    assert 'href="https://edinet.example/a"' in page
    assert "ACME Robotics" in page
    assert "equity" in page                              # 次タスクのチップ


def test_empty_state_when_no_entities():
    # covers: INV-R2  項目なしは正直に空状態（捏造しない）
    page = build_page({"entities": []})
    assert "まだありません" in page


def test_html_is_escaped():
    # covers: NFR-2  XSS 安全：本文の山括弧はエスケープ
    payload = {"entities": [{"entity": "E", "headline": "<script>x</script>",
                             "confidence": 0, "confidence_label": "未確認",
                             "bullets": [], "sources": [], "next_tasks": []}]}
    page = build_page(payload)
    assert "<script>x</script>" not in page
    assert "&lt;script&gt;" in page


def test_graph_section_rendered_when_present():
    # covers: NFR-8  graph.json があれば関係グラフ節を描く
    graph = {"edges": [{"src": "Fund-X", "dst": "ACME", "relation": "shareholder",
                        "confidence": 3, "confidence_label": "高",
                        "sources": ["https://edinet.example/a"]}]}
    page = build_page(PAYLOAD, graph)
    assert "関係グラフ" in page and "大株主" in page


def test_render_intel_writes_file_and_is_deterministic(tmp_path):
    # covers: NFR-8  intel.json → intel.html、同入力で同出力
    (tmp_path / "intel.json").write_text(json.dumps(PAYLOAD, ensure_ascii=False), encoding="utf-8")
    out1 = tmp_path / "intel1.html"
    out2 = tmp_path / "intel2.html"
    render_intel(tmp_path, out1)
    render_intel(tmp_path, out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")
    assert "確度: 高" in out1.read_text(encoding="utf-8")
