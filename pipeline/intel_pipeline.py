"""インテリジェンス・パイプライン：substrate と A/B/C を結ぶ統合（run_daily 接続点）。

各 Fact を観測命題（Claim）に起こし、記者（B）が確度ラベル付き・出典つきに起草、
**publishable（確度≥中）かつ compliance（NFR-4）通過**のものだけを `data/intel.json` に出す。
各 entity には次に掘るべきチャネル（C のタスキング）を添える。

安全性：公開ニュース面（index.html）には触れない。新しいデータ生成物を1つ増やすだけ。
既定はオフライン決定論（SampleFactCollector＋DeterministicReporter）で、鍵もネットも不要。
確度・採否は substrate（コード）が判定し、文章化のみ ML が提案する分離を維持（NFR-8 / INV-R2）。
"""
from __future__ import annotations

import json
from pathlib import Path

from pipeline.compliance import ComplianceVerifier
from pipeline.intel_collect import build_intel_collector
from pipeline.intelligence import CHANNELS, Claim
from pipeline.reporter import IntelBrief, build_reporter
from pipeline.tasking import covered_channels, plan

DATA = Path(__file__).resolve().parent.parent / "data"


def _cleared(brief: IntelBrief, verifier: ComplianceVerifier) -> bool:
    """記事の全出典ホストが ToS 確認済みか（NFR-4）。出典なしは不可。"""
    if not brief.sources:
        return False
    return all(verifier.verify({"source_url": s, "translated": False}).ok
               for s in brief.sources)


def _next_tasks(entity: str, facts: list, *, limit: int = 3) -> list[dict]:
    """C：既取得チャネルを踏まえ、次に掘るべき未取得チャネルを上位 limit 件。"""
    covered = frozenset(covered_channels(facts))
    ranked = plan(entity, list(CHANNELS), covered=covered)
    uncovered = [t for t in ranked if not t.covered]
    return [{"channel": t.channel, "score": round(t.score, 2), "reason": t.reason}
            for t in uncovered[:limit]]


def run_intel(now: str, data_dir: Path = DATA, *, collector=None, reporter=None,
              verifier: ComplianceVerifier | None = None) -> dict:
    """Fact 収集 → 起草 → ガバナンス選別 → intel.json 生成（決定論）。"""
    collector = collector or build_intel_collector()[0]
    reporter = reporter or build_reporter()
    verifier = verifier or ComplianceVerifier()

    facts = collector.collect_facts(now)
    by_entity: dict[str, list] = {}
    for f in facts:
        by_entity.setdefault(f.entity, []).append(f)

    items: list[dict] = []
    for f in facts:
        # 各 Fact を「観測命題」に起こす（確度はその Fact の信頼度で決まる）
        brief = reporter.report(Claim(f.statement, supporting=[f], entity=f.entity))
        if brief is None or not brief.publishable or not _cleared(brief, verifier):
            continue                                  # 弱い/未確認/未許可は公開しない
        items.append({
            "entity": brief.entity,
            "headline": brief.headline,
            "confidence": int(brief.confidence),
            "confidence_label": brief.confidence_label,
            "derived": brief.derived,
            "agent": brief.agent,
            "engine": brief.engine,
            "bullets": [{"text": ln.text, "sources": ln.sources} for ln in brief.bullets],
            "sources": brief.sources,
            "next_tasks": _next_tasks(brief.entity, by_entity.get(brief.entity, [])),
        })

    payload = {
        "generated_at": now,
        "count": len(items),
        "engine": reporter.engine,
        "entities": items,
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    out = data_dir / "intel.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"count": len(items), "engine": reporter.engine, "path": str(out)}
