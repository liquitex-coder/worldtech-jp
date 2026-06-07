"""アクセス解析タグ注入のテスト証人（Cloudflare Web Analytics・トークンゲート）。"""
from pipeline.analytics import apply, snippet


PAGE = "<html><head><title>x</title></head><body>hi</body></html>"


def test_no_tag_without_token():
    # トークン空 → タグを入れない（既定で無効）
    assert snippet("") == ""
    assert apply(PAGE, "") == PAGE


def test_tag_injected_with_token():
    out = apply(PAGE, "tok123")
    assert "static.cloudflareinsights.com/beacon.min.js" in out
    assert '"token": "tok123"' in out
    assert out.index("ANALYTICS:START") < out.index("</head>")   # head 内に入る


def test_injection_is_idempotent():
    once = apply(PAGE, "tok123")
    twice = apply(once, "tok123")
    assert once == twice                                  # 二重化しない
    assert once.count("beacon.min.js") == 1


def test_token_removed_when_cleared():
    on = apply(PAGE, "tok123")
    off = apply(on, "")                                   # トークンを消すとタグも消える
    assert "beacon.min.js" not in off
    assert "ANALYTICS:START" not in off
