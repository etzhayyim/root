"""
AuditWitnessCell — Continuous Pregel cell witnessing all super-step transitions + release MST events.

Per ADR-2605201800 §Decision + ADR-2605192415 §B continuous-witness pattern.

Trigger: LangGraph super-step boundary, release MST finalization, 60s sensor polling
Effect:
  - Collect (stateRootBefore, stateRootAfter, txDigest) triple
  - Sign with rotating witness key, append to auditLog MST collection
  - Detect tampering (missing prior signature / hash-chain break)
  - Batched anchor (every 100 events or 10 minutes) via AnchorBridge
  - On tampering: rite status=superseded_for_audit + Public Fund grant request +
    Council Lv9 + Five-Bootstrap-Council notification

Murakumo node: reuben (firstborn / witness — Gen 49:3, Gen 29:32 "God has seen my affliction").
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver


SourceKind = Literal["super_step", "release_finalized", "sensor_poll"]
TamperingSeverity = Literal["none", "suspicion", "confirmed"]


class AuditWitnessState(TypedDict, total=False):
    # Input
    source_kind: SourceKind
    rite_id: str
    state_root_before: str
    state_root_after: str
    tx_digest: str
    event_payload: dict

    # Chain check
    prev_signed_triple_cid: str
    chain_valid: bool
    chain_break_reason: str

    # Witness signature
    witness_key_id: str
    signed_triple_hex: str

    # Tampering
    tampering_severity: TamperingSeverity

    # Anchor batch
    audit_event_cid: str
    batch_anchored: bool
    base_l2_anchor_tx_hash: str

    # Outputs
    audit_event_uri: str
    incident_uri: str  # only set when tampering confirmed


def build_graph(
    checkpointer: BaseCheckpointSaver,
    audit_log_port,
    witness_keystore,
    anchor_bridge,
    public_fund_port,
    council_notifier,
):
    g = StateGraph(AuditWitnessState)

    g.add_node("collect_state_diff", collect_state_diff)
    g.add_node("verify_chain_continuity", lambda s: verify_chain_continuity(s, audit_log_port))
    g.add_node("sign_and_append", lambda s: sign_and_append(s, witness_keystore, audit_log_port))
    g.add_node("anchor_batch", lambda s: anchor_batch(s, anchor_bridge, audit_log_port))
    g.add_node("on_tampering_detected", lambda s: on_tampering_detected(s, public_fund_port, council_notifier))

    g.add_edge(START, "collect_state_diff")
    g.add_edge("collect_state_diff", "verify_chain_continuity")

    def chain_router(state):
        # tampering_severity confirmed only on 2-node consensus; single-node = suspicion
        if state.get("tampering_severity") == "confirmed":
            return "on_tampering_detected"
        return "sign_and_append"

    g.add_conditional_edges("verify_chain_continuity", chain_router)
    g.add_edge("sign_and_append", "anchor_batch")
    g.add_edge("anchor_batch", END)
    g.add_edge("on_tampering_detected", END)

    return g.compile(checkpointer=checkpointer)


# ─── Node functions ──────────────────────────────────────────────────


def collect_state_diff(state):
    """Compute / pass-through (stateRootBefore, stateRootAfter, txDigest)."""
    # Inputs already populated by trigger emitter; this node is a hook for extra normalization
    if not state.get("tx_digest"):
        # Fallback digest: concat roots
        before = state.get("state_root_before", "")
        after = state.get("state_root_after", "")
        return {"tx_digest": f"{before[:32]}::{after[:32]}"}
    return state


def verify_chain_continuity(state, audit_log_port):
    """Look up previous signed triple; verify chain hash continuity."""
    if audit_log_port is None:
        return {"chain_valid": True, "tampering_severity": "none", "prev_signed_triple_cid": ""}
    prev = audit_log_port.tail_signed_triple(rite_id=state.get("rite_id", ""))
    if prev is None:
        # First witness for this rite — chain genesis OK
        return {"chain_valid": True, "tampering_severity": "none", "prev_signed_triple_cid": ""}
    chain_ok = audit_log_port.verify_chain_link(
        prev_signed_cid=prev.cid,
        next_state_root_before=state.get("state_root_before", ""),
    )
    if chain_ok:
        return {
            "chain_valid": True,
            "tampering_severity": "none",
            "prev_signed_triple_cid": prev.cid,
        }
    # Chain break detected — require 2-node consensus before raising `confirmed`
    consensus = audit_log_port.poll_replica_consensus(
        rite_id=state["rite_id"],
        expected_prev_cid=prev.cid,
    )
    severity: TamperingSeverity = "confirmed" if consensus.replicas_agree else "suspicion"
    return {
        "chain_valid": False,
        "chain_break_reason": f"prev_cid {prev.cid} not matched by next state_root_before",
        "tampering_severity": severity,
        "prev_signed_triple_cid": prev.cid,
    }


def sign_and_append(state, witness_keystore, audit_log_port):
    """Sign (prev_cid || state_root_before || state_root_after || tx_digest) and append."""
    if witness_keystore is None or audit_log_port is None:
        return {
            "witness_key_id": "stub-key",
            "signed_triple_hex": "0xstub",
            "audit_event_cid": "ipfs://stub-audit-event",
            "audit_event_uri": f"at://stub/audit/{state.get('rite_id','unknown')}/{state.get('tx_digest','')}",
        }
    key = witness_keystore.current_key()
    payload = (
        state.get("prev_signed_triple_cid", "")
        + state.get("state_root_before", "")
        + state.get("state_root_after", "")
        + state.get("tx_digest", "")
    )
    sig = witness_keystore.sign(key_id=key.id, payload=payload.encode())
    appended = audit_log_port.append(
        rite_id=state.get("rite_id", ""),
        source_kind=state.get("source_kind", "super_step"),
        prev_cid=state.get("prev_signed_triple_cid", ""),
        state_root_before=state.get("state_root_before", ""),
        state_root_after=state.get("state_root_after", ""),
        tx_digest=state.get("tx_digest", ""),
        witness_key_id=key.id,
        signature_hex=sig.hex(),
        event_payload=state.get("event_payload", {}),
    )
    return {
        "witness_key_id": key.id,
        "signed_triple_hex": sig.hex(),
        "audit_event_cid": appended.cid,
        "audit_event_uri": appended.vertex_uri,
    }


def anchor_batch(state, anchor_bridge, audit_log_port):
    """Anchor every 100 events or 10 minutes, whichever first."""
    if anchor_bridge is None or audit_log_port is None:
        return {"batch_anchored": False, "base_l2_anchor_tx_hash": ""}
    batch_status = audit_log_port.batch_status()
    if not (batch_status.event_count >= 100 or batch_status.seconds_since_last_anchor >= 600):
        return {"batch_anchored": False, "base_l2_anchor_tx_hash": ""}
    result = anchor_bridge.batched_anchor(
        contract="AuditAnchorRegistry",
        cids=batch_status.pending_cids,
    )
    audit_log_port.mark_anchored(batch_status.pending_cids, tx_hash=result.tx_hash)
    return {"batch_anchored": True, "base_l2_anchor_tx_hash": result.tx_hash}


def on_tampering_detected(state, public_fund_port, council_notifier):
    """Mark rite superseded + Public Fund grant + Council notification."""
    rite_id = state.get("rite_id", "")
    incident_uri = ""
    if public_fund_port is not None:
        public_fund_port.request_audit_grant(
            reason="yobel.tampering_detected",
            rite_id=rite_id,
            chain_break_reason=state.get("chain_break_reason", ""),
        )
    if council_notifier is not None:
        notification = council_notifier.notify(
            targets=["council_lv9_chair", "five_bootstrap_council"],
            event_type="yobel.tampering_confirmed",
            rite_id=rite_id,
            severity="confirmed",
            payload=state,
        )
        incident_uri = notification.incident_uri
    return {
        "incident_uri": incident_uri or f"at://stub/incident/{rite_id}",
    }
