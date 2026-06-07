"""エージェント生成物の検証ガバナンス（NFR-7 / INV-R2）：統合監査台帳。

各カテゴリ専門エージェント（収集→翻訳→要約）の**生成物は提案であって verdict に非ず**。本モジュールは
記事ごとに、エージェントが生成した各 claim（日本語タイトル・本文・3行まとめ）を列挙し、

- **provenance（出典紐付け）**：すべての claim が source_url（一次情報）に紐づくこと。
- **accepted（採用）かどうか**：決定論ゲート（翻訳/要約の Verifier）を通った提案だけが accepted。
  未接続/未収録/検証不合格は **omitted（捏造ではなく "出していない"）** として記録する。
- **非捏造の不変条件**：`accepted ⇒ provenance あり`。出典なき採用 claim が 1 件でもあれば台帳は **不正**。

これにより「採用された日本語はすべて原文・出典に紐づき、捏造されていない」ことを機械検証し、
監査証跡（data/governance-ledger.json）として残す。Auditor は署名しない（advisory・INV-R1）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Claim:
    kind: str                 # "title_ja" / "body_ja" / "tldr"
    accepted: bool            # 決定論ゲートを通って採用されたか
    has_provenance: bool      # source_url に紐づくか
    note: str = ""


@dataclass
class LedgerEntry:
    id: str
    agent: str
    source_url: str
    engine: str
    claims: list[Claim] = field(default_factory=list)


class GovernanceLedger:
    """エージェント生成物の採否・出典紐付けを記録し、非捏造不変条件を検証する。"""

    def _claims_for(self, a: dict) -> list[Claim]:
        has_src = bool(a.get("source_url"))
        translated = bool(a.get("translated"))
        claims = [
            Claim("title_ja", accepted=bool(a.get("title_ja")) and translated,
                  has_provenance=has_src,
                  note="" if a.get("title_ja") else "omitted(未接続/不合格→捏造しない)"),
            Claim("body_ja", accepted=bool(a.get("body_ja")) and translated,
                  has_provenance=has_src,
                  note="" if a.get("body_ja") else "omitted(未接続/不合格→捏造しない)"),
            Claim("tldr", accepted=bool(a.get("tldr")),
                  has_provenance=has_src,
                  note="" if a.get("tldr") else "omitted(要約未収録→捏造しない)"),
        ]
        return claims

    def build(self, articles: list[dict]) -> list[LedgerEntry]:
        entries: list[LedgerEntry] = []
        for a in articles:
            entries.append(LedgerEntry(
                id=a.get("id", ""), agent=a.get("agent", ""),
                source_url=a.get("source_url", ""), engine=a.get("translation_engine", ""),
                claims=self._claims_for(a),
            ))
        return entries

    def audit(self, articles: list[dict]) -> dict:
        """非捏造不変条件 `accepted ⇒ provenance` を全 claim で検証し、監査結果を返す。"""
        entries = self.build(articles)
        violations: list[dict] = []
        accepted = omitted = 0
        for e in entries:
            for c in e.claims:
                if c.accepted:
                    accepted += 1
                    if not c.has_provenance:                 # 採用 claim に出典なし＝捏造の温床
                        violations.append({"id": e.id, "claim": c.kind, "reason": "accepted-without-provenance"})
                else:
                    omitted += 1
        return {
            "articles": len(entries),
            "claims": accepted + omitted,
            "accepted": accepted,
            "omitted": omitted,                              # 捏造せず "出していない" の総数
            "violations": violations,
            "sound": not violations,                         # True = 採用claimはすべて出典紐付け（非捏造）
            "ledger": [
                {"id": e.id, "agent": e.agent, "engine": e.engine, "source_url": e.source_url,
                 "claims": [c.__dict__ for c in e.claims]}
                for e in entries
            ],
        }
