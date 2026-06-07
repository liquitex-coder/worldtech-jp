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
    "A growing body of work shows large language models can re-check their own "
    "outputs before answering. The model drafts a response, then runs a second pass "
    "that looks for unsupported claims, missing citations and logical gaps, and "
    "revises accordingly. Crucially the technique needs no extra training: it wraps "
    "an existing model in a verify-then-answer loop. Early benchmarks report a clear "
    "drop in hallucination rates on question-answering tasks, though the extra pass "
    "adds latency. Researchers caution that self-verification narrows errors but does "
    "not eliminate them, and that a sourced, deterministic check still matters for "
    "high-stakes use.":
        "大規模言語モデルが、回答する前に自らの出力を検証できることを示す研究が増えている。"
        "モデルはまず下書きの回答を作り、続く二段目で根拠のない主張・引用漏れ・論理の飛躍を探し、"
        "必要に応じて書き直す。重要なのは追加学習を必要としない点で、既存モデルを"
        "「検証してから答える」ループで包むだけでよい。初期のベンチマークでは質問応答タスクで"
        "幻覚の発生率が明確に下がったと報告されているが、二段目の処理で応答は遅くなる。"
        "研究者は、自己検証は誤りを狭めるものの根絶はせず、重要な用途では出典に紐づく"
        "決定論的な検証が依然として欠かせないと注意を促す。",
    "Tactile-Augmented World Models for Legged Humanoids":
        "脚式ヒューマノイドのための触覚拡張世界モデル",
    "This paper integrates full-body tactile sensing into the world model of a legged "
    "humanoid robot. Instead of relying on vision alone, the system fuses thousands of "
    "skin-level pressure signals with proprioception to predict how the body will "
    "interact with the ground. On unknown terrain the tactile-augmented model recovers "
    "from slips and stumbles more often than a vision-only baseline. The authors argue "
    "that touch gives embodied AI the kind of fast, local feedback cameras cannot, and "
    "that physical AI is moving from simulation toward real hardware.":
        "本論文は、脚式ヒューマノイドの世界モデルに全身の触覚センシングを統合する。"
        "視覚だけに頼るのではなく、皮膚レベルの数千の圧力信号を自己受容感覚と融合し、"
        "身体が地面とどう相互作用するかを予測する。未知の地形では、触覚を加えたモデルは"
        "視覚のみのベースラインよりも高い頻度で滑りやつまずきから復帰した。著者らは、"
        "触覚はカメラには得られない速く局所的なフィードバックを身体性AIに与えると論じ、"
        "フィジカルAIがシミュレーションから実機へと移りつつあると指摘する。",
    "FastVec: vector search in 10 lines":
        "FastVec：10行で始めるベクトル検索",
    "FastVec is a tiny open-source library that implements approximate nearest "
    "neighbour search in about ten lines of core code. It trades a little accuracy for "
    "a large speed-up, making it a friendly entry point for developers who want vector "
    "search without a heavy database. The library has few dependencies and ships with a "
    "worked example over a small document set. After a popular write-up its star count "
    "climbed quickly. The maintainers note it is meant for learning and prototyping, "
    "not as a replacement for production vector stores.":
        "FastVec は、近似最近傍探索を中核わずか約10行で実装した小さなオープンソースライブラリだ。"
        "わずかな精度と引き換えに大きな高速化を得ており、重厚なデータベースなしでベクトル検索を"
        "試したい開発者にとって入りやすい。依存は少なく、小さな文書集合で動く実例が同梱される。"
        "話題の解説記事をきっかけにスター数は急増した。メンテナは、本番のベクトルストアの代替では"
        "なく、学習や試作のためのものだと注意を添えている。",
    "How quadruped robots predict stairs":
        "四足歩行ロボットはどうやって階段を予測するか",
    "This explainer video walks through how a quadruped robot climbs stairs it has "
    "never seen. The key is predictive locomotion control: the robot estimates the "
    "shape of the steps ahead from a short history of foot contacts and joint angles, "
    "then plans where to place each foot a few moves in advance. The demo shows stable "
    "ascent and descent on staircases of varying height. The narrator stresses that "
    "prediction, not reaction, is what keeps the gait smooth when the ground changes.":
        "この解説動画は、四足歩行ロボットが一度も見たことのない階段をどう登るかを順を追って示す。"
        "鍵となるのは予測的な歩行制御だ。ロボットは足の接地と関節角度の短い履歴から前方の段の形状を"
        "推定し、数手先まで各足の置き場所を計画する。デモでは高さの異なる階段で安定した昇降が示される。"
        "ナレーションは、地面が変化するとき歩容を滑らかに保つのは反応ではなく予測だと強調する。",
    "Vertical farming cost structure nears open-field":
        "垂直農法のコスト構造が露地栽培に近づく",
    "A new analysis argues that the cost structure of vertical farming is edging closer "
    "to open-field agriculture for a handful of crops. Falling prices for LED lighting "
    "and automation, plus year-round yields in a controlled environment, narrow the gap "
    "that energy costs once made unbridgeable. The report cautions that the economics "
    "still favour leafy greens and herbs rather than staple grains, and that cheap "
    "renewable power is the deciding variable. Scaling, it concludes, depends on siting "
    "farms where electricity is both clean and inexpensive.":
        "新しい分析は、垂直農法のコスト構造が一部の作物で露地栽培に近づきつつあると論じる。"
        "LED照明と自動化の価格低下に加え、環境制御下での通年収穫が、かつてエネルギーコストで"
        "埋めがたかった差を縮めている。ただし採算が合うのは主要穀物よりも葉物野菜やハーブであり、"
        "安価な再生可能電力が決定的な変数だと報告は釘を刺す。規模拡大は、電力が清浄かつ安価な"
        "場所に農場を置けるかにかかっていると結論づけている。",
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
