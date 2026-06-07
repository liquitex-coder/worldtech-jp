"""Sign the AI-feature addendum (§3.4 / §1.3) via the Auditor's canonical signing path.

INV-R1: the human (liquitex / 本名 liquitex) authorised signing the AI addendum
(FR-33..40, NFR-8, AC-12..15) on 2026-06-07. fill_signature_table fills the *second*
unsigned `_未署名_` row (the milestone-1 row is already signed, so it no longer matches
the placeholder). Records are APPENDED to signatures.jsonl, preserving milestone-1.
Claude/Auditor never sign (INV-R1); this only transcribes the human's decision.

Run from C:\\Users\\user\\Claim-Auditor with PYTHONUTF8=1.
"""
import json
from pathlib import Path

from claim_auditor.analysis.requirement_gap import ClauseProvenance
from claim_auditor.analysis.signing import (
    clause_signature_record,
    fill_signature_table,
)

DOCS = Path(__file__).resolve().parent.parent
SIGNER, DATE = "liquitex", "2026-06-07"

targets = [
    (
        DOCS / "案件定義書.md",
        "NEWS_MATOME_REQUIREMENTS_AI_ADDENDUM",
        "AI機能 addendum（§3.4 FR-33〜FR-40・NFR-8・AC-12〜AC-15）",
    ),
    (
        DOCS / "受け入れ定義_done_B.md",
        "NEWS_MATOME_DONE_B_AI_ADDENDUM",
        "AI機能 addendum done（§1.3 AC-12〜AC-15）",
    ),
]

records = []
for path, anchor, scope in targets:
    md = path.read_text(encoding="utf-8")
    signed = fill_signature_table(md, signer=SIGNER, date=DATE, scope=scope)
    if signed == md:
        raise SystemExit(f"no unsigned addendum row found in {path.name}")
    path.write_text(signed, encoding="utf-8")
    prov = ClauseProvenance(proposed_by="human", human_signed=f"{SIGNER} {DATE}")
    rec = clause_signature_record(anchor, scope, prov)
    records.append(rec)
    print(f"SIGNED addendum in {path.name}")
    print(f"   tier={rec['tier']}  signer={rec['human_signed']}")
    print(f"   sha256={rec['sha256']}")

sigfile = DOCS / "audit" / "signatures.jsonl"
with sigfile.open("a", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("\nAppended addendum records -> audit/signatures.jsonl")
