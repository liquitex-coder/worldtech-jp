"""翻訳エンジン（FR-21）＋ 決定論検証（NFR-8 / INV-R2）。

設計：**翻訳出力は「提案」**（人手コーパスでも MT/LLM でも）であり、verdict に非ず。
`TranslationVerifier`（出典必須・用語の一貫性・長さの常識）を**通った提案だけ採用**する。
未収録・検証不合格は **捏造せず None**（嘘の日本語を作らない）。原文は常に併記される（FR-22/NFR-5）。
"""
from __future__ import annotations

# 専門用語グロッサリ：原文にこの英語があれば、訳文に規定の日本語が現れること（用語一貫性）
GLOSSARY = {
    "hallucination": "幻覚",
    "tactile": "触覚",
    "humanoid": "ヒューマノイド",
    "world model": "世界モデル",
    "vector search": "ベクトル検索",
    "approximate nearest neighbour": "近似最近傍",
    "quadruped": "四足歩行",
    "vertical farming": "垂直農法",
}


class TranslationVerifier:
    """翻訳提案を採否する決定論ゲート（INV-R2）。LLM/MT は提案者で verdict に非ず。"""

    def __init__(self, glossary: dict[str, str] | None = None):
        self.glossary = glossary if glossary is not None else GLOSSARY

    def verify(self, original: str, translation: str, source_url: str) -> tuple[bool, str]:
        if not source_url:
            return False, "no-source"                        # 出典なきものは採用しない
        if not translation or not translation.strip():
            return False, "empty"
        ratio = len(translation) / max(len(original), 1)
        if not (0.15 <= ratio <= 6.0):                       # 極端な欠落/水増しを弾く
            return False, "length"
        low = original.lower()
        for en, ja in self.glossary.items():
            if en in low and ja not in translation:          # 専門語の訳語ずれを弾く
                return False, f"term:{en}->{ja}"
        return True, "ok"


class CorpusTranslator:
    """人手で検証済みの対訳コーパスを参照する翻訳エンジン。

    アルゴリズムは日本語を**発明しない**：収録された人手訳のみを、検証器に通して返す。
    未収録は None（捏造しない）。本番では MT/LLM 提案に置換可（同じ検証器を必ず通す）。
    """

    engine_name = "corpus(human-verified)"

    def __init__(self, corpus: dict[str, str], verifier: TranslationVerifier | None = None):
        self.corpus = corpus
        self.verifier = verifier or TranslationVerifier()

    def translate(self, text: str, src: str, tgt: str = "ja", *, source_url: str = "") -> str | None:
        candidate = self.corpus.get(text.strip())
        if candidate is None:                                # 未収録 → 捏造しない
            return None
        ok, _reason = self.verifier.verify(text, candidate, source_url or "corpus")
        return candidate if ok else None                    # 検証不合格も採用しない


# 人手検証済みサンプル対訳（SampleCollector の各原文 → 日本語）。原文は併記され続ける。
SAMPLE_CORPUS = {
    "Self-verifying LLMs cut hallucinations":
        "自己検証するLLMが幻覚を減らす",
    "A line of work shows large models re-checking their own outputs...":
        "大規模モデルが自らの出力を再検証する一連の研究が示されている。",
    "Tactile-Augmented World Models for Legged Humanoids":
        "脚式ヒューマノイドのための触覚拡張世界モデル",
    "We integrate full-body tactile sensing into the world model...":
        "全身の触覚センシングを世界モデルに統合する。",
    "FastVec: vector search in 10 lines":
        "FastVec：10行で始めるベクトル検索",
    "A tiny OSS library for approximate nearest neighbour search...":
        "近似最近傍探索のための小さなOSSライブラリ。",
    "How quadruped robots predict stairs":
        "四足歩行ロボットはどうやって階段を予測するか",
    "An explainer video on predictive locomotion control...":
        "予測的な歩行制御を解説する動画。",
    "Vertical farming cost structure nears open-field":
        "垂直農法のコスト構造が露地栽培に近づく",
    "New analysis on the economics of controlled-environment agriculture...":
        "環境制御型農業の経済性に関する新しい分析。",
}


def sample_translator() -> CorpusTranslator:
    """SampleCollector に対応する人手検証済みトランスレータ。"""
    return CorpusTranslator(SAMPLE_CORPUS)


class LLMTranslator:
    """実 MT/LLM 翻訳エンジンの差込口（FR-21 本番経路）。

    **LLM/MT は提案者で verdict に非ず（INV-R2）**。`client(text, src, tgt) -> str` の出力を
    `TranslationVerifier`（出典必須・用語一貫性・長さ）に通し、**通った提案だけ採用**する。
    API 失敗・空・検証不合格は **None**（捏造を採用しない・NFR-8）。

    本番では client を実 API 呼び出しに差し替えるだけ（例：MTサービス / LLM）。検証器は不変。
    """

    engine_name = "llm"

    def __init__(self, client, verifier: TranslationVerifier | None = None):
        self.client = client
        self.verifier = verifier or TranslationVerifier()

    def translate(self, text: str, src: str, tgt: str = "ja", *, source_url: str = "") -> str | None:
        try:
            proposal = self.client(text, src, tgt)
        except Exception:
            return None                                  # API失敗 → 捏造しない
        if not proposal or not proposal.strip():
            return None
        ok, _reason = self.verifier.verify(text, proposal, source_url or "llm")
        return proposal if ok else None                  # 検証不合格は採用しない
