"""権利運用ガバナンス（NFR-4）：著作権・各サイト利用規約の順守を**機械チェック**する。

方針（FR-13 / FR-22 / NFR-4）：収集・引用は **全文転載しない（引用範囲に留める）**・**原文出典リンク必須**・
**翻訳である旨の明示**・**収集元の robots/ToS が引用＋リンクを許す範囲**であること。これらを満たさない項目は
**公開に載せない**（捏造ではなく権利侵害の温床を断つ）。判定は決定論（LLM-free）。

実運用では `ALLOWED_SOURCES` に各収集元の ToS 確認結果（引用可否・robots）を人手で登録する。
未登録ドメインは保守的に **不許可**（黙って取り込まない）。
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

# 引用範囲の上限（文字）。これを超える本文は「全文転載の疑い」として弾く（要点紹介に留める）。
MAX_EXCERPT_CHARS = 1000

# 収集元ごとの ToS 確認結果（人手登録）。quote=引用+出典リンクが規約上許される / robots=クロール許可。
# 本番は各サイトの robots.txt・利用規約を確認して登録する（SCHEDULE.md にも運用注記）。
ALLOWED_SOURCES: dict[str, dict] = {
    "techcrunch.example": {"quote": True, "robots": True},
    "arxiv.org": {"quote": True, "robots": True},          # arXiv：要約＋原論文リンクは可
    "github.example": {"quote": True, "robots": True},
    "youtube.example": {"quote": True, "robots": True},     # 公式埋め込み＋出典リンク
    "nature.example": {"quote": True, "robots": True},
    # インテリジェンス基盤のサンプル周辺信号ソース（example ドメイン）。
    # 本番の EDINET/EDGAR 等は robots/ToS 確認のうえ実ホストをここに登録する（NFR-4）。
    "edinet.example": {"quote": True, "robots": True},      # 法定開示（持分異動）サンプル
    "press.example": {"quote": True, "robots": True},       # 取引先/納品先サンプル
    "energy.example": {"quote": True, "robots": True},      # 使用電力量サンプル
}


@dataclass(frozen=True)
class ComplianceResult:
    ok: bool
    reason: str


class ComplianceVerifier:
    """1 記事が権利運用（NFR-4）を満たすか判定する決定論ゲート。"""

    def __init__(self, allowed: dict[str, dict] | None = None, max_excerpt: int = MAX_EXCERPT_CHARS):
        self.allowed = allowed if allowed is not None else ALLOWED_SOURCES
        self.max_excerpt = max_excerpt

    def _host(self, url: str) -> str:
        host = (urlparse(url).netloc or "").lower()
        return host[4:] if host.startswith("www.") else host

    def verify(self, article: dict) -> ComplianceResult:
        src = article.get("source_url") or ""
        if not src:
            return ComplianceResult(False, "no-source")          # 出典なきものは載せない（FR-13）
        host = self._host(src)
        rule = self.allowed.get(host)
        if rule is None:
            return ComplianceResult(False, f"source-not-cleared:{host}")  # ToS 未確認は保守的に不許可
        if not rule.get("quote", False):
            return ComplianceResult(False, f"quote-not-permitted:{host}")
        if not rule.get("robots", False):
            return ComplianceResult(False, f"robots-disallow:{host}")
        # 全文転載の疑い：引用範囲の上限を超える本文は弾く（要点のみ紹介する）
        for field in ("body_original", "body_ja"):
            text = article.get(field) or ""
            if len(text) > self.max_excerpt:
                return ComplianceResult(False, f"excerpt-too-long:{field}")
        # 翻訳明示：翻訳済みなら原文（出典＋原文併記）が残っていること（FR-22 の権利根拠）
        if article.get("translated") and not article.get("body_original"):
            return ComplianceResult(False, "translation-without-original")
        return ComplianceResult(True, "ok")


def screen(articles: list[dict], verifier: ComplianceVerifier | None = None) -> dict:
    """記事群を権利ゲートに通し、許可/不許可とその理由を返す（公開前スクリーニング）。"""
    v = verifier or ComplianceVerifier()
    cleared, blocked = [], []
    for a in articles:
        r = v.verify(a)
        (cleared if r.ok else blocked).append({"id": a.get("id"), "reason": r.reason})
    return {
        "total": len(articles),
        "cleared": [c["id"] for c in cleared],
        "blocked": blocked,
        "all_cleared": not blocked,
    }
