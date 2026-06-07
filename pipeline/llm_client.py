"""実翻訳エンジン（Claude API）の差込口（FR-21 本番経路）。

設計（INV-R2 / NFR-8）：**LLM は提案者で verdict に非ず**。ここで得た翻訳案は `LLMTranslator` 経由で
必ず `TranslationVerifier`（出典必須・用語一貫性・長さ）を通り、**通った提案だけ採用**される。
API 失敗・検証不合格は **None**（捏造を採用しない）。

有効化条件：環境変数 `ANTHROPIC_API_KEY` があり、かつ `anthropic` SDK が入っている時のみ。
どちらか欠けたら **None を返し**、呼び出し側はコーパス/原文保持にフォールバックする（サイトは壊れない）。
モデルは既定 `claude-opus-4-8`。コスト重視なら `NEWSMATOME_TRANSLATE_MODEL=claude-haiku-4-5` 等で上書き可。
"""
from __future__ import annotations

import os

from pipeline.translate import LLMTranslator, TranslationVerifier

DEFAULT_MODEL = "claude-opus-4-8"

_SYSTEM = (
    "You are a professional translator for a Japanese technology-news site. "
    "Translate the user's text from {src} into natural, accurate Japanese. "
    "Output ONLY the translation — no preamble, no notes, no quotation marks. "
    "Preserve technical terms precisely and do not add information that is not in the source."
)


def build_llm_translator(verifier: TranslationVerifier | None = None) -> LLMTranslator | None:
    """キーと SDK が揃っていれば LLMTranslator を返す。欠ければ None（フォールバック）。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    model = os.environ.get("NEWSMATOME_TRANSLATE_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic()  # キーは環境変数から解決

    def call(text: str, src: str, tgt: str = "ja") -> str:
        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            system=_SYSTEM.format(src=src),
            messages=[{"role": "user", "content": text}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    return LLMTranslator(call, verifier=verifier)
