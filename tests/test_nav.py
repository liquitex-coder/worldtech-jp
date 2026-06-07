"""ナビ再編（FR-41）・面白カテゴリ（FR-31）・言語選択（FR-42）のテスト証人。"""
from pathlib import Path

from pipeline.render import _nav

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
ABOUT = (ROOT / "about.html").read_text(encoding="utf-8")


def test_merged_groups_and_new_categories_in_nav():
    # covers: FR-41, AC-16
    # サイエンス＝[サイエンス,テクノロジー] / AI＝[AI,フィジカルAI,ロボット技術,日本のAI]
    assert INDEX.count("catgroup") >= 4                 # 4グループ（サイエンス/AI/コード/面白）
    assert "日本のAI" in INDEX                           # 新カテゴリ
    # AI グループのドロップダウンにロボット技術が統合されている
    ai_group = INDEX.split("面白")[0]
    assert "ロボット技術" in INDEX and "フィジカルAI" in INDEX


def test_fun_category_with_anime_gadget_manga():
    # covers: FR-31
    for c in ("面白", "アニメ", "ガジェット", "漫画"):
        assert c in INDEX                                # おもしろ＝[アニメ,ガジェット,漫画]


def test_language_selector_present():
    # covers: FR-42, AC-17
    assert "lang-select" in INDEX                        # 言語選択UI
    assert "日本語" in INDEX and ">EN<" in INDEX          # 日本語 / English


def test_generated_nav_uses_groups():
    # covers: FR-41
    nav = _nav("フィジカルAI", "../")
    assert "catgroup" in nav and "cat-trigger active" in nav  # フィジカルAI 在籍の AI グループが active
    assert "日本のAI" in nav and "面白" in nav


def test_about_nav_consistent():
    # covers: FR-41
    assert "日本のAI" in ABOUT and "面白" in ABOUT and "lang-select" in ABOUT
