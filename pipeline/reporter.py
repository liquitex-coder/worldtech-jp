"""記者エージェント（B）：substrate（Fact/Claim/Inference）を消費して記事を起草する。

設計（INV-R2 / NFR-8）：**確度・採否はコードが判定、文章化は ML が提案**。
- 確度は `intelligence.claim_confidence/inference_confidence`（決定論）で計算し、LLM には決めさせない。
- 出典に裏付けられない文は `GroundingVerifier` が弾く（捏造を公開しない＝INV-R2 の錨）。
- 採用可な Fact が無い Claim/Inference は **報じない**（None）。

エンジン選択（`build_reporter`）：`ANTHROPIC_API_KEY`＋`anthropic` SDK が揃えば `LLMReporter`、
欠ければ `DeterministicReporter`（Fact を投影するだけの非捏造ベースライン）。どちらでもサイト・CI は不変。
本モジュールは substrate の消費側で、`run_daily` には未接続（表示不変）。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from pipeline.intelligence import (
    Claim,
    Confidence,
    Inference,
    admit_claim,
    admit_inference,
    confidence_label,
    inference_confidence,
    is_admissible_fact,
    publishable,
)


@dataclass(frozen=True)
class GroundedLine:
    """1 文と、それを裏付ける出典 URL 群（出典なき文は公開しない）。"""
    text: str
    sources: list[str]


@dataclass
class IntelBrief:
    """記者が出力する記事レコード（確度ラベルと出典を必ず保持）。"""
    entity: str
    headline: str
    confidence: Confidence
    bullets: list[GroundedLine]
    sources: list[str]
    derived: bool          # 観測事実の要約か、導出（推論）か
    agent: str             # バイライン（FR-30）
    engine: str            # "" = 決定論投影 / "llm" = ML 起草

    @property
    def confidence_label(self) -> str:
        return confidence_label(self.confidence)

    @property
    def publishable(self) -> bool:
        """確度しきい値（既定=中）。権利側（NFR-4）は compliance に委譲。"""
        return publishable(self.confidence)


class GroundingVerifier:
    """ML が起草した各文を、提供済み Fact の出典に**必ず**マップできるか検証する（INV-R2）。"""

    def verify_line(self, line: GroundedLine, allowed_sources: set[str]) -> bool:
        return bool(line.sources) and all(s in allowed_sources for s in line.sources)

    def filter(self, lines: list[GroundedLine], allowed_sources: set[str]) -> list[GroundedLine]:
        """裏付けのある文だけ残す（出典なし・未提供出典の文は捏造として除外）。"""
        return [ln for ln in lines if self.verify_line(ln, allowed_sources)]


@dataclass(frozen=True)
class _Projection:
    entity: str
    headline: str
    confidence: Confidence
    bullets: list[GroundedLine]
    facts: list                 # 採用可な Fact 群（grounding 用の出典集合の素）
    derived: bool


def _uniq(seq: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for s in seq:
        seen.setdefault(s, None)
    return list(seen)


def _byline(entity: str) -> str:
    return f"{entity}担当アナリスト" if entity else "インテリジェンス担当エージェント"


def _project(obj) -> _Projection | None:
    """Claim/Inference を**出典付きの決定論投影**に落とす（採用不可なら None）。"""
    if isinstance(obj, Inference):
        if not admit_inference(obj).ok:
            return None
        facts: list = []
        bullets: list[GroundedLine] = []
        for c in obj.premises:
            cf = [f for f in c.supporting if is_admissible_fact(f)[0]]
            facts.extend(cf)
            bullets.append(GroundedLine(c.statement, [f.source_url for f in cf]))
        return _Projection(obj.entity, f"{obj.statement}（推論）",
                           inference_confidence(obj), bullets, facts, True)
    if isinstance(obj, Claim):
        adm = admit_claim(obj)
        if not adm.ok:
            return None
        cf = [f for f in obj.supporting if is_admissible_fact(f)[0]]
        bullets = [GroundedLine(f.statement, [f.source_url]) for f in cf]
        return _Projection(obj.entity, obj.statement, adm.confidence, bullets, cf, False)
    raise TypeError(f"unsupported subject: {type(obj).__name__}")


def _brief(proj: _Projection, bullets: list[GroundedLine], engine: str) -> IntelBrief:
    return IntelBrief(
        entity=proj.entity, headline=proj.headline,
        confidence=proj.confidence,                 # 確度は常にコード由来（LLM に決めさせない）
        bullets=bullets,
        sources=_uniq([s for b in bullets for s in b.sources]),
        derived=proj.derived, agent=_byline(proj.entity), engine=engine,
    )


class DeterministicReporter:
    """LLM-free の非捏造ベースライン：Fact をそのまま出典付きで投影する。"""
    engine = ""

    def report(self, obj) -> IntelBrief | None:
        proj = _project(obj)
        return None if proj is None else _brief(proj, proj.bullets, self.engine)


class LLMReporter:
    """ML が文章を起草（提案）し、grounding 検証を通った文だけ採用する。

    `call(entity, facts) -> list[GroundedLine]` は注入式（テストは fake、本番は Claude）。
    検証で全滅したら決定論投影にフォールバック。**確度は常にコードが計算**。
    """
    engine = "llm"

    def __init__(self, call, verifier: GroundingVerifier | None = None):
        self.call = call
        self.verifier = verifier or GroundingVerifier()

    def report(self, obj) -> IntelBrief | None:
        proj = _project(obj)
        if proj is None:
            return None
        allowed = {f.source_url for f in proj.facts}
        try:
            drafted = self.call(proj.entity, proj.facts)
        except Exception:                           # 生成失敗 → 決定論投影に戻す（捏造しない）
            drafted = []
        grounded = self.verifier.filter(drafted, allowed)
        bullets = grounded or proj.bullets          # 裏付けが残らなければ投影にフォールバック
        return _brief(proj, bullets, self.engine)


def build_reporter(verifier: GroundingVerifier | None = None):
    """鍵と SDK が揃えば LLMReporter、欠ければ DeterministicReporter（B の入口）。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return DeterministicReporter()
    try:
        import anthropic
    except ImportError:
        return DeterministicReporter()

    model = os.environ.get("NEWSMATOME_REPORT_MODEL", "claude-opus-4-8")
    client = anthropic.Anthropic()
    _SYSTEM = (
        "You are a Japanese intelligence analyst. Write concise Japanese bullet lines that "
        "ONLY restate the provided facts. For each line, cite the exact source_url(s) you used. "
        "Never add information not present in the facts."
    )

    def call(entity: str, facts: list) -> list[GroundedLine]:
        import json
        payload = [{"statement": f.statement, "source_url": f.source_url} for f in facts]
        resp = client.messages.create(
            model=model, max_tokens=1024, system=_SYSTEM,
            messages=[{"role": "user", "content":
                       f"entity={entity}\nfacts={json.dumps(payload, ensure_ascii=False)}\n"
                       'Return JSON: [{"text": "...", "sources": ["url", ...]}]'}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        try:
            rows = json.loads(text)
        except json.JSONDecodeError:
            return []
        return [GroundedLine(r.get("text", ""), list(r.get("sources", [])))
                for r in rows if isinstance(r, dict)]

    return LLMReporter(call, verifier=verifier)
