"""要約エンジン（FR-35 AI 3行まとめ）＋ 決定論検証（NFR-8 / INV-R2）。

翻訳と同じ設計：**要約は提案であって verdict に非ず**。`SummaryVerifier`（出典必須・
1〜3行・空/長すぎを弾く）を通った提案だけ採用。未収録は **捏造せず空 []**。
本番は LLM 提案に置換可（同検証器を必ず通す）。
"""
from __future__ import annotations


class SummaryVerifier:
    """TL;DR 提案の採否ゲート（INV-R2）。"""

    MAX_BULLETS = 3
    MAX_LEN = 120

    def verify(self, bullets: list[str], source_url: str) -> tuple[bool, str]:
        if not source_url:
            return False, "no-source"
        if not (1 <= len(bullets) <= self.MAX_BULLETS):
            return False, "count"
        for b in bullets:
            if not b or not b.strip():
                return False, "empty"
            if len(b) > self.MAX_LEN:
                return False, "too-long"
        return True, "ok"


class CorpusSummarizer:
    """人手検証済みの 3 行要約を参照。未収録/検証不合格は [] （捏造しない）。"""

    engine_name = "corpus(human-verified)"

    def __init__(self, corpus: dict[str, list[str]], verifier: SummaryVerifier | None = None):
        self.corpus = corpus
        self.verifier = verifier or SummaryVerifier()

    def summarize(self, *, source_url: str, original_text: str = "") -> list[str]:
        bullets = self.corpus.get(source_url)
        if not bullets:
            return []                                # 未収録 → 捏造しない
        ok, _ = self.verifier.verify(bullets, source_url)
        return list(bullets) if ok else []           # 検証不合格も採用しない


# SampleCollector の各記事（source_url キー）に対する人手検証済み 3 行要約
SAMPLE_SUMMARIES = {
    "https://techcrunch.example/self-verify": [
        "大規模モデルが自らの出力を再検証する手法が複数登場。",
        "追加学習なしで既存モデルに適用でき、幻覚を抑制する。",
        "信頼性評価の議論が一段進んだ。",
    ],
    "https://arxiv.org/abs/2606.01234": [
        "全身の触覚センシングを世界モデルに統合する枠組みを提案。",
        "視覚のみより未知地形での転倒回復率が向上。",
        "身体性AIが実機フェーズへ進む裏付けとなる。",
    ],
    "https://github.example/fastvec": [
        "近似最近傍探索を約10行で扱える小さなOSS。",
        "依存が少なくベクトル検索の入門に向く。",
        "話題化でスター数が急増。",
    ],
    "https://youtube.example/watch?v=stairs": [
        "四足歩行ロボットが階段を予測して登る仕組みを解説。",
        "予測的な歩行制御が鍵。",
        "デモ映像で安定した昇降を確認できる。",
    ],
    "https://nature.example/food/vertical": [
        "垂直農法のコスト構造が露地栽培に近づきつつある。",
        "環境制御型農業の経済性を新たに分析。",
        "スケール化の条件が論点。",
    ],
}


def sample_summarizer() -> CorpusSummarizer:
    return CorpusSummarizer(SAMPLE_SUMMARIES)
