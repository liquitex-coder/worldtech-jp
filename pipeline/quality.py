"""翻訳品質（NFR-5）：誤訳を抑え、原文を参照できることを**決定論で採点・記録**する。

`TranslationVerifier`（translate.py・採否ゲート）が「採るか否か」なら、本モジュールは採用済み翻訳の
**品質を継続監視**する層。各記事について以下を決定論で確認し、品質レポート（data/quality-report.json）を出す：

- **原文参照可能**：原文出典リンク（source_url）と**原文の併記**（body_original）があること（NFR-5 の核）。
- **用語一貫性**：原文に専門用語があれば訳語が現れること（GLOSSARY 被覆率）。
- **長さの妥当性**：訳が原文比で極端に欠落/水増ししていないこと。

捏造しない：未翻訳（translated=False）は**減点ではなく "untranslated" として正直に集計**し、
品質スコアの分母から除く（嘘の日本語を作っていないことの裏返し）。
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.translate import GLOSSARY, TranslationVerifier


@dataclass(frozen=True)
class QualityRow:
    id: str
    translated: bool
    has_source: bool          # 原文出典リンクあり（NFR-5）
    has_original: bool        # 原文併記あり（参照可能・NFR-5）
    glossary_ok: bool         # 専門用語の訳語一貫性
    length_ok: bool           # 長さの妥当性
    passed: bool              # 翻訳済み＆全チェック合格


class QualityAuditor:
    """採用済み翻訳の品質を決定論で採点する（NFR-5）。"""

    def __init__(self, glossary: dict[str, str] | None = None):
        self.glossary = glossary if glossary is not None else GLOSSARY
        self.verifier = TranslationVerifier(self.glossary)

    def _glossary_ok(self, original: str, translation: str) -> bool:
        low = (original or "").lower()
        for en, ja in self.glossary.items():
            if en in low and ja not in (translation or ""):
                return False
        return True

    def assess(self, a: dict) -> QualityRow:
        translated = bool(a.get("translated"))
        has_source = bool(a.get("source_url"))
        has_original = bool(a.get("body_original")) and bool(a.get("title_original"))
        if not translated:
            # 未翻訳：捏造していない＝正直。品質判定の対象外（passed=False, but not a defect）
            return QualityRow(a.get("id", ""), False, has_source, has_original, True, True, False)
        title_ok, _ = self.verifier.verify(
            a.get("title_original", ""), a.get("title_ja") or "", a.get("source_url") or "")
        body_ok, _ = self.verifier.verify(
            a.get("body_original", ""), a.get("body_ja") or "", a.get("source_url") or "")
        glossary_ok = (self._glossary_ok(a.get("title_original", ""), a.get("title_ja") or "")
                       and self._glossary_ok(a.get("body_original", ""), a.get("body_ja") or ""))
        length_ok = title_ok and body_ok
        passed = has_source and has_original and glossary_ok and length_ok
        return QualityRow(a.get("id", ""), True, has_source, has_original, glossary_ok, length_ok, passed)

    def report(self, articles: list[dict]) -> dict:
        rows = [self.assess(a) for a in articles]
        translated = [r for r in rows if r.translated]
        passed = [r for r in translated if r.passed]
        return {
            "total": len(rows),
            "translated": len(translated),
            "untranslated": len(rows) - len(translated),   # 正直に未翻訳を計上（非捏造）
            "passed": len(passed),
            "quality_ratio": round(len(passed) / len(translated), 3) if translated else None,
            "all_translated_pass": len(passed) == len(translated),
            "rows": [r.__dict__ for r in rows],
        }
