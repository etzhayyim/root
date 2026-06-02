"""RiteDeclarationCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any, Literal
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Constants & Mocks ---

RiteType = Literal[
    "shmita_7yr",
    "yobel_50yr",
    "tokusei_rei",
    "religious_jubilee",
    "political_amnesty",
]

RiteStatus = Literal["declared", "active", "completed", "cancelled", "superseded"]

# --- Node functions ---

def validate_input(state: dict[str, Any]) -> dict[str, Any]:
    errors = []
    rite_type = state.get("rite_type")
    if rite_type not in (
        "shmita_7yr", "yobel_50yr", "tokusei_rei", "religious_jubilee", "political_amnesty",
    ):
        errors.append(f"invalid riteType: {rite_type}")

    doctrinal_basis = state.get("doctrinal_basis", "")
    if not doctrinal_basis or len(doctrinal_basis) > 1000:
        errors.append("doctrinalBasis required, max 1000 chars")

    scope = state.get("scope", "")
    if not scope or len(scope) > 2000:
        errors.append("scope required, max 2000 chars")

    if not state.get("effective_date"):
        errors.append("effectiveDate required")

    if rite_type == "political_amnesty" and not doctrinal_basis.strip():
        errors.append("political_amnesty requires sovereign decree reference in doctrinalBasis")

    return {"input_valid": len(errors) == 0, "input_errors": errors}


def verify_issuer_standing(state: dict[str, Any]) -> dict[str, Any]:
    """Issuer must be SBT Lv1+ or in the Charter Compliance Registry. (Mocked)"""
    # Mocking port logic
    sbt_level = 0
    in_registry = False
    return {"issuer_sbt_level": sbt_level, "issuer_in_charter_registry": in_registry}


def charter_rider_gate(state: dict[str, Any]) -> dict[str, Any]:
    """Scope text scan + DMN to enforce Charter Rider §2(a-h) prohibitions."""
    violations = []
    scope = state.get("scope", "").lower()
    # §2(a) military
    if any(kw in scope for kw in ("military debt", "defense contractor debt", "arms procurement debt")):
        if "transparent-force-rd" not in scope:
            violations.append("§2(a) military scope requires transparent-force-rd disclosure (ADR-2605192315)")
    # §2(b) speculative finance
    if any(kw in scope for kw in ("margin", "leverage", "arbitrage", "predatory")):
        violations.append("§2(b) speculative finance keywords in scope — yobel is one-way forgiveness only")

    return {
        "charter_rider_compliant": len(violations) == 0,
        "charter_rider_violations": violations,
    }


def council_ratification_dmn(state: dict[str, Any]) -> dict[str, Any]:
    """COLLECT-hit DMN per dmn/council-ratification-threshold.md."""
    lv6 = 3
    lv9 = 1
    quorum = 50
    gates: list[str] = []

    rite_type = state.get("rite_type")
    if rite_type == "yobel_50yr":
        lv6 += 2
        quorum += 10
        gates.append("land-sovereignty-coordination")
    elif rite_type == "tokusei_rei":
        lv6 += 1
        lv9 += 1
        quorum += 10
        gates.append("jurisdiction-claim-coordination")
    elif rite_type == "religious_jubilee":
        gates.append("partner-religious-corp-notification")
    elif rite_type == "political_amnesty":
        lv6 += 3
        lv9 += 1
        quorum += 20
        gates.extend(["transparent-force-rd-disclosure", "council-five-bootstrap-consultation"])

    return {
        "required_lv6_plus_count": lv6,
        "required_lv9_chair_count": lv9,
        "required_quorum_pct": min(quorum, 100),
        "additional_gates": gates,
    }


def submit_council_proposal(state: dict[str, Any]) -> dict[str, Any]:
    """Emit governance proposal MST record; returns proposal URI. (Mocked)"""
    # council_ratification_port is None
    return {"council_proposal_uri": f"at://stub/{state.get('rite_id', 'unknown')}/proposal"}


def await_council_decision(state: dict[str, Any]) -> dict[str, Any]:
    """Block on Council deliberation. (Mocked)"""
    # council_ratification_port is None
    return {"council_ratified": False, "council_ratification_signatures": []}


def land_sovereignty_coordination(state: dict[str, Any]) -> dict[str, Any]:
    """yobel_50yr: identify land tenure records auto-reverting. (Mocked)"""
    # land_registry_port is None
    return {"overlapping_land_ids": [], "land_coordination_complete": True}


def anchor_rite(state: dict[str, Any]) -> dict[str, Any]:
    """Write rite MST record. (Mocked)"""
    # anchor_bridge is None
    return {
        "rite_status": "active",
        "rite_vertex_uri": f"at://did:web:yobel.etzhayyim.com/com.etzhayyim.apps.etzhayyim.yobel.rite/{state.get('rite_id', 'unknown')}",
        "base_l2_anchor_tx_hash": "",
    }


def emit_cancellation(state: dict[str, Any]) -> dict[str, Any]:
    """Mark rite as cancelled."""
    return {
        "rite_status": "cancelled",
        "rite_vertex_uri": f"at://stub/{state.get('rite_id', 'unknown')}/cancelled",
    }

# --- Router Functions ---

def gate_router(state: dict[str, Any]) -> str:
    if not state.get("input_valid"):
        return "emit_cancellation"
    if state.get("issuer_sbt_level", 0) < 1 and not state.get("issuer_in_charter_registry"):
        return "emit_cancellation"
    if not state.get("charter_rider_compliant"):
        return "emit_cancellation"
    return "council_ratification_dmn"

def council_router(state: dict[str, Any]) -> str:
    if not state.get("council_ratified"):
        return "emit_cancellation"
    if state.get("rite_type") == "yobel_50yr":
        return "land_sovereignty_coordination"
    return "anchor_rite"

# --- Graph Construction ---

_g = StateGraph(dict)

_g.add_node("validate_input", validate_input)
_g.add_node("verify_issuer_standing", verify_issuer_standing)
_g.add_node("charter_rider_gate", charter_rider_gate)
_g.add_node("council_ratification_dmn", council_ratification_dmn)
_g.add_node("submit_council_proposal", submit_council_proposal)
_g.add_node("await_council_decision", await_council_decision)
_g.add_node("land_sovereignty_coordination", land_sovereignty_coordination)
_g.add_node("anchor_rite", anchor_rite)
_g.add_node("emit_cancellation", emit_cancellation)

_g.add_edge(START, "validate_input")
_g.add_edge("validate_input", "verify_issuer_standing")
_g.add_edge("verify_issuer_standing", "charter_rider_gate")

_g.add_conditional_edges("charter_rider_gate", gate_router)

_g.add_edge("council_ratification_dmn", "submit_council_proposal")
_g.add_edge("submit_council_proposal", "await_council_decision")

_g.add_conditional_edges("await_council_decision", council_router)

_g.add_edge("land_sovereignty_coordination", "anchor_rite")
_g.add_edge("anchor_rite", END)
_g.add_edge("emit_cancellation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
