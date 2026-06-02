from __future__ import annotations
from typing import Literal, Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Constants & Types ---
RiteType = Literal[
    "shmita_7yr",
    "yobel_50yr",
    "tokusei_rei",
    "religious_jubilee",
    "political_amnesty",
]

PROHIBITED_INSTRUMENTS_R13 = frozenset({"liquidation", "margin_call", "seizure"})

# --- Node functions ---

def validate_input(state: dict) -> dict:
    valid = bool(state.get("rite_id")) and bool(state.get("debtor_did"))
    return {"input_valid": valid}

def load_rite_context(state: dict) -> dict:
    # Port logic: if rite_registry_port is None, return these defaults from original
    return {
        "rite_status": "active",
        "rite_type": "shmita_7yr",
        "rite_effective_date": "2026-05-20T00:00:00Z",
        "rite_jurisdiction_scope": ["ALL"],
    }

def verify_debtor_sbt(state: dict) -> dict:
    # Port logic: if council_sbt_port / charter_compliance_port are None
    debtor = state.get("debtor_did", "")
    sbt = 0
    sbt_entity_type = "unknown"
    community = debtor.startswith("did:web:etzhayyim.com")
    jurisdiction = "ALL"
    return {
        "debtor_sbt_level": sbt,
        "debtor_sbt_entity_type": sbt_entity_type,
        "debtor_community_member": community,
        "debtor_jurisdiction_iso3": jurisdiction,
    }

def cross_check_creditor_enrollments(state: dict) -> dict:
    # Port logic: if creditor_enrollment_port is None
    return {"matched_debts": []}

def run_eligibility_dmn(state: dict) -> dict:
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

    # R14 short-circuit
    if declared_entity_type != "natural_person" or sbt_entity_type != "natural_person":
        return {
            "eligible": False,
            "dmn_rule_fired": "R14",
            "dmn_reasons": [
                f"debtor is not a natural person (declared={declared_entity_type or 'unset'}, "
                f"sbt_claim={sbt_entity_type}). yobel releases debt for individuals only; legal-person debt is out of scope."
            ],
        }

    # R12 short-circuit
    if sbt < 1:
        return {
            "eligible": False,
            "dmn_rule_fired": "R12",
            "dmn_reasons": ["no Council SBT — Charter §1.13 SBT-based identity requirement not met"],
        }

    # R13 short-circuit
    prohibited = [d for d in debts if d.get("instrument") in PROHIBITED_INSTRUMENTS_R13]
    if prohibited:
        return {
            "eligible": False,
            "dmn_rule_fired": "R13",
            "dmn_reasons": [
                "instrument prohibited by Charter Rider §2(b) — yobel is one-way forgiveness only, cannot validate coercive instruments"
            ],
        }

    # Rite-type-specific logic
    if rite_type == "shmita_7yr":
        if not community:
            return {"eligible": False, "dmn_rule_fired": "R3", "dmn_reasons": ["shmita: not a community member (Deut 15:3)"]}
        pre_cycle = all(d.get("origination_date", "") < effective for d in debts) if debts else True
        if not pre_cycle:
            return {"eligible": False, "dmn_rule_fired": "R2", "dmn_reasons": ["shmita: debt originated after cycle start — not within sabbatical horizon"]}
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

def encrypt_proof(state: dict) -> dict:
    if not state.get("eligibility_proof"):
        return {"encrypted_proof_cid": ""}
    return {"encrypted_proof_cid": "ipfs://stub-proof"}

def anchor_enrollment(state: dict) -> dict:
    """Mock of anchor_bridge.write_and_anchor with anchor=True."""
    enrollment_id = f"{state['rite_id']}-debt-{state['debtor_did'].split(':')[-1][:8]}"
    pairing = "paired" if state.get("matched_debts") else "unpaired"
    return {
        "enrollment_id": enrollment_id,
        "pairing_status": pairing,
        "enrollment_vertex_uri": f"at://{state['debtor_did']}/com.etzhayyim.apps.etzhayyim.yobel.debtorEnrollment/{enrollment_id}",
    }

def anchor_enrollment_ineligible(state: dict) -> dict:
    """Mock of anchor_bridge.write_and_anchor with anchor=False."""
    enrollment_id = f"{state['rite_id']}-debt-{state['debtor_did'].split(':')[-1][:8]}"
    pairing = "paired" if state.get("matched_debts") else "unpaired"
    return {
        "enrollment_id": enrollment_id,
        "pairing_status": pairing,
        "enrollment_vertex_uri": f"at://{state['debtor_did']}/com.etzhayyim.apps.etzhayyim.yobel.debtorEnrollment/{enrollment_id}",
    }

def emit_rejection(state: dict) -> dict:
    return {"enrollment_id": "", "pairing_status": "unpaired", "enrollment_vertex_uri": ""}

def post_dmn_router(state: dict) -> str:
    if not state.get("input_valid"):
        return "emit_rejection"
    if state.get("rite_status") != "active":
        return "emit_rejection"
    if state.get("eligible"):
        return "encrypt_proof"
    return "anchor_enrollment_ineligible"

# --- Graph Construction ---
_g = StateGraph(dict)

_g.add_node("validate_input", validate_input)
_g.add_node("load_rite_context", load_rite_context)
_g.add_node("verify_debtor_sbt", verify_debtor_sbt)
_g.add_node("cross_check_creditor_enrollments", cross_check_creditor_enrollments)
_g.add_node("run_eligibility_dmn", run_eligibility_dmn)
_g.add_node("encrypt_proof", encrypt_proof)
_g.add_node("anchor_enrollment", anchor_enrollment)
_g.add_node("anchor_enrollment_ineligible", anchor_enrollment_ineligible)
_g.add_node("emit_rejection", emit_rejection)

_g.add_edge(START, "validate_input")
_g.add_edge("validate_input", "load_rite_context")
_g.add_edge("load_rite_context", "verify_debtor_sbt")
_g.add_edge("verify_debtor_sbt", "cross_check_creditor_enrollments")
_g.add_edge("cross_check_creditor_enrollments", "run_eligibility_dmn")

_g.add_conditional_edges("run_eligibility_dmn", post_dmn_router)
_g.add_edge("encrypt_proof", "anchor_enrollment")
_g.add_edge("anchor_enrollment", END)
_g.add_edge("anchor_enrollment_ineligible", END)
_g.add_edge("emit_rejection", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
