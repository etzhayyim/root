"""
AuditWitnessCell — Continuous robot-witness audit cell.

Per ADR-2605201400 §9 + ADR-2605202200 (cell.py contract).

Religious-corp's self-inspection layer. NOT dependent on state inspectors.
N >= 2 independent Giemon robot signatures attest every super-step boundary
+ every recordPhysicalAuditEvent class event.

Trigger:    continuous + super-step boundary + event-driven
            Listens to: com.etzhayyim.apps.etzhayyim.kuniUmi.recordPhysicalAuditEvent
Effect:     verify N>=2 signatures → on mismatch escalate to Council Lv6+
            → feed Phenotype.effectiveMultiplier delta (ADR-2605192230)
Murakumo:   levi (leader, membership + council orchestration)

CRITICAL invariants:
  - N >= 2 mandatory always. Constitutional.
  - injury / anomaly events trigger Council escalation
  - witness_mismatch → automatic halt of relevant ConstructionOrchestrationCell
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)


EventClass = Literal["anomaly", "intrusion", "injury", "compliance-check", "community-event"]


class AuditWitnessState(TypedDict, total=False):
    # Input
    siteDid: str
    planDid: str | None
    eventClass: EventClass
    subtype: str
    occurredAt: str
    evidenceCid: str
    participantDids: list[str]
    witnessAttestations: list[dict[str, Any]]

    # Verification outputs
    signaturesVerified: int
    blobConsistencyOk: bool
    invariantViolated: bool

    # Escalation
    councilEscalated: bool
    auditDid: str  # final recordPhysicalAuditEvent DID

    # Phenotype feedback (ADR-2605192230)
    phenotypeDeltaTargetDid: str | None
    phenotypeDeltaBps: int  # signed basis points

    # Audit
    _event_uri: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def poll_witnesses(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Fetch latest sensor blob CIDs from N >= 2 independent robots at the site."""
    raise NotImplementedError(
        "Requires kotodama.open_robo.fleet poll endpoint."
    )


def verify_signatures(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Verify each robot's Ed25519 signature over the blob hash.

    Per ADR-2605191657 (did:key challenge-response auth) signing scheme.
    """
    attestations = state.get("witnessAttestations", [])
    state["signaturesVerified"] = len([a for a in attestations if a.get("signature")])
    # TODO: actual Ed25519 verify against did:web public-key resolution
    return state


def compare_blobs(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Robots observe the same physical reality; blob hashes for shared sensor
    channels MUST match within tolerance (sensor noise floor).
    """
    attestations = state.get("witnessAttestations", [])
    # Scaffold: declare consistent if >= 2 attestations carry blobHash
    blob_hashes = [a.get("blobHash") for a in attestations if a.get("blobHash")]
    state["blobConsistencyOk"] = len(set(blob_hashes)) <= 1 if blob_hashes else False
    state["invariantViolated"] = (
        state.get("signaturesVerified", 0) < 2
        or not state.get("blobConsistencyOk", False)
    )
    return state


def attest_record(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Write `recordPhysicalAuditEvent` MST record (encrypted for anomaly/injury,
    public for community-event/compliance-check per ADR-2605181100).
    """
    raise NotImplementedError(
        "Requires deps.sdk for MST write + per-class XChaCha20-Poly1305 envelope routing."
    )


def escalate_mismatch(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Witness mismatch → automatic halt + Council Lv6+ escalation.

    Writes recordPhysicalAuditEvent class=anomaly subtype=witness-mismatch +
    notifies Council via council_deliberation cell.
    """
    state["councilEscalated"] = True
    raise NotImplementedError(
        "Requires council_deliberation cell coordination + ConstructionOrchestrationCell halt signal."
    )


def feedback_phenotype(state: AuditWitnessState, deps: CellDeps) -> AuditWitnessState:
    """Emit Phenotype delta per ADR-2605192230 for injury / community-event events."""
    raise NotImplementedError(
        "Requires deps.geth_private_port + Phenotype.sol contract address (ADR-2605172300)."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    g = StateGraph(AuditWitnessState)

    g.add_node("poll_witnesses", lambda s: poll_witnesses(s, deps))
    g.add_node("verify_signatures", lambda s: verify_signatures(s, deps))
    g.add_node("compare_blobs", lambda s: compare_blobs(s, deps))
    g.add_node("attest_record", lambda s: attest_record(s, deps))
    g.add_node("escalate_mismatch", lambda s: escalate_mismatch(s, deps))
    g.add_node("feedback_phenotype", lambda s: feedback_phenotype(s, deps))

    g.add_edge(START, "poll_witnesses")
    g.add_edge("poll_witnesses", "verify_signatures")
    g.add_edge("verify_signatures", "compare_blobs")

    def consistency_router(state: AuditWitnessState) -> str:
        if state.get("invariantViolated"):
            return "escalate_mismatch"
        return "attest_record"

    g.add_conditional_edges("compare_blobs", consistency_router)

    def attest_router(state: AuditWitnessState) -> str:
        event_class = state.get("eventClass")
        if event_class in ("injury", "community-event"):
            return "feedback_phenotype"
        return END

    g.add_conditional_edges("attest_record", attest_router)
    g.add_edge("escalate_mismatch", END)
    g.add_edge("feedback_phenotype", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    """One thread per audit event (idempotent re-processing)."""
    rkey = event_record.get("rkey", "unknown")
    return f"AuditWitnessCell:{rkey}"


def healthz_extra(deps: CellDeps) -> dict:
    return {
        "role": "religious-corp self-inspection (constitutional)",
        "trigger_nsid": "com.etzhayyim.apps.etzhayyim.kuniUmi.recordPhysicalAuditEvent",
        "witness_invariant_min": 2,
        "constitutional_invariant": "N >= 2 NEVER reduce (ADR-2605201400 §9)",
        "feeds_phenotype": True,
    }
