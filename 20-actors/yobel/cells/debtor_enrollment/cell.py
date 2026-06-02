"""
DebtorEnrollmentCell — Pregel cell running eligibility DMN + cross-check creditor enrollments.

Per ADR-2605201800 §Decision + dmn/eligibility-by-rite-type.md (FIRST hit, R12/R13 short-circuit).

Trigger: enrollDebtor XRPC request scoped to a `status=active` rite
Effect:
  - Validate input + verify debtor SBT (Charter §1.13 invariant)
  - Run FIRST-hit DMN eligibility-by-rite-type (R12 SBT gate + R13 §2(b) instrument gate short-circuit)
  - Cross-check creditor enrollments for matching debtor (pairing for release_settlement)
  - XChaCha20-Poly1305-envelope eligibilityProof (PII)
  - Anchor debtorEnrollment MST record (skip Base L2 anchor when eligible=false to save gas)

Murakumo node: issachar (discernment + scholar — Gen 49:14-15, 1 Chr 12:32).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver


RiteType = Literal[
    "shmita_7yr",
    "yobel_50yr",
    "tokusei_rei",
    "religious_jubilee",
    "political_amnesty",
]

PROHIBITED_INSTRUMENTS_R13 = frozenset({"liquidation", "margin_call", "seizure"})


class DebtorEnrollmentState(TypedDict, total=False):
    # Input — from enrollDebtor lexicon
    rite_id: str
    debtor_did: str
    debtor_entity_type: str  # MUST be "natural_person" — schema-enforced + R14 DMN gate
    eligibility_proof: str

    # Loaded rite + creditor context
    rite_status: str
    rite_type: RiteType
    rite_effective_date: str
    rite_jurisdiction_scope: list[str]
    matched_debts: list[dict]  # from cross-check against creditor enrollments

    # Validation results
    input_valid: bool
    debtor_sbt_level: int
    debtor_sbt_entity_type: str  # resolved from CouncilSBT entityType claim
    debtor_community_member: bool
    debtor_jurisdiction_iso3: str

    # DMN output
    eligible: bool
    dmn_rule_fired: str
    dmn_reasons: list[str]

    # Outputs
    enrollment_id: str
    encrypted_proof_cid: str
    enrollment_vertex_uri: str
    pairing_status: Literal["paired", "unpaired"]


def build_graph(
    checkpointer: BaseCheckpointSaver,
    rite_registry_port,
    creditor_enrollment_port,
    council_sbt_port,
    charter_compliance_port,
    envelope_crypto,
    anchor_bridge,
):
    g = StateGraph(DebtorEnrollmentState)

    g.add_node("validate_input", validate_input)
    g.add_node("load_rite_context", lambda s: load_rite_context(s, rite_registry_port))
    g.add_node("verify_debtor_sbt", lambda s: verify_debtor_sbt(s, council_sbt_port, charter_compliance_port))
    g.add_node("cross_check_creditor_enrollments", lambda s: cross_check_creditor_enrollments(s, creditor_enrollment_port))
    g.add_node("run_eligibility_dmn", run_eligibility_dmn)
    g.add_node("encrypt_proof", lambda s: encrypt_proof(s, envelope_crypto))
    g.add_node("anchor_enrollment", lambda s: anchor_enrollment(s, anchor_bridge, anchor=True))
    g.add_node("anchor_enrollment_ineligible", lambda s: anchor_enrollment(s, anchor_bridge, anchor=False))
    g.add_node("emit_rejection", emit_rejection)

    g.add_edge(START, "validate_input")
    g.add_edge("validate_input", "load_rite_context")
    g.add_edge("load_rite_context", "verify_debtor_sbt")
    g.add_edge("verify_debtor_sbt", "cross_check_creditor_enrollments")
    g.add_edge("cross_check_creditor_enrollments", "run_eligibility_dmn")

    def post_dmn_router(state):
        if not state.get("input_valid"):
            return "emit_rejection"
        if state.get("rite_status") != "active":
            return "emit_rejection"
        if state.get("eligible"):
            return "encrypt_proof"
        # Ineligible: still anchor an enrollment record (transparency) but skip Base L2 anchor to save gas
        return "anchor_enrollment_ineligible"

    g.add_conditional_edges("run_eligibility_dmn", post_dmn_router)
    g.add_edge("encrypt_proof", "anchor_enrollment")
    g.add_edge("anchor_enrollment", END)
    g.add_edge("anchor_enrollment_ineligible", END)
    g.add_edge("emit_rejection", END)

    return g.compile(checkpointer=checkpointer)


# ─── Node functions ──────────────────────────────────────────────────


def validate_input(state):
    valid = bool(state.get("rite_id")) and bool(state.get("debtor_did"))
    return {"input_valid": valid}


def load_rite_context(state, rite_registry_port):
    if rite_registry_port is None:
        return {
            "rite_status": "active",
            "rite_type": "shmita_7yr",
            "rite_effective_date": "2026-05-20T00:00:00Z",
            "rite_jurisdiction_scope": ["ALL"],
        }
    rite = rite_registry_port.get_rite(state["rite_id"])
    return {
        "rite_status": rite.status if rite else "unknown",
        "rite_type": rite.rite_type if rite else "shmita_7yr",
        "rite_effective_date": rite.effective_date if rite else "",
        "rite_jurisdiction_scope": rite.scope_jurisdictions if rite else [],
    }


def verify_debtor_sbt(state, council_sbt_port, charter_compliance_port):
    debtor = state.get("debtor_did", "")
    sbt = council_sbt_port.balance_of_level(debtor) if council_sbt_port else 0
    # Resolve entityType claim from CouncilSBT (default 'unknown' so R14 rejects gracefully)
    sbt_entity_type = (
        council_sbt_port.entity_type_of(debtor)
        if council_sbt_port and hasattr(council_sbt_port, "entity_type_of")
        else "unknown"
    )
    community = (
        debtor.startswith("did:web:etzhayyim.com")
        or (charter_compliance_port and charter_compliance_port.is_aligned(debtor))
    )
    jurisdiction = (
        charter_compliance_port.jurisdiction_of(debtor) if charter_compliance_port else "ALL"
    )
    return {
        "debtor_sbt_level": sbt,
        "debtor_sbt_entity_type": sbt_entity_type,
        "debtor_community_member": community,
        "debtor_jurisdiction_iso3": jurisdiction,
    }


def cross_check_creditor_enrollments(state, creditor_enrollment_port):
    """Find creditor enrollments matching this debtor for the rite. Coerce DebtRow → dict for downstream DMN."""
    if creditor_enrollment_port is None:
        return {"matched_debts": []}
    matched = creditor_enrollment_port.find_debts_for_debtor(
        rite_id=state["rite_id"],
        debtor_did=state["debtor_did"],
    )
    normalized = [
        {
            "debt_id": d.debt_id,
            "debtor_did": d.debtor_did,
            "principal_micro_usdc": d.principal_micro_usdc,
            "accrued_micro_usdc": d.accrued_micro_usdc,
            "origination_date": d.origination_date,
            "instrument": d.instrument,
        }
        if hasattr(d, "debt_id")
        else d
        for d in matched
    ]
    return {"matched_debts": normalized}


def run_eligibility_dmn(state):
    """FIRST-hit DMN per dmn/eligibility-by-rite-type.md. R14+R12+R13 short-circuit."""
    sbt = state.get("debtor_sbt_level", 0)
    sbt_entity_type = state.get("debtor_sbt_entity_type", "unknown")
    declared_entity_type = state.get("debtor_entity_type", "")
    community = state.get("debtor_community_member", False)
    rite_type = state.get("rite_type")
    effective = state.get("rite_effective_date", "")
    scope = state.get("rite_jurisdiction_scope", [])
    jurisdiction = state.get("debtor_jurisdiction_iso3", "")
    in_scope = ("ALL" in scope) or (jurisdiction in scope)
    debts = state.get("matched_debts", [])

    # R14 — global natural-person-only gate (short-circuit; highest priority).
    # yobel releases debt for individuals only (自然人). Legal-person debt is out of scope.
    # Both the declared entity type (from lexicon input) and the resolved CouncilSBT
    # entityType claim MUST be 'natural_person'.
    if declared_entity_type != "natural_person" or sbt_entity_type != "natural_person":
        return {
            "eligible": False,
            "dmn_rule_fired": "R14",
            "dmn_reasons": [
                f"debtor is not a natural person (declared={declared_entity_type or 'unset'}, "
                f"sbt_claim={sbt_entity_type}). yobel releases debt for individuals only; legal-person debt is out of scope."
            ],
        }

    # R12 — global SBT gate (short-circuit)
    if sbt < 1:
        return {
            "eligible": False,
            "dmn_rule_fired": "R12",
            "dmn_reasons": ["no Council SBT — Charter §1.13 SBT-based identity requirement not met"],
        }

    # R13 — global Charter Rider §2(b) prohibited-instrument gate (short-circuit)
    prohibited = [d for d in debts if d.get("instrument") in PROHIBITED_INSTRUMENTS_R13]
    if prohibited:
        return {
            "eligible": False,
            "dmn_rule_fired": "R13",
            "dmn_reasons": [
                "instrument prohibited by Charter Rider §2(b) — yobel is one-way forgiveness only, cannot validate coercive instruments"
            ],
        }

    # Rite-type-specific
    if rite_type == "shmita_7yr":
        if not community:
            return {"eligible": False, "dmn_rule_fired": "R3", "dmn_reasons": ["shmita: not a community member (Deut 15:3)"]}
        pre_cycle = all(d.get("origination_date", "") < effective for d in debts) if debts else True
        if not pre_cycle:
            return {"eligible": False, "dmn_rule_fired": "R2", "dmn_reasons": ["shmita: debt originated after cycle start — not within sabbatical horizon"]}
        # Note: sovereign_bond / corporate_bond can no longer appear here (lexicon enum dropped them + R13/R14 short-circuit upstream)
        return {"eligible": True, "dmn_rule_fired": "R1", "dmn_reasons": ["shmita: community member + pre-cycle debt"]}

    if rite_type == "yobel_50yr":
        if not community:
            return {"eligible": False, "dmn_rule_fired": "R5", "dmn_reasons": ["yobel: community membership required"]}
        if all(d.get("origination_date", "") < effective for d in debts) if debts else True:
            return {"eligible": True, "dmn_rule_fired": "R4", "dmn_reasons": ["yobel: full Jubilee release — debt + bondage + land tenure (Lev 25:10)"]}
        return {"eligible": False, "dmn_rule_fired": "R5", "dmn_reasons": ["yobel: post-cycle debt out of scope"]}

    if rite_type == "tokusei_rei":
        if not in_scope:
            return {"eligible": False, "dmn_rule_fired": "R7", "dmn_reasons": ["tokusei: outside declared jurisdiction scope"]}
        # sovereign_bond / corporate_bond filter removed — lexicon enum already excludes them
        return {"eligible": True, "dmn_rule_fired": "R6", "dmn_reasons": ["tokusei: jurisdiction match (natural-person debt only per ADR-2605201800)"]}

    if rite_type == "religious_jubilee":
        if not community:
            return {"eligible": False, "dmn_rule_fired": "R9", "dmn_reasons": ["Catholic Holy Year: community membership required"]}
        spiritual = all(d.get("instrument") in ("tithe_obligation", "other") for d in debts) if debts else True
        if spiritual:
            return {"eligible": True, "dmn_rule_fired": "R8", "dmn_reasons": ["Catholic Holy Year: indulgentia plenaria for tithe / spiritual debt"]}
        return {"eligible": False, "dmn_rule_fired": "R9", "dmn_reasons": ["Catholic Holy Year: applies to spiritual / tithe debt only — monetary debt out of scope"]}

    if rite_type == "political_amnesty":
        if not in_scope:
            return {"eligible": False, "dmn_rule_fired": "R11", "dmn_reasons": [
                "political amnesty: outside declared sovereign scope. Note: yobel political_amnesty handles MASS AMNESTY FOR INDIVIDUAL DEBTORS only — sovereign/corporate debt restructuring is out of scope (ADR-2605201800)"
            ]}
        return {"eligible": True, "dmn_rule_fired": "R10", "dmn_reasons": [
            "political amnesty: sovereign decree referenced + jurisdiction match (mass amnesty for natural-person debtors — e.g. tax delinquency pardon)"
        ]}

    return {"eligible": False, "dmn_rule_fired": "fallthrough", "dmn_reasons": [f"unknown riteType: {rite_type}"]}


def encrypt_proof(state, envelope_crypto):
    if envelope_crypto is None:
        return {"encrypted_proof_cid": "ipfs://stub-proof"}
    if not state.get("eligibility_proof"):
        return {"encrypted_proof_cid": ""}
    cipher = envelope_crypto.envelope(
        plaintext=state["eligibility_proof"],
        recipients=[state["debtor_did"]],
        purpose="yobel.debtor_enrollment.proof",
    )
    return {"encrypted_proof_cid": cipher.cid}


def anchor_enrollment(state, anchor_bridge, anchor: bool):
    enrollment_id = f"{state['rite_id']}-debt-{state['debtor_did'].split(':')[-1][:8]}"
    pairing = "paired" if state.get("matched_debts") else "unpaired"
    if anchor_bridge is None:
        return {
            "enrollment_id": enrollment_id,
            "pairing_status": pairing,
            "enrollment_vertex_uri": f"at://{state['debtor_did']}/com.etzhayyim.apps.etzhayyim.yobel.debtorEnrollment/{enrollment_id}",
        }
    result = anchor_bridge.write_and_anchor(
        collection="com.etzhayyim.apps.etzhayyim.yobel.debtorEnrollment",
        rkey=enrollment_id,
        payload={
            "rite_id": state["rite_id"],
            "debtor_did": state["debtor_did"],
            "eligible": state.get("eligible", False),
            "dmn_rule_fired": state.get("dmn_rule_fired", ""),
            "dmn_reasons": state.get("dmn_reasons", []),
            "encrypted_proof_cid": state.get("encrypted_proof_cid", ""),
            "pairing_status": pairing,
            "matched_debts_count": len(state.get("matched_debts", [])),
        },
        anchor_to_base_l2=anchor,
    )
    return {
        "enrollment_id": enrollment_id,
        "pairing_status": pairing,
        "enrollment_vertex_uri": result.vertex_uri,
    }


def emit_rejection(state):
    return {"enrollment_id": "", "pairing_status": "unpaired", "enrollment_vertex_uri": ""}
