"""パイプライン中核：収集 → カテゴリ専門エージェント統括 → 日本語化 → 記事JSON。

設計原則（NFR-8 / INV-R2）：**LLM/翻訳は提案であって verdict に非ず**。エンジン未接続なら
**捏造せず未翻訳のまま出典付きで残す**。全記事は source_url（一次情報）必須＝出典なき項目は
admission で弾く。決定論（時刻は呼び出し側が渡す・乱数なし）。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

# 13 カテゴリ（FR-23）。各カテゴリに専門エージェントを配置（FR-29）。
CATEGORIES = [
    "サイエンス", "AI", "テクノロジー", "コード", "アルゴリズム",
    "ロボット技術", "フィジカルAI", "アート", "デザイン",
    "動画", "動物", "自然", "農業",
    "日本のAI", "アニメ", "ガジェット", "漫画",   # 追加（2026-06-07）
]
KINDS = {"article", "paper", "code", "video"}


def category_agent(category: str) -> str:
    """カテゴリ → 担当専門エージェント名（FR-29 / FR-30 バイラインの源）。"""
    if category not in CATEGORIES:
        raise ValueError(f"unknown category (no specialist agent): {category!r}")
    return f"{category}担当エージェント"


# ---------------------------------------------------------------- データモデル
@dataclass(frozen=True)
class RawItem:
    """収集された一次情報（翻訳前）。"""
    title: str
    body: str
    source_url: str          # 一次情報の出典（必須・NFR-8/FR-13）
    source_lang: str         # 原言語（例 en/de/zh）
    category: str
    kind: str = "article"
    image: str = ""          # サムネ（無ければ FR-18 プレースホルダで描画）


@dataclass
class Article:
    """サイトが描画する記事レコード（翻訳の有無を正直に保持）。"""
    id: str
    category: str
    kind: str
    agent: str               # 担当エージェント（バイライン・FR-30）
    title_original: str
    title_ja: str | None     # 未接続なら None（捏造しない）
    body_original: str
    body_ja: str | None
    tldr: list[str]          # 要約エンジン未接続なら []（捏造しない）
    source_url: str
    source_lang: str
    translated: bool
    translation_engine: str  # "" = 未接続
    collected_at: str        # 呼び出し側が渡す（決定論）
    image: str = ""          # サムネURL（無ければプレースホルダ・FR-18）


# ---------------------------------------------------------------- 収集（FR-20）
class SampleCollector:
    """オフライン・決定論のサンプル収集元（実 RSS/arXiv/GitHub/YouTube 収集の差込口）。

    本番では RSSCollector / ArxivCollector / GithubCollector / YoutubeCollector を
    実装してここに差し込む。雛形段階は外部依存なしで動かす。
    """

    _ITEMS = [
        ("Self-verifying LLMs cut hallucinations",
         "A line of work shows large models re-checking their own outputs...",
         "https://techcrunch.example/self-verify", "en", "AI", "article",
         "https://picsum.photos/seed/ai1/640/360"),
        ("Tactile-Augmented World Models for Legged Humanoids",
         "We integrate full-body tactile sensing into the world model...",
         "https://arxiv.org/abs/2606.01234", "en", "フィジカルAI", "paper",
         "https://picsum.photos/seed/paper/640/360"),
        ("FastVec: vector search in 10 lines",
         "A tiny OSS library for approximate nearest neighbour search...",
         "https://github.example/fastvec", "en", "コード", "code",
         "https://picsum.photos/seed/code/640/360"),
        ("How quadruped robots predict stairs",
         "An explainer video on predictive locomotion control...",
         "https://youtube.example/watch?v=stairs", "en", "ロボット技術", "video",
         "https://picsum.photos/seed/robot/640/360"),
        ("Vertical farming cost structure nears open-field",
         "New analysis on the economics of controlled-environment agriculture...",
         "https://nature.example/food/vertical", "en", "農業", "article",
         ""),   # 画像なし → FR-18 プレースホルダで描画
    ]

    def collect(self) -> list[RawItem]:
        return [RawItem(*row) for row in self._ITEMS]


# ----------------------------------------------------- 翻訳（FR-21・未接続=正直）
class PassthroughTranslator:
    """翻訳エンジン未接続。**捏造せず None を返す**（嘘の日本語を作らない・NFR-8）。

    本番では MTTranslator / LLMTranslator（出典紐付け・用語検証つき）に差し替える。
    その時のみ translated=True になり、原文は併記され続ける（FR-22/NFR-5）。
    """
    engine_name = ""  # 未接続

    def translate(self, text: str, src: str, tgt: str = "ja", *, source_url: str = "") -> str | None:
        return None


class _NoSummarizer:
    """要約エンジン未接続：常に空（捏造しない）。本番は CorpusSummarizer 等に差替。"""
    engine_name = ""

    def summarize(self, *, source_url: str, original_text: str = "") -> list[str]:
        return []


# ---------------------------------------------- オーケストレータ（FR-29 / FR-32）
class Orchestrator:
    """収集→専門エージェント割当→日本語化→記事化を統括（segment_orchestrator 流）。"""

    def __init__(self, collector=None, translator=None, summarizer=None):
        self.collector = collector or SampleCollector()
        self.translator = translator or PassthroughTranslator()
        self.summarizer = summarizer or _NoSummarizer()

    def _admit(self, raw: RawItem) -> bool:
        """NFR-8 admission：出典なし／カテゴリ不正は採用しない（捏造の温床を断つ）。"""
        return bool(raw.source_url) and raw.category in CATEGORIES and raw.kind in KINDS

    def process(self, raw: RawItem, *, collected_at: str) -> Article:
        agent = category_agent(raw.category)          # FR-29/FR-30
        title_ja = self.translator.translate(raw.title, raw.source_lang, source_url=raw.source_url)
        body_ja = self.translator.translate(raw.body, raw.source_lang, source_url=raw.source_url)
        translated = title_ja is not None and body_ja is not None
        tldr = self.summarizer.summarize(source_url=raw.source_url, original_text=raw.body)
        aid = hashlib.sha1(raw.source_url.encode("utf-8")).hexdigest()[:12]
        return Article(
            id=aid, category=raw.category, kind=raw.kind, agent=agent,
            title_original=raw.title, title_ja=title_ja,
            body_original=raw.body, body_ja=body_ja,
            tldr=tldr,                                # 要約器の出力（未接続なら []・捏造しない）
            source_url=raw.source_url, source_lang=raw.source_lang,
            translated=translated, translation_engine=self.translator.engine_name,
            collected_at=collected_at, image=raw.image,
        )

    def run(self, *, collected_at: str) -> list[Article]:
        out: list[Article] = []
        for raw in self.collector.collect():
            if not self._admit(raw):
                continue
            out.append(self.process(raw, collected_at=collected_at))
        return out


def write_articles(articles: list[Article], path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": articles[0].collected_at if articles else None,
        "count": len(articles),
        "translation_engine": articles[0].translation_engine if articles else "",
        "articles": [asdict(a) for a in articles],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"count": len(articles), "path": str(path)}
