"""管理ダッシュボード生成のテスト証人（運用可視化）。"""
import json

from pipeline.dashboard import build_dashboard


def _seed(data_dir):
    arts = {"generated_at": "2026-06-07T07:00:00+09:00", "count": 2,
            "translation_engine": "corpus(human-verified)",
            "articles": [
                {"id": "a1", "category": "AI", "kind": "article",
                 "source_url": "https://techcrunch.example/x", "source_lang": "en",
                 "title_original": "X", "title_ja": "エックス", "translated": True},
                {"id": "a2", "category": "農業", "kind": "paper",
                 "source_url": "https://arxiv.org/abs/1", "source_lang": "en",
                 "title_original": "Y", "title_ja": None, "translated": False},
            ]}
    (data_dir / "articles.json").write_text(json.dumps(arts, ensure_ascii=False), encoding="utf-8")
    (data_dir / "compliance-report.json").write_text(
        json.dumps({"total": 2, "cleared": ["a1", "a2"], "blocked": [], "all_cleared": True}), encoding="utf-8")
    (data_dir / "quality-report.json").write_text(
        json.dumps({"total": 2, "translated": 1, "untranslated": 1, "passed": 1, "quality_ratio": 1.0}), encoding="utf-8")
    (data_dir / "governance-ledger.json").write_text(
        json.dumps({"accepted": 3, "omitted": 3, "violations": [], "sound": True}), encoding="utf-8")


def test_dashboard_renders_sources_and_status(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    _seed(data)
    out = tmp_path / "admin.html"
    res = build_dashboard(data_dir=data, out=out)
    page = out.read_text(encoding="utf-8")

    assert res["count"] == 2 and res["hosts"] == 2
    assert "管理ダッシュボード" in page
    assert "techcrunch.example" in page and "arxiv.org" in page   # どこのニュースを拾ったか
    assert "未翻訳" in page and "a2" in page                       # 未翻訳を正直に表示
    assert "アクセス解析" in page and "未接続" in page             # 読者所在＝外部プロバイダ要・未接続
    assert 'name="robots" content="noindex' in page              # 検索除外


def test_dashboard_handles_missing_files(tmp_path):
    data = tmp_path / "data"
    data.mkdir()                                                  # 何も無くても落ちない
    out = tmp_path / "admin.html"
    res = build_dashboard(data_dir=data, out=out)
    assert res["count"] == 0 and out.exists()
