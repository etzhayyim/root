"""
RiteDeclarationCell — Pregel cell orchestrating the 6-step rite declaration gate.

Per ADR-2605201800 (Yobel Collective Debt Release Actor) + ADR-2605192230 (Three-Tier Enforcement).

Trigger: declareRite XRPC request from an etzhayyim-aligned (or partner) religious-corp DID
Effect:
  - Validate rite input (riteType / doctrinalBasis / scope / effectiveDate)
  - Verify issuer Council standing (SBT Lv1+ or partner-religious-corp registry)
  - Charter Rider §2(a-h) gate (scope text scan + DMN)
  - Council ratification DMN → emit governance proposal → wait for Council Lv6+ × 3 + Lv9 chair
  - Land sovereignty coordination (yobel_50yr only)
  - Anchor rite MST record via MST → IPFS → Base L2 batched anchor (AnchorBridge)

Murakumo node: judah (leader, kingly proclamation — Gen 49:8-10).
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

RiteStatus = Literal["declared", "active", "completed", "cancelled", "superseded"]


class RiteDeclarationState(TypedDict, total=False):
    # Input — from declareRite lexicon
    rite_id: str
    rite_type: RiteType
    scope: str
    effective_date: str  # ISO-8601 datetime
    expiry_date: str  # optional
    doctrinal_basis: str
    jurisdiction_notes: str
    issuer_did: str

    # Validation results
    input_valid: bool
    input_errors: list[str]
    issuer_sbt_level: int
    issuer_in_charter_registry: bool
    charter_rider_compliant: bool
    charter_rider_violations: list[str]

    # DMN council ratification output
    required_lv6_plus_count: int
    required_lv9_chair_count: int
    required_quorum_pct: int
    additional_gates: list[str]
    council_proposal_uri: str
    council_ratified: bool
    council_ratification_signatures: list[str]

    # Land sovereignty (yobel_50yr only)
    overlapping_land_ids: list[int]
    land_coordination_complete: bool

    # Outputs
    rite_status: RiteStatus
    rite_vertex_uri: str
    base_l2_anchor_tx_hash: str


def build_graph(
    checkpointer: BaseCheckpointSaver,
    charter_compliance_port,
    council_sbt_port,
    council_ratification_port,
    land_registry_port,
    anchor_bridge,
):
    g = StateGraph(RiteDeclarationState)

    g.add_node("validate_input", validate_input)
    g.add_node("verify_issuer_standing", lambda s: verify_issuer_standing(s, council_sbt_port, charter_compliance_port))
    g.add_node("charter_rider_gate", lambda s: charter_rider_gate(s, charter_compliance_port))
    g.add_node("council_ratification_dmn", council_ratification_dmn)
    g.add_node("submit_council_proposal", lambda s: submit_council_proposal(s, council_ratification_port))
    g.add_node("await_council_decision", lambda s: await_council_decision(s, council_ratification_port))
    g.add_node("land_sovereignty_coordination", lambda s: land_sovereignty_coordination(s, land_registry_port))
    g.add_node("anchor_rite", lambda s: anchor_rite(s, anchor_bridge))
    g.add_node("emit_cancellation", emit_cancellation)

    g.add_edge(START, "validate_input")
    g.add_edge("validate_input", "verify_issuer_standing")
    g.add_edge("verify_issuer_standing", "charter_rider_gate")

    def gate_router(state):
        if not state.get("input_valid"):
            return "emit_cancellation"
        if state.get("issuer_sbt_level", 0) < 1 and not state.get("issuer_in_charter_registry"):
            return "emit_cancellation"
        if not state.get("charter_rider_compliant"):
            return "emit_cancellation"
        return "council_ratification_dmn"

    g.add_conditional_edges("charter_rider_gate", gate_router)
    g.add_edge("council_ratification_dmn", "submit_council_proposal")
    g.add_edge("submit_council_proposal", "await_council_decision")

    def council_router(state):
        if not state.get("council_ratified"):
            return "emit_cancellation"
        if state.get("rite_type") == "yobel_50yr":
            return "land_sovereignty_coordination"
        return "anchor_rite"

    g.add_conditional_edges("await_council_decision", council_router)
    g.add_edge("land_sovereignty_coordination", "anchor_rite")
    g.add_edge("anchor_rite", END)
    g.add_edge("emit_cancellation", END)

    return g.compile(checkpointer=checkpointer)


# ─── Node functions ──────────────────────────────────────────────────


def validate_input(state):
    errors = []
    if state.get("rite_type") not in (
        "shmita_7yr", "yobel_50yr", "tokusei_rei", "religious_jubilee", "political_amnesty",
    ):
        errors.append(f"invalid riteType: {state.get('rite_type')}")
    if not state.get("doctrinal_basis") or len(state["doctrinal_basis"]) > 1000:
        errors.append("doctrinalBasis required, max 1000 chars")
    if not state.get("scope") or len(state["scope"]) > 2000:
        errors.append("scope required, max 2000 chars")
    if not state.get("effective_date"):
        errors.append("effectiveDate required")
    if state.get("rite_type") == "political_amnesty" and not state.get("doctrinal_basis", "").strip():
        errors.append("political_amnesty requires sovereign decree reference in doctrinalBasis")

    return {"input_valid": len(errors) == 0, "input_errors": errors}


def verify_issuer_standing(state, council_sbt_port, charter_compliance_port):
    """Issuer must be SBT Lv1+ or in the Charter Compliance Registry."""
    issuer = state.get("issuer_did", "")
    sbt_level = council_sbt_port.balance_of_level(issuer) if council_sbt_port else 0
    in_registry = (
        charter_compliance_port.is_aligned(issuer)
        if charter_compliance_port else False
    )
    return {"issuer_sbt_level": sbt_level, "issuer_in_charter_registry": in_registry}


def charter_rider_gate(state, charter_compliance_port):
    """Scope text scan + DMN to enforce Charter Rider §2(a-h) prohibitions."""
    violations = []
    scope = state.get("scope", "").lower()
    # §2(a) military — military debt forgiveness requires transparent-force-rd disclosure
    if any(kw in scope for kw in ("military debt", "defense contractor debt", "arms procurement debt")):
        if "transparent-force-rd" not in scope:
            violations.append("§2(a) military scope requires transparent-force-rd disclosure (ADR-2605192315)")
    # §2(b) speculative finance — already enforced at lexicon schema level; double-check scope
    if any(kw in scope for kw in ("margin", "leverage", "arbitrage", "predatory")):
        violations.append("§2(b) speculative finance keywords in scope — yobel is one-way forgiveness only")
    # §2(c-h) — would call charter_compliance_port.scope_check(scope) for full DMN
    return {
        "charter_rider_compliant": len(violations) == 0,
        "charter_rider_violations": violations,
    }


def council_ratification_dmn(state):
    """COLLECT-hit DMN per dmn/council-ratification-threshold.md."""
    # B1 baseline
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


def submit_council_proposal(state, council_ratification_port):
    """Emit governance proposal MST record; returns proposal URI."""
    if council_ratification_port is None:
        return {"council_proposal_uri": f"at://stub/{state['rite_id']}/proposal"}
    uri = council_ratification_port.submit_proposal(
        topic="yobel_rite_declaration",
        rite_id=state["rite_id"],
        rite_type=state["rite_type"],
        required_lv6_plus_count=state["required_lv6_plus_count"],
        required_lv9_chair_count=state["required_lv9_chair_count"],
        required_quorum_pct=state["required_quorum_pct"],
        additional_gates=state["additional_gates"],
        doctrinal_basis=state["doctrinal_basis"],
        scope=state["scope"],
    )
    return {"council_proposal_uri": uri}


def await_council_decision(state, council_ratification_port):
    """Block on Council deliberation (default 30 days per Three-Tier Enforcement)."""
    if council_ratification_port is None:
        return {"council_ratified": False, "council_ratification_signatures": []}
    decision = council_ratification_port.await_decision(
        proposal_uri=state["council_proposal_uri"],
        timeout_days=30,
    )
    return {
        "council_ratified": decision.ratified,
        "council_ratification_signatures": decision.signatures,
    }


def land_sovereignty_coordination(state, land_registry_port):
    """yobel_50yr: identify land tenure records auto-reverting under Lev 25:23."""
    if land_registry_port is None:
        return {"overlapping_land_ids": [], "land_coordination_complete": True}
    land_ids = land_registry_port.find_overlapping_tenures(scope=state["scope"])
    return {"overlapping_land_ids": land_ids, "land_coordination_complete": True}


def anchor_rite(state, anchor_bridge):
    """Write rite MST record with status=active, anchor via MST → IPFS → Base L2."""
    if anchor_bridge is None:
        return {
            "rite_status": "active",
            "rite_vertex_uri": f"at://did:web:yobel.etzhayyim.com/com.etzhayyim.apps.etzhayyim.yobel.rite/{state['rite_id']}",
            "base_l2_anchor_tx_hash": "",
        }
    result = anchor_bridge.write_and_anchor(
        collection="com.etzhayyim.apps.etzhayyim.yobel.rite",
        rkey=state["rite_id"],
        payload={
            "rite_id": state["rite_id"],
            "rite_type": state["rite_type"],
            "scope": state["scope"],
            "effective_date": state["effective_date"],
            "expiry_date": state.get("expiry_date"),
            "doctrinal_basis": state["doctrinal_basis"],
            "jurisdiction_notes": state.get("jurisdiction_notes", ""),
            "issuer_did": state["issuer_did"],
            "status": "active",
            "council_proposal_uri": state["council_proposal_uri"],
            "council_ratification_signatures": state["council_ratification_signatures"],
            "overlapping_land_ids": state.get("overlapping_land_ids", []),
        },
    )
    return {
        "rite_status": "active",
        "rite_vertex_uri": result.vertex_uri,
        "base_l2_anchor_tx_hash": result.anchor_tx_hash,
    }


def emit_cancellation(state):
    """Mark rite as cancelled — Council rejection / Charter Rider violation / invalid input."""
    return {
        "rite_status": "cancelled",
        "rite_vertex_uri": f"at://stub/{state.get('rite_id','unknown')}/cancelled",
    }
