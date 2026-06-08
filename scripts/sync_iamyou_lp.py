"""I am You 表紙LP 同期ジェネレータ — private 正本 → 公開版（worldtech Pages /iamyou/）。

**正本は private `iamyou/index.html`**。本スクリプトがそれを読み、公開境界（FR-17 アクセス3層）に
合わせて決定論変換し `worldtech-jp/iamyou/index.html`（公開表紙のみ）を生成する。

変換（冪等・LLM-free）:
  1. 生成物バナーを先頭に付与（公開版を手編集しないための注意書き）。
  2. head に canonical / OGP / twitter（SEO）と「公開ミラー」注記を注入（既にあれば二重注入しない）。
  3. 会員系リンク `member.html` → LINE 相談モーダル（会員エリア実体は非公開/backend）。
  4. エージェント登録リンク `agent.html` → ページ内インラインフォーム `#agent`。

使い方:
  python -m scripts.sync_iamyou_lp --src ../iamyou/index.html --out iamyou/index.html
  （既定: 兄弟ディレクトリ ../iamyou/index.html を正本とする）
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

SITE = "https://liquitex-coder.github.io/worldtech-jp/iamyou/"

_BANNER = (
    "<!-- GENERATED — do not edit. 正本は private `iamyou/index.html`。\n"
    "     更新は private を編集し scripts/sync_iamyou_lp.py で再生成すること。 -->\n"
)

_HEAD_BLOCK = (
    '<!-- 公開 表紙ミラー：会員/エージェントの実体（認証・見積・応募管理・具体価格）は非公開\n'
    '     （private iamyou / backend）。本ページは非会員向け公開LP（FR-17「表紙のみ」）。 -->\n'
    f'<link rel="canonical" href="{SITE}">\n'
    '<meta property="og:type" content="website">\n'
    '<meta property="og:title" content="I am You — Your eyes, hands &amp; feet in Japan">\n'
    '<meta property="og:description" content="リアル人間エージェントPF。現地視察・購入/発送代行・訪問動画。I can be your eyes in Japan.">\n'
    f'<meta property="og:url" content="{SITE}">\n'
    '<meta name="twitter:card" content="summary_large_image">'
)


def to_public(src_html: str) -> str:
    """private 正本HTML → 公開表紙HTML（決定論・冪等）。"""
    out = src_html

    # (1) 生成物バナー（未付与時のみ）
    if "GENERATED — do not edit" not in out:
        out = re.sub(r"(<!DOCTYPE html>\s*\n?)", r"\1" + _BANNER, out, count=1)

    # (2) head 注入（canonical 未挿入時のみ＝冪等）
    if 'rel="canonical"' not in out:
        out = re.sub(
            r'(<meta name="description"[^>]*>\n?)',
            r"\1" + _HEAD_BLOCK + "\n",
            out,
            count=1,
        )

    # (3) 会員系 → LINE 相談モーダル（公開版に会員エリア実体を出さない）
    out = out.replace(
        'href="member.html"',
        "href=\"#\" onclick=\"openModal('line');return false;\"",
    )
    # (4) エージェント登録 → ページ内インラインフォーム
    out = out.replace('href="agent.html"', 'href="#agent"')

    return out


def sync(src: Path, out: Path) -> dict:
    public = to_public(src.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(public, encoding="utf-8")
    leaks = [tok for tok in ('href="member.html"', 'href="agent.html"') if tok in public]
    return {
        "src": str(src), "out": str(out), "bytes": len(public),
        "canonical": 'rel="canonical"' in public,
        "leaks": leaks,                                  # 公開版に残ってはいけない発リンク
    }


def main() -> None:
    here = Path(__file__).resolve().parent.parent          # worldtech-jp/
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(here.parent / "iamyou" / "index.html"),
                    help="private 正本 index.html")
    ap.add_argument("--out", default=str(here / "iamyou" / "index.html"),
                    help="公開版 出力先")
    args = ap.parse_args()
    res = sync(Path(args.src), Path(args.out))
    status = "OK" if not res["leaks"] else f"NG leaks={res['leaks']}"
    print(f"[sync_iamyou_lp] {res['src']} -> {res['out']}  "
          f"({res['bytes']}B, canonical={res['canonical']}) {status}")


if __name__ == "__main__":
    main()
