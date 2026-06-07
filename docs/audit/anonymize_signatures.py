"""Regenerate signatures.jsonl with the public handle 'liquitex' (anonymisation).

The signer is the same human (account liquitex); only the displayed identity changes
from the real name to the handle for the public repository. SHA-256 includes the
signer string, so the digests are recomputed via the same clause_signature_record so
the tamper-evident chain stays self-consistent under the handle.

Run from C:\\Users\\user\\Claim-Auditor with PYTHONUTF8=1.
"""
import json
from pathlib import Path

from claim_auditor.analysis.requirement_gap import ClauseProvenance
from claim_auditor.analysis.signing import clause_signature_record

SIGNER, DATE = "liquitex", "2026-06-07"
DOCS = Path(__file__).resolve().parent.parent

TARGETS = [
    ("NEWS_MATOME_REQUIREMENTS",
     "第一マイルストーン全体（§3.1/§3.2/§3.3 補足条項 FR-17〜FR-32・AC-7〜AC-11 ＋ 本書全体）"),
    ("NEWS_MATOME_DONE_B",
     "第一マイルストーン done (AC-1〜AC-11)"),
    ("NEWS_MATOME_REQUIREMENTS_AI_ADDENDUM",
     "AI機能 addendum（§3.4 FR-33〜FR-40・NFR-8・AC-12〜AC-15）"),
    ("NEWS_MATOME_DONE_B_AI_ADDENDUM",
     "AI機能 addendum done（§1.3 AC-12〜AC-15）"),
]

records = []
for anchor, scope in TARGETS:
    prov = ClauseProvenance(proposed_by="human", human_signed=f"{SIGNER} {DATE}")
    rec = clause_signature_record(anchor, scope, prov)
    records.append(rec)
    print(f"{anchor}\n   signer={rec['human_signed']}  sha256={rec['sha256']}")

(DOCS / "audit" / "signatures.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
    encoding="utf-8",
)
print("\nRewrote audit/signatures.jsonl with handle 'liquitex'.")
