"""Self-apply Engine-N (source_coverage): signed requirement → test-witness 被覆.

Reads the signed SPEC (案件定義書.md ＋ 受け入れ定義_done_B.md) and the acceptance
test sources, then measures which signed requirement anchors have a strong test
witness (``# covers: AC-x``). core（署名・実装済み）が全被覆なら緑、over（将来）は
未被覆として正しく残る。決定論・LLM-free。

Run from C:\\Users\\user\\Claim-Auditor with PYTHONUTF8=1.
"""
from pathlib import Path

from claim_auditor.analysis.source_coverage import measure

NS = Path(__file__).resolve().parent.parent.parent          # news-site/
DOCS = NS / "docs"
spec = (
    (DOCS / "案件定義書.md").read_text(encoding="utf-8")
    + "\n"
    + (DOCS / "受け入れ定義_done_B.md").read_text(encoding="utf-8")
)
tests = [
    (NS / "tests" / "test_acceptance.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_pipeline.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_translation.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_collect.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_render.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_summarize.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_llm_translate.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_search.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_about.py").read_text(encoding="utf-8"),
    (NS / "tests" / "test_nav.py").read_text(encoding="utf-8"),
]

# core（署名・第一マイルストーン＋AI addendum, 実装済み）48 アンカー
CORE = {
    *[f"AC-{i}" for i in range(1, 16)],
    *[f"FR-{i}" for i in (1,2,3,4,5,6,7,8,9,10,13,14,15,16,17,18,19,22,23,24,25,26,28,30,33,34,35,36,37,38,39,40)],
    "NFR-3",
}

r = measure(spec, tests, strict_witness=True)
covered = set(r.covered)
uncovered = set(r.uncovered)
core_uncovered = sorted(CORE - covered)
over_uncovered = sorted(uncovered - CORE)

print("=" * 64)
print("Engine-N source_coverage — signed requirement → test witness")
print("=" * 64)
print(f"declared anchors : {r.total}")
print(f"witnessed        : {len(r.covered)}  ratio={r.ratio:.3f}")
print(f"covered          : {', '.join(r.covered)}")
print("-" * 64)
print(f"CORE (signed, built) : {len(CORE)}")
print(f"  CORE covered       : {len(CORE & covered)}/{len(CORE)}")
print(f"  CORE uncovered     : {core_uncovered or '(none) ✅'}")
print(f"OVER (future)        : uncovered (expected) = {over_uncovered}")
print("-" * 64)
if not core_uncovered:
    print("RESULT: ✅ すべての署名 core 要件にテスト証人あり（被覆 100%）。")
else:
    print(f"RESULT: ❌ 未被覆の core 要件: {core_uncovered}")
