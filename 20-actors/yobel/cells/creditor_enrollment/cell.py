"""
CreditorEnrollmentCell — Pregel cell verifying creditor opt-in + historical-record-only invariant.

Per ADR-2605201800 §Decision + Charter Rider v2 §2(b) one-way enforcement.

Trigger: enrollCreditor XRPC request scoped to a `status=active` rite
Effect:
  - Validate input (debts[] cardinality, originationDate)
  - Verify creditor Council standing (SBT Lv1+ or non-aligned with warning)
  - Recover EIP-712 signedConsent → assert signer matches creditorDid ERC725 keystore
  - Historical-record-only gate: all debts[].originationDate < rite.effectiveDate
  - Instrument safety gate: reject liquidation / margin_call / seizure
  - XChaCha20-Poly1305-envelope sensitive fields (debts[].principalMicroUsdc, debtorDid)
  - Anchor creditorEnrollment MST record

Murakumo node: gad (good fortune / treasury — Gen 49:19).
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver


Instrument = Literal[
    "loan",
    "promissory_note",
    "mortgage",
    "trade_receivable",
    "tax_obligation",
    "tithe_obligation",
    "other",
]

# Both lists are schema-excluded too; cell-level set is defense-in-depth.
PROHIBITED_INSTRUMENTS = frozenset({"margin_call", "liquidation", "seizure"})
# Legal-person-only debt classes (yobel is natural-person-only — see ADR-2605201800).
LEGAL_PERSON_ONLY_INSTRUMENTS = frozenset({"sovereign_bond", "corporate_bond"})


class DebtItem(TypedDict, total=False):
    debt_id: str
    debtor_did: str
    principal_micro_usdc: int
    accrued_micro_usdc: int
    origination_date: str  # ISO-8601
    instrument: Instrument


class CreditorEnrollmentState(TypedDict, total=False):
    # Input — from enrollCreditor lexicon
    rite_id: str
    creditor_did: str
    debts: list[DebtItem]
    signed_consent: str  # EIP-712 hex signature or DPoP JWT

    # Loaded rite context
    rite_status: str
    rite_effective_date: str

    # Validation results
    input_valid: bool
    input_errors: list[str]
    creditor_sbt_level: int
    creditor_aligned: bool  # SBT Lv1+ OR partner-religious-corp
    consent_signature_valid: bool
    historical_record_compliant: bool
    historical_record_violations: list[str]
    instrument_safety_compliant: bool
    instrument_violations: list[str]

    # Outputs
    enrollment_id: str
    encrypted_debts_cid: str
    enrollment_vertex_uri: str
    debt_count: int


def build_graph(
    checkpointer: BaseCheckpointSaver,
    rite_registry_port,
    council_sbt_port,
    charter_compliance_port,
    erc725_port,
    envelope_crypto,
    anchor_bridge,
):
    g = StateGraph(CreditorEnrollmentState)

    g.add_node("validate_input", validate_input)
    g.add_node("load_rite_context", lambda s: load_rite_context(s, rite_registry_port))
    g.add_node("verify_creditor_standing", lambda s: verify_creditor_standing(s, council_sbt_port, charter_compliance_port))
    g.add_node("verify_signed_consent", lambda s: verify_signed_consent(s, erc725_port))
    g.add_node("historical_record_gate", historical_record_gate)
    g.add_node("instrument_safety_gate", instrument_safety_gate)
    g.add_node("encrypt_sensitive", lambda s: encrypt_sensitive(s, envelope_crypto))
    g.add_node("anchor_enrollment", lambda s: anchor_enrollment(s, anchor_bridge))
    g.add_node("emit_rejection", emit_rejection)

    g.add_edge(START, "validate_input")
    g.add_edge("validate_input", "load_rite_context")
    g.add_edge("load_rite_context", "verify_creditor_standing")
    g.add_edge("verify_creditor_standing", "verify_signed_consent")
    g.add_edge("verify_signed_consent", "historical_record_gate")
    g.add_edge("historical_record_gate", "instrument_safety_gate")

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

    g.add_conditional_edges("instrument_safety_gate", gate_router)
    g.add_edge("encrypt_sensitive", "anchor_enrollment")
    g.add_edge("anchor_enrollment", END)
    g.add_edge("emit_rejection", END)

    return g.compile(checkpointer=checkpointer)


# ─── Node functions ──────────────────────────────────────────────────


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


def load_rite_context(state, rite_registry_port):
    if rite_registry_port is None:
        return {"rite_status": "active", "rite_effective_date": "2026-05-20T00:00:00Z"}
    rite = rite_registry_port.get_rite(state["rite_id"])
    return {
        "rite_status": rite.status if rite else "unknown",
        "rite_effective_date": rite.effective_date if rite else "",
    }


def verify_creditor_standing(state, council_sbt_port, charter_compliance_port):
    creditor = state.get("creditor_did", "")
    sbt = council_sbt_port.balance_of_level(creditor) if council_sbt_port else 0
    aligned = (
        sbt >= 1
        or (charter_compliance_port and charter_compliance_port.is_aligned(creditor))
    )
    return {"creditor_sbt_level": sbt, "creditor_aligned": aligned}


def verify_signed_consent(state, erc725_port):
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


def encrypt_sensitive(state, envelope_crypto):
    """XChaCha20-Poly1305-envelope debts[].principalMicroUsdc + debts[].debtorDid (ADR-2605181100)."""
    if envelope_crypto is None:
        return {"encrypted_debts_cid": "ipfs://stub-cipher"}
    cipher = envelope_crypto.envelope(
        plaintext=state["debts"],
        recipients=[
            state["creditor_did"],
            # Council Lv6+ × 3 + asher (release_settlement leader) added by envelope_crypto.add_council_recipients()
        ],
        purpose="yobel.creditor_enrollment",
    )
    return {"encrypted_debts_cid": cipher.cid}


def anchor_enrollment(state, anchor_bridge):
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
