"""毎朝7時の定時バッチ入口（FR-32）。

`python -m pipeline.run_daily --now 2026-06-07T07:00:00+09:00` で
収集→統括→日本語化→`data/articles.json` を生成する。時刻は引数で渡す（決定論）。
本番スケジュールは `pipeline/SCHEDULE.md`（毎朝 07:00 JST の cron / Task Scheduler）。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import json

from pipeline.compliance import screen
from pipeline.collect_rss import RSSCollector
from pipeline.core import Orchestrator, PassthroughTranslator, SampleCollector, write_articles
from pipeline.feeds import load_feeds
from pipeline.governance import GovernanceLedger
from pipeline.i18n import build_en_edition
from pipeline.llm_client import build_llm_translator
from pipeline.quality import QualityAuditor
from pipeline.render import build as render_index
from pipeline.search import build_search_index
from pipeline.summarize import sample_summarizer
from pipeline.translate import sample_translator

DEFAULT_NOW = "2026-06-07T07:00:00+09:00"
DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "articles.json"


def _write_json(name: str, payload: dict) -> None:
    (DATA / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_collector():
    """feeds.json が登録されていれば実RSS収集、無ければサンプル（FR-12 / FR-20）。"""
    feeds = load_feeds()
    return (RSSCollector(feeds), True) if feeds else (SampleCollector(), False)


def build_translator(real_feeds: bool):
    """翻訳エンジンを選ぶ（提案→決定論検証→採用・捏造しない, INV-R2 / FR-21）。

    優先：実翻訳API（ANTHROPIC_API_KEY あり）→ サンプル時はコーパス → 実フィードで鍵無しは原文保持。
    """
    llm = build_llm_translator()
    if llm is not None:
        return llm, "llm"
    if not real_feeds:
        return sample_translator(), "corpus(human-verified)"
    return PassthroughTranslator(), ""        # 実フィード＋鍵無し→未翻訳のまま出典付き（NFR-8）


def main(now: str = DEFAULT_NOW, out: Path = OUT) -> dict:
    # 収集元と翻訳エンジンを環境に応じて選択（既定はサンプル＋コーパス＝現状維持）
    collector, real_feeds = build_collector()
    translator, engine = build_translator(real_feeds)
    orch = Orchestrator(collector=collector, translator=translator, summarizer=sample_summarizer())
    print(f"[run_daily] collector={type(collector).__name__} translator={engine or 'passthrough'}")
    articles = orch.run(collected_at=now)

    summary = write_articles(articles, out)
    rendered = render_index(out)                       # データ駆動描画：index.html を生成
    idx = build_search_index(out)                      # 全文検索インデックス（FR-11）
    en = build_en_edition(out)                         # NFR-6：/en/ 英語版＋hreflang 相互リンク
    print(f"[run_daily] search index {idx['docs']} docs -> {idx['path']}")
    print(f"[run_daily] en edition {en['en_pages']} pages, hreflang on {en['ja_hreflang_injected']} JA pages")

    # 公開前ガバナンス（決定論・LLM-free）：権利運用 / 翻訳品質 / 生成物検証
    arts = json.loads(out.read_text(encoding="utf-8"))["articles"]
    comp = screen(arts)                                # NFR-4：権利運用ゲート
    qual = QualityAuditor().report(arts)               # NFR-5：翻訳品質レポート
    gov = GovernanceLedger().audit(arts)               # NFR-7：生成物検証台帳
    _write_json("compliance-report.json", comp)
    _write_json("quality-report.json", qual)
    _write_json("governance-ledger.json", gov)
    print(f"[run_daily] NFR-4 compliance: cleared={len(comp['cleared'])}/{comp['total']} blocked={len(comp['blocked'])}")
    print(f"[run_daily] NFR-5 quality   : translated_pass={qual['passed']}/{qual['translated']} ratio={qual['quality_ratio']}")
    print(f"[run_daily] NFR-7 governance: accepted={gov['accepted']} omitted={gov['omitted']} sound={gov['sound']}")

    translated = sum(1 for a in articles if a.translated)
    print(f"[run_daily] rendered {rendered['rendered']} cards -> index.html")
    print(f"[run_daily] {now}  collected={summary['count']}  "
          f"translated={translated}/{summary['count']}  engine={articles[0].translation_engine if articles else '-'}  "
          f"-> {summary['path']}")
    if translated < summary["count"]:
        print("[run_daily] 一部/全部が未翻訳（コーパス未収録 or 検証不合格）→ 捏造せず原文・出典を保持（NFR-8）。")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", default=DEFAULT_NOW, help="ISO8601 収集時刻（JST）")
    args = ap.parse_args()
    main(now=args.now)
