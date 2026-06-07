"""自動化レイヤのテスト証人：フィード選択・翻訳エンジン選択・LLM鍵ゲート（FR-12/FR-21/FR-32）。

外部ネットワーク・APIキー無しで決定論的に検証する。既定（feeds空・鍵無し）でサンプル動作に
フォールバックし、サイトが壊れないことを保証する。
"""
import json

from pipeline.collect_rss import RSSCollector
from pipeline.core import PassthroughTranslator, SampleCollector
from pipeline.feeds import load_feeds
from pipeline.llm_client import build_llm_translator
from pipeline.translate import CorpusTranslator, LLMTranslator
from pipeline import run_daily


def test_feeds_empty_by_default(tmp_path):
    # covers: FR-12
    assert load_feeds(tmp_path / "missing.json") == []     # 未登録 → 空（サンプルにフォールバック）


def test_feeds_parse_and_filter_invalid(tmp_path):
    # covers: FR-12
    p = tmp_path / "feeds.json"
    p.write_text(json.dumps([
        {"url": "https://a.example/rss", "category": "AI", "kind": "paper", "lang": "en"},
        {"url": "https://b.example/rss", "category": "存在しない", "kind": "article"},  # 不正カテゴリ→除外
        {"category": "AI"},                                                            # url無し→除外
    ]), encoding="utf-8")
    feeds = load_feeds(p)
    assert len(feeds) == 1
    assert feeds[0].url == "https://a.example/rss" and feeds[0].category == "AI"


def test_build_collector_uses_sample_when_no_feeds(monkeypatch):
    # covers: FR-12
    monkeypatch.setattr(run_daily, "load_feeds", lambda: [])
    collector, real = run_daily.build_collector()
    assert isinstance(collector, SampleCollector) and real is False


def test_build_collector_uses_rss_when_feeds(monkeypatch):
    # covers: FR-12
    from pipeline.collect_rss import FeedConfig
    monkeypatch.setattr(run_daily, "load_feeds",
                        lambda: [FeedConfig("https://x.example/rss", "AI", "paper", "en")])
    collector, real = run_daily.build_collector()
    assert isinstance(collector, RSSCollector) and real is True


def test_translator_falls_back_to_corpus_for_samples(monkeypatch):
    # covers: FR-21
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    tr, engine = run_daily.build_translator(real_feeds=False)
    assert isinstance(tr, CorpusTranslator) and engine == "corpus(human-verified)"


def test_translator_passthrough_for_real_feeds_without_key(monkeypatch):
    # covers: NFR-8
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    tr, engine = run_daily.build_translator(real_feeds=True)
    assert isinstance(tr, PassthroughTranslator) and engine == ""   # 未翻訳・捏造しない


def test_llm_translator_disabled_without_key(monkeypatch):
    # covers: NFR-8
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert build_llm_translator() is None                  # 鍵が無ければ有効化しない


def test_llm_translator_built_when_key_and_sdk(monkeypatch):
    # covers: FR-21
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import sys, types
    # 軽量なフェイク anthropic SDK を注入（実APIは呼ばない）
    fake = types.ModuleType("anthropic")
    fake.Anthropic = lambda *a, **k: object()
    monkeypatch.setitem(sys.modules, "anthropic", fake)
    tr = build_llm_translator()
    assert isinstance(tr, LLMTranslator)                   # 鍵＋SDKで本番経路が組まれる（検証器は不変）
