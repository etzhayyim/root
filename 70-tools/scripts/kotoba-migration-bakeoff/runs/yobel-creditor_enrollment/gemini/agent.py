from __future__ import annotations
from typing import Any, Literal
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Constants & Mocks ---
PROHIBITED_INSTRUMENTS = frozenset({"margin_call", "liquidation", "seizure"})
LEGAL_PERSON_ONLY_INSTRUMENTS = frozenset({"sovereign_bond", "corporate_bond"})

# Ports mocked as None to follow original fallback logic
rite_registry_port = None
council_sbt_port = None
charter_compliance_port = None
erc725_port = None
envelope_crypto = None
anchor_bridge = None

# --- Node functions ---

def validate_input(state):
    errors: list[str] = []
    debts = state.get("debts", [])
    if not debts:
        errors.append("debts[] must have ≥ 1 entry")
    if len(debts) > 1000:
        errors.append("debts[] capped at 1000 entries per enrollment call")
    if not state.get("creditor_did"):
        errors.append("creditorDid required")
    if not state.get("signed_consent"):
        errors.append("signedConsent required")
    for i, d in enumerate(debts):
        if d.get("principal_micro_usdc", -1) < 0:
            errors.append(f"debts[{i}].principalMicroUsdc must be ≥ 0")
        if not d.get("origination_date"):
            errors.append(f"debts[{i}].originationDate required")
    return {"input_valid": len(errors) == 0, "input_errors": errors}


def load_rite_context(state):
    if rite_registry_port is None:
        return {"rite_status": "active", "rite_effective_date": "2026-05-20T00:00:00Z"}
    rite = rite_registry_port.get_rite(state["rite_id"])
    return {
        "rite_status": rite.status if rite else "unknown",
        "rite_effective_date": rite.effective_date if rite else "",
    }


def verify_creditor_standing(state):
    creditor = state.get("creditor_did", "")
    sbt = council_sbt_port.balance_of_level(creditor) if council_sbt_port else 0
    aligned = (
        sbt >= 1
        or (charter_compliance_port and charter_compliance_port.is_aligned(creditor))
    )
    return {"creditor_sbt_level": sbt, "creditor_aligned": aligned}


def verify_signed_consent(state):
    """ERC725 EIP-712 signature recover; assert signer == creditorDid keystore."""
    if erc725_port is None:
        return {"consent_signature_valid": False}
    valid = erc725_port.verify_eip712_signed_consent(
        signer_did=state["creditor_did"],
        payload={
            "rite_id": state["rite_id"],
            "creditor_did": state["creditor_did"],
            "debts": state["debts"],
        },
        signature=state["signed_consent"],
    )
    return {"consent_signature_valid": bool(valid)}


def historical_record_gate(state):
    """All debts[].originationDate must be < rite.effectiveDate (Charter Rider §2(b) one-way)."""
    violations: list[str] = []
    effective = state.get("rite_effective_date", "")
    for i, d in enumerate(state.get("debts", [])):
        if d.get("origination_date", "") >= effective:
            violations.append(
                f"debts[{i}]: originationDate {d.get('origination_date')} >= rite.effectiveDate {effective} — new debt origination not allowed"
            )
    return {
        "historical_record_compliant": len(violations) == 0,
        "historical_record_violations": violations,
    }


def instrument_safety_gate(state):
    """Reject (a) Charter Rider §2(b) prohibited instruments and (b) legal-person-only
    instruments (yobel is natural-person-only — see ADR-2605201800). Defense in depth,
    lexicon already excludes both classes from its enum."""
    violations: list[str] = []
    for i, d in enumerate(state.get("debts", [])):
        inst = d.get("instrument", "")
        if inst in PROHIBITED_INSTRUMENTS:
            violations.append(f"debts[{i}].instrument={inst} prohibited by Charter Rider §2(b)")
        if inst in LEGAL_PERSON_ONLY_INSTRUMENTS:
            violations.append(
                f"debts[{i}].instrument={inst} is a legal-person-only instrument; "
                "yobel is natural-person-only (ADR-2605201800)"
            )
    return {
        "instrument_safety_compliant": len(violations) == 0,
        "instrument_violations": violations,
    }


def encrypt_sensitive(state):
    """XChaCha20-Poly1305-envelope debts[].principalMicroUsdc + debts[].debtorDid (ADR-2605181100)."""
    if envelope_crypto is None:
        return {"encrypted_debts_cid": "ipfs://stub-cipher"}
    cipher = envelope_crypto.envelope(
        plaintext=state["debts"],
        recipients=[
            state["creditor_did"],
        ],
        purpose="yobel.creditor_enrollment",
    )
    return {"encrypted_debts_cid": cipher.cid}


def anchor_enrollment(state):
    enrollment_id = f"{state['rite_id']}-cred-{state['creditor_did'].split(':')[-1][:8]}"
    if anchor_bridge is None:
        return {
            "enrollment_id": enrollment_id,
            "debt_count": len(state.get("debts", [])),
            "enrollment_vertex_uri": f"at://{state['creditor_did']}/com.etzhayyim.apps.etzhayyim.yobel.creditorEnrollment/{enrollment_id}",
        }
    result = anchor_bridge.write_and_anchor(
        collection="com.etzhayyim.apps.etzhayyim.yobel.creditorEnrollment",
        rkey=enrollment_id,
        payload={
            "rite_id": state["rite_id"],
            "creditor_did": state["creditor_did"],
            "encrypted_debts_cid": state["encrypted_debts_cid"],
            "debt_count": len(state.get("debts", [])),
            "signed_consent_digest": state["signed_consent"][:32],
        },
    )
    return {
        "enrollment_id": enrollment_id,
        "debt_count": len(state.get("debts", [])),
        "enrollment_vertex_uri": result.vertex_uri,
    }


def emit_rejection(state):
    return {
        "enrollment_id": "",
        "debt_count": 0,
        "enrollment_vertex_uri": "",
    }

def gate_router(state):
    if not state.get("input_valid"):
        return "emit_rejection"
    if state.get("rite_status") != "active":
        return "emit_rejection"
    if not state.get("consent_signature_valid"):
        return "emit_rejection"
    if not state.get("historical_record_compliant"):
        return "emit_rejection"
    if not state.get("instrument_safety_compliant"):
        return "emit_rejection"
    return "encrypt_sensitive"

# --- Graph construction ---

_g = StateGraph(dict)

_g.add_node("validate_input", validate_input)
_g.add_node("load_rite_context", load_rite_context)
_g.add_node("verify_creditor_standing", verify_creditor_standing)
_g.add_node("verify_signed_consent", verify_signed_consent)
_g.add_node("historical_record_gate", historical_record_gate)
_g.add_node("instrument_safety_gate", instrument_safety_gate)
_g.add_node("encrypt_sensitive", encrypt_sensitive)
_g.add_node("anchor_enrollment", anchor_enrollment)
_g.add_node("emit_rejection", emit_rejection)

_g.add_edge(START, "validate_input")
_g.add_edge("validate_input", "load_rite_context")
_g.add_edge("load_rite_context", "verify_creditor_standing")
_g.add_edge("verify_creditor_standing", "verify_signed_consent")
_g.add_edge("verify_signed_consent", "historical_record_gate")
_g.add_edge("historical_record_gate", "instrument_safety_gate")

_g.add_conditional_edges("instrument_safety_gate", gate_router)
_g.add_edge("encrypt_sensitive", "anchor_enrollment")
_g.add_edge("anchor_enrollment", END)
_g.add_edge("emit_rejection", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
