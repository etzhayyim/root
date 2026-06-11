"""
ConstructionOrchestrationCell — Phase 3 of kuni-umi 4-phase deployment workflow.

Per ADR-2605201400 §3 + ADR-2605202200 (cell.py contract).

Trigger:    MST listener on `com.etzhayyim.apps.etzhayyim.kuniUmi.proposeDeploymentPlan`
            (accepted=true, decision=accept)
Effect:     Dispatch Giemon fleet via open-robo → drive Pregel super-step (1
            cell = 1 Giemon unit) → stream `recordConstructionProgress` at
            1–10 Hz → witness verify at each super-step → on completion emit
            handoff blob.
Murakumo:   joseph (leader)

CRITICAL invariants:
  - cadence_hz_max = 10 (hard-RT motion stays in Giemon firmware)
  - witness N >= 2 per super-step (constitutional, ADR-2605201400 §9)
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)


class ConstructionOrchestrationState(TypedDict, total=False):
    # Input (from proposeDeploymentPlan)
    planDid: str
    siteDid: str
    fleetDid: str
    fleetAllocation: dict[str, Any]

    # Construction progress
    superStepIndex: int
    currentCellId: str
    phase: Literal["queued", "in-progress", "complete", "halted", "handoff-ready"]
    completionPct: float
    sensorBlobCids: list[str]
    anomalyFlags: list[str]
    witnessAttestations: list[dict[str, Any]]

    # Outputs
    progressDids: list[str]  # accumulated recordConstructionProgress DIDs
    handoffBlob: dict[str, Any] | None
    finalized: bool

    # Audit
    _event_uri: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def dispatch_fleet(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """open_robo.fleet.dispatch(fleetDid, taskCid) — IPFS-pinned construction plan."""
    raise NotImplementedError(
        "Requires kotodama.open_robo.fleet.dispatch — not yet implemented."
    )


def super_step_loop(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """Drive Pregel super-step iteration: 1 construction cell = 1 Pregel node.

    CRITICAL: cadence ≤ 10 Hz (deps.config.cadence_hz_max enforced).
    Hard-RT motion is owned by Giemon firmware, not this loop.
    """
    raise NotImplementedError(
        "Requires open-robo BSP super-step driver + cadence enforcement; per ADR-2605151200 §6 "
        "and ADR-2605201400 §3 Phase 3."
    )


def stream_progress(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """Emit `recordConstructionProgress` MST record (1-10 Hz checkpointer cadence)."""
    raise NotImplementedError(
        "Requires deps.sdk for MST write of "
        "com.etzhayyim.apps.etzhayyim.kuniUmi.recordConstructionProgress + witness attestation field."
    )


def witness_verify(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """At each super-step boundary, collect N >= 2 robot signatures.

    Mismatch → emit recordPhysicalAuditEvent class=anomaly subtype=witness-mismatch +
    auto-halt + Council Lv6+ escalation.
    """
    raise NotImplementedError(
        "Requires AuditWitnessCell coordination (sibling cell on levi). "
        "Constitutional invariant: N >= 2 mandatory per super-step boundary."
    )


def handler_anomaly(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """Handle sensor/actuator anomaly → encrypted recordPhysicalAuditEvent → halt or resume."""
    raise NotImplementedError(
        "Requires deps.sdk for XChaCha20-Poly1305 envelope (ADR-2605181100) + Council notification."
    )


def complete_handoff(state: ConstructionOrchestrationState, deps: CellDeps) -> ConstructionOrchestrationState:
    """Prepare handover blob (control verbs + calibration data + as-built CIM updates).

    Emits terminal recordConstructionProgress with phase='handoff-ready' → triggers
    CommissioningCell on simeon.
    """
    raise NotImplementedError(
        "Requires as-built CIM record update via open-* utility lexicons + handoff blob CID pin."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    # Enforce cadence_hz_max constitutional invariant on graph instantiation
    cadence_hz_max = deps.config.get("cadence_hz_max", 10)
    if cadence_hz_max > 10:
        raise ValueError(
            f"ConstructionOrchestrationCell cadence_hz_max={cadence_hz_max} exceeds constitutional limit 10 "
            f"(per ADR-2605201400 §3 Phase 3 + ADR-2605202200). Hard-RT motion must stay in Giemon firmware."
        )

    g = StateGraph(ConstructionOrchestrationState)

    g.add_node("dispatch_fleet", lambda s: dispatch_fleet(s, deps))
    g.add_node("super_step_loop", lambda s: super_step_loop(s, deps))
    g.add_node("stream_progress", lambda s: stream_progress(s, deps))
    g.add_node("witness_verify", lambda s: witness_verify(s, deps))
    g.add_node("handler_anomaly", lambda s: handler_anomaly(s, deps))
    g.add_node("complete_handoff", lambda s: complete_handoff(s, deps))

    g.add_edge(START, "dispatch_fleet")
    g.add_edge("dispatch_fleet", "super_step_loop")
    g.add_edge("super_step_loop", "stream_progress")
    g.add_edge("stream_progress", "witness_verify")

    def witness_router(state: ConstructionOrchestrationState) -> str:
        attestations = state.get("witnessAttestations", [])
        if len(attestations) < 2:
            # Constitutional invariant violated — escalate
            return "handler_anomaly"
        if state.get("anomalyFlags"):
            return "handler_anomaly"
        if state.get("phase") == "handoff-ready":
            return "complete_handoff"
        return "super_step_loop"  # next super-step

    g.add_conditional_edges("witness_verify", witness_router)
    g.add_edge("handler_anomaly", END)  # halt; resume requires Council deliberation
    g.add_edge("complete_handoff", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    """One thread per plan — super-step iteration accumulates in same checkpointer thread."""
    value = event_record.get("value", {})
    plan_did = value.get("planDid") or event_record.get("rkey", "unknown")
    return f"ConstructionOrchestrationCell:{plan_did}"


def healthz_extra(deps: CellDeps) -> dict:
    return {
        "phase": "3-construction",
        "trigger_nsid": "com.etzhayyim.apps.etzhayyim.kuniUmi.proposeDeploymentPlan",
        "cadence_hz_max": deps.config.get("cadence_hz_max", 10),
        "witness_invariant_min": 2,
        "hard_rt_owner": "Giemon firmware (open-robo + open-ot field tier WAMR)",
    }
