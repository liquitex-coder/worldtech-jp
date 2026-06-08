"""I am You 表紙LP 同期ジェネレータのテスト（決定論・冪等・公開境界の保護）。"""
from scripts.sync_iamyou_lp import to_public

# private 正本の最小サンプル（会員/エージェント発リンクを含む）
SRC = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>I am You</title>
<meta name="description" content="real human-agent platform">
</head>
<body>
<a href="member.html">ログイン</a>
<a class="btn" href="member.html">会員登録</a>
<a href="agent.html">登録フォームへ</a>
<section id="agent"><form class="reg"></form></section>
<script>function openModal(k){}</script>
</body></html>"""


def test_no_member_or_agent_leaks_in_public():
    # covers: NFR-4
    out = to_public(SRC)
    assert 'href="member.html"' not in out      # 会員エリア実体を公開しない
    assert 'href="agent.html"' not in out
    assert "openModal('line')" in out           # 会員系→LINE相談
    assert 'href="#agent"' in out               # 登録→ページ内フォーム


def test_injects_canonical_and_ogp_once():
    # covers: NFR-2
    out = to_public(SRC)
    assert out.count('rel="canonical"') == 1
    assert 'property="og:url"' in out and 'worldtech-jp/iamyou/' in out
    assert "GENERATED — do not edit" in out     # 生成物バナー


def test_transform_is_idempotent():
    # covers: NFR-2
    once = to_public(SRC)
    twice = to_public(once)
    assert once == twice                        # 二重生成しても安定（canonical/バナー二重化なし）
