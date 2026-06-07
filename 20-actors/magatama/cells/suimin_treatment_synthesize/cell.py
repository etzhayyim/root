"""
SuiminTreatmentSynthesizeCell — population-level treatment-evidence landscape.

Per ADR-2606072800 §Decision 3 G2 (grade-mandatory) + G4 (referral-not-treatment) +
G10 (Murakumo-only) + §Decision 5.

Aggregates graded evidenceRecords for one (conditionSlug, treatmentSlug) into a
POPULATION-LEVEL landscape — never an individual recommendation. NO diagnosis, severity (AHI)
judgment, device setting, surgical indication, or prescription (N1-N5, G4). Output is handed to
suimin_disclaimer_gate (G3 invariant) before any patient-facing surfacing.

Pregel graph (3 nodes):

    receive_graded_records       <-  message(s) from suimin_evidence_grade
        |
        v
    g2_g4_synthesize             ->  Murakumo (G10): aggregate into landscape; compute overall
                                     GRADE; keep brand-neutral (device class / INN only, G12);
                                     refuse any individual-level directive (G4)
        |
        v
    emit_synthesis               ->  MST PUT com.etzhayyim.suimin.treatmentSynthesis
                                  ->  next-cell message: suimin_disclaimer_gate (MANDATORY)

Tier: B (Per-Domain).
Murakumo node (proposed): levi.
Charter Rider §2 risk: requires G3 disclaimer (downstream gate) + G4 referral-not-treatment.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# COUNCIL ACTIVATION GATE (ADR-2606072800 §Decision 3 G2 + G4 + G9)
# ─────────────────────────────────────────────────────────────────────────────
COUNCIL_CHARTER_ATTESTATION_TX_HASH: str | None = None
SILEN_SUIMIN_BASELINE_REVIEW_CID: str | None = None
SOURCE_WHITELIST_REGISTRY_CID: str | None = None
PER_TREATMENT_SYNTHESIS_BASELINE_CID: str | None = None

if (
    COUNCIL_CHARTER_ATTESTATION_TX_HASH is None
    or SILEN_SUIMIN_BASELINE_REVIEW_CID is None
    or SOURCE_WHITELIST_REGISTRY_CID is None
    or PER_TREATMENT_SYNTHESIS_BASELINE_CID is None
):
    raise RuntimeError(
        "suimin_treatment_synthesize cell scaffold-only — Council has not (a) attested the "
        "suimin master charter ADR-2606072800, or (b) ratified the source whitelist (G1), "
        "or (c) ratified the per-treatment synthesis baseline (G2 overall-grade-mandatory + "
        "G4 referral-not-treatment: NO individual diagnosis / AHI / device setting / surgical "
        "indication / prescription; G9 witness N>=2 incl. R2+ licensed sleep MD co-sign). "
        "Output MUST pass through suimin_disclaimer_gate (G3). Do not deploy."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pregel super-step skeleton (only reached after the Council gate is removed)
# ─────────────────────────────────────────────────────────────────────────────
#
# from pymagatama.organism import PregelCell
#
# class SuiminTreatmentSynthesizeCell(PregelCell):
#     process_step = "treatment-synthesize"
#     pregel_tier = "B"
#     murakumo_node = "levi"
#
#     def super_step(self, graded_records, baseline):
#         # 1. group by (conditionSlug, treatmentSlug); require >=1 evidenceRecord (G1)
#         # 2. Murakumo synthesize population-level landscape (G10); overall GRADE (G2)
#         # 3. brand-neutral text only (G12); refuse individual directives (G4/N1-N5)
#         # 4. emit treatmentSynthesis; downstream = suimin_disclaimer_gate (G3 invariant)
#         raise NotImplementedError("R1 phase wave implements super_step")
