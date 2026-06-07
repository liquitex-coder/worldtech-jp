"""運営者プロフィール・実績ページ（FR-27）のテスト証人。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ABOUT = (ROOT / "about.html").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")


def test_about_has_services_track_record_profile_contact():
    # covers: FR-27
    assert "サービス" in ABOUT                                  # サービス紹介
    assert "受託開発" in ABOUT and "翻訳・メディア運用代行" in ABOUT and "記事広告" in ABOUT  # 3種
    assert "実績" in ABOUT and "stat-card" in ABOUT             # 実績サマリ
    assert "運営者" in ABOUT and "liquitex" in ABOUT            # 運営者プロフィール
    assert 'id="contact"' in ABOUT and "contact-form" in ABOUT  # お問い合わせフォーム


def test_index_cta_links_to_about():
    # covers: FR-27
    assert "about.html#contact" in INDEX                         # 案件導線が実績ページへ
