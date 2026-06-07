"""
SuiminSourceIngestCell — read-only ingest of WHITELISTED sources into evidenceRecord.

Per ADR-2606072800 §Decision 2 (source-whitelist invariant G1) + §Decision 5.

suimin does NOT diagnose or treat. This cell only fetches treatment-evidence from sources
that are present in the Council-ratified com.etzhayyim.suimin.sourceWhitelist (PubMed/MeSH,
Cochrane systematic reviews, AASM / national sleep-society clinical practice guidelines,
ICSD-3 / ICD-11 classification anchors) and records each item with verifiable provenance
(PMID / DOI / Cochrane CD-ID / guideline-ID). No claim without a whitelisted source + provenance.

Pregel graph (3 nodes):

    receive_ingest_xrpc          <-  XRPC: operator-initiated ingest request for a
                                     (conditionSlug, treatmentSlug) over whitelisted sources
        |
        v
    g1_whitelist_validate        ->  validate:
                                      - every source resolves to a whitelisted sourceClass
                                      - provenance id present + matches provenanceIdKind
                                      - preprints labeled as preprint (G12)
        |
        v
    emit_evidence_record         ->  MST PUT com.etzhayyim.suimin.evidenceRecord (ungraded)
                                  ->  next-cell message: suimin_evidence_grade

Tier: B (Per-Domain).
Murakumo node (proposed): levi.
Charter Rider §2 risk: NONE (read-only corpus ingest; no PHI — R0/R1 corpus-level only).
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# COUNCIL ACTIVATION GATE (ADR-2606072800 §Decision 3 G1)
# ─────────────────────────────────────────────────────────────────────────────
# Scaffold-only until ALL hold:
#
#   1. Council Lv6+ >= 3 multisig attested the master charter ADR-2606072800
#      (silenSuiminReview scope master-charter-baseline).
#   2. The source whitelist registry is ratified (G1 — scope source-whitelist-baseline).
#
# Any None below -> import-time RuntimeError.

COUNCIL_CHARTER_ATTESTATION_TX_HASH: str | None = None
SILEN_SUIMIN_BASELINE_REVIEW_CID: str | None = None
SOURCE_WHITELIST_REGISTRY_CID: str | None = None

if (
    COUNCIL_CHARTER_ATTESTATION_TX_HASH is None
    or SILEN_SUIMIN_BASELINE_REVIEW_CID is None
    or SOURCE_WHITELIST_REGISTRY_CID is None
):
    raise RuntimeError(
        "suimin_source_ingest cell scaffold-only — Council has not (a) attested the "
        "suimin master charter ADR-2606072800 (silen-suimin master-charter-baseline), "
        "or (b) ratified the source whitelist registry (G1 — only PubMed/Cochrane/"
        "ICSD-3/ICD-11/AASM/national-sleep-society sources are admissible, every claim "
        "needs verifiable provenance). Do not deploy."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pregel super-step skeleton (only reached after the Council gate is removed)
# ─────────────────────────────────────────────────────────────────────────────
#
# from pymagatama.organism import PregelCell, EvidenceRecord
#
# class SuiminSourceIngestCell(PregelCell):
#     process_step = "source-ingest"
#     pregel_tier = "B"
#     murakumo_node = "levi"
#
#     def super_step(self, ingest_xrpc, whitelist):
#         # 1. for each source: resolve sourceClass; reject if not in whitelist (G1)
#         # 2. require provenance id matching provenanceIdKind (G1)
#         # 3. label preprints; never present as established evidence (G12)
#         # 4. emit ungraded evidenceRecord; downstream = suimin_evidence_grade
#         raise NotImplementedError("R1 phase wave implements super_step")
