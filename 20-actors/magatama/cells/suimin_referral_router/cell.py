"""
SuiminReferralRouterCell — referral routing to LOCAL sleep-medicine care.

Per ADR-2606072800 §Decision 3 G4 (referral-not-treatment) + §Decision 5.

Surfaces WHAT KIND of facility to consult (sleep-medicine outpatient / accredited sleep-testing
center / otolaryngology / respiratory / cardiology comorbidity / pediatric sleep / dental oral
appliance / emergency) and, from a Council-ratified directory, nearby facilities. Presentation
only — NO appointment booking, NO telehealth scheduling, NO device sales (N6/N7).

Pregel graph (3 nodes):

    receive_gated_output         <-  message from suimin_disclaimer_gate
        |
        v
    g4_route                     ->  map condition + urgency -> recommendedFacilityKinds;
                                     attach directory entries (coarse area, no precise geoloc)
        |
        v
    emit_referral                ->  MST PUT com.etzhayyim.suimin.referralPathway
                                  ->  (terminal — patient is pointed to a local clinician)

Tier: B (Per-Domain).
Murakumo node (proposed): levi.
Charter Rider §2 risk: NONE (presentation/routing only; no booking, no PHI in R1).
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# COUNCIL ACTIVATION GATE (ADR-2606072800 §Decision 3 G4)
# ─────────────────────────────────────────────────────────────────────────────
COUNCIL_CHARTER_ATTESTATION_TX_HASH: str | None = None
SILEN_SUIMIN_BASELINE_REVIEW_CID: str | None = None
REFERRAL_DIRECTORY_REGISTRY_CID: str | None = None

if (
    COUNCIL_CHARTER_ATTESTATION_TX_HASH is None
    or SILEN_SUIMIN_BASELINE_REVIEW_CID is None
    or REFERRAL_DIRECTORY_REGISTRY_CID is None
):
    raise RuntimeError(
        "suimin_referral_router cell scaffold-only — Council has not (a) attested the "
        "suimin master charter ADR-2606072800, or (b) ratified the referral directory "
        "registry (G4 referral-only — present which KIND of local sleep-medicine facility to "
        "consult + nearby facilities; NO appointment booking / telehealth scheduling / device "
        "sales). Do not deploy."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pregel super-step skeleton (only reached after the Council gate is removed)
# ─────────────────────────────────────────────────────────────────────────────
#
# from pymagatama.organism import PregelCell
#
# class SuiminReferralRouterCell(PregelCell):
#     process_step = "referral-router"
#     pregel_tier = "B"
#     murakumo_node = "levi"
#
#     def super_step(self, gated_output, directory):
#         # 1. map (conditionSlug, urgency) -> recommendedFacilityKinds (G4)
#         # 2. attach directory entries (coarse area only, no precise patient geoloc)
#         # 3. emit referralPathway (presentation only; no booking, N6/N7)
#         raise NotImplementedError("R1 phase wave implements super_step")
