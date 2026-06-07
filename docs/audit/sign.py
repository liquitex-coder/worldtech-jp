"""Record the human (liquitex / 本名 liquitex) signature via the Auditor's canonical
signing path (INV-R1).

The human authorised (2026-06-07): signer='liquitex', scope='第一マイルストーン全体'.
This routes that deliberate decision through analysis.signing.fill_signature_table
(the sole provisional->signed transition, which refuses an empty signer) and emits a
tamper-evident SHA-256 record per signed document. Claude/Auditor never sign (INV-R1);
this only transcribes the human's decision.

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
        "NEWS_MATOME_REQUIREMENTS",
        "第一マイルストーン全体（§3.1/§3.2/§3.3 補足条項 FR-17〜FR-32・AC-7〜AC-11 ＋ 本書全体）",
    ),
    (
        DOCS / "受け入れ定義_done_B.md",
        "NEWS_MATOME_DONE_B",
        "第一マイルストーン done (AC-1〜AC-11)",
    ),
]

records = []
for path, anchor, scope in targets:
    md = path.read_text(encoding="utf-8")
    signed = fill_signature_table(md, signer=SIGNER, date=DATE, scope=scope)
    path.write_text(signed, encoding="utf-8")
    prov = ClauseProvenance(proposed_by="human", human_signed=f"{SIGNER} {DATE}")
    rec = clause_signature_record(anchor, scope, prov)
    records.append(rec)
    print(f"SIGNED {path.name}")
    print(f"   tier={rec['tier']}  signer={rec['human_signed']}")
    print(f"   sha256={rec['sha256']}")

(DOCS / "audit" / "signatures.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
    encoding="utf-8",
)
print("\nWrote tamper-evident records -> audit/signatures.jsonl")
