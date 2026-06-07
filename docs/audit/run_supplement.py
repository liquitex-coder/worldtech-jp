"""Self-apply the Claim-Auditor Requirement Supplement (A vs B) — INV-R6.

Runs claim_auditor.analysis.requirement_gap.meet() on the case-definition draft A and
the done/outcome B, prints the GapReport (gap=抜け / core / over) deterministically.
The Auditor never signs anything; gaps are advisory until a human re-roots (INV-R1).

Run from C:\\Users\\user\\Claim-Auditor with PYTHONUTF8=1.
"""
from pathlib import Path

from claim_auditor.analysis.requirement_gap import meet, render_gap_report

DOCS = Path(__file__).resolve().parent.parent
A = (DOCS / "案件定義書.md").read_text(encoding="utf-8")
B = (DOCS / "受け入れ定義_done_B.md").read_text(encoding="utf-8")

report = meet(A, B)

print("=" * 64)
print("Requirement Supplement self-application — meet(A, B)  [NewsMatome]")
print("=" * 64)
print(render_gap_report(report, b_name="done B"))
print("-" * 64)
print(f"defined      : {report.defined}")
print(f"no_meeting   : {report.no_meeting}")
print(f"union_size   : {report.union_size}")
print(f"gap   (抜け) : {report.gap}")
print(f"core  (確定) : {report.core}")
print(f"over (過剰)  : {report.over}")
