"""毎朝7時の定時バッチ入口（FR-32）。

`python -m pipeline.run_daily --now 2026-06-07T07:00:00+09:00` で
収集→統括→日本語化→`data/articles.json` を生成する。時刻は引数で渡す（決定論）。
本番スケジュールは `pipeline/SCHEDULE.md`（毎朝 07:00 JST の cron / Task Scheduler）。
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pipeline.core import Orchestrator, write_articles
from pipeline.render import build as render_index
from pipeline.search import build_search_index
from pipeline.summarize import sample_summarizer
from pipeline.translate import sample_translator

DEFAULT_NOW = "2026-06-07T07:00:00+09:00"
OUT = Path(__file__).resolve().parent.parent / "data" / "articles.json"


def main(now: str = DEFAULT_NOW, out: Path = OUT) -> dict:
    # FR-21：人手検証済みコーパスのトランスレータを接続（提案→決定論検証→採用, INV-R2）
    orch = Orchestrator(translator=sample_translator(), summarizer=sample_summarizer())
    articles = orch.run(collected_at=now)
    summary = write_articles(articles, out)
    rendered = render_index(out)                       # データ駆動描画：index.html を生成
    idx = build_search_index(out)                      # 全文検索インデックス（FR-11）
    print(f"[run_daily] search index {idx['docs']} docs -> {idx['path']}")
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
