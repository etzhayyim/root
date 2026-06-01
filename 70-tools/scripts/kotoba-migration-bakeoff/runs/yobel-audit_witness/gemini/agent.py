"""AuditWitnessCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any, Literal
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Constants and Mocks ---
SourceKind = Literal["super_step", "release_finalized", "sensor_poll"]
TamperingSeverity = Literal["none", "suspicion", "confirmed"]

# --- Node functions ---

def collect_state_diff(state: dict) -> dict:
    """Compute / pass-through (stateRootBefore, stateRootAfter, txDigest)."""
    if not state.get("tx_digest"):
        before = state.get("state_root_before", "")
        after = state.get("state_root_after", "")
        return {"tx_digest": f"{before[:32]}::{after[:32]}"}
    return {} # LangGraph nodes should return only updates

def verify_chain_continuity(state: dict) -> dict:
    """Look up previous signed triple; verify chain hash continuity. (Mocked)"""
    # Original used audit_log_port. In WASM, we mock it or use state.
    # For this port, we'll assume it's valid unless state says otherwise,
    # as we don't have the real port objects.
    return {"chain_valid": True, "tampering_severity": "none", "prev_signed_triple_cid": ""}

def sign_and_append(state: dict) -> dict:
    """Sign (prev_cid || state_root_before || state_root_after || tx_digest) and append. (Mocked)"""
    return {
        "witness_key_id": "stub-key",
        "signed_triple_hex": "0xstub",
        "audit_event_cid": "ipfs://stub-audit-event",
        "audit_event_uri": f"at://stub/audit/{state.get('rite_id','unknown')}/{state.get('tx_digest','')}",
    }

def anchor_batch(state: dict) -> dict:
    """Anchor every 100 events or 10 minutes, whichever first. (Mocked)"""
    return {"batch_anchored": False, "base_l2_anchor_tx_hash": ""}

def on_tampering_detected(state: dict) -> dict:
    """Mark rite superseded + Public Fund grant + Council notification. (Mocked)"""
    rite_id = state.get("rite_id", "")
    return {
        "incident_uri": f"at://stub/incident/{rite_id}",
    }

# --- Router ---

def chain_router(state: dict) -> str:
    if state.get("tampering_severity") == "confirmed":
        return "on_tampering_detected"
    return "sign_and_append"

# --- Graph Builder ---

_g = StateGraph(dict)

_g.add_node("collect_state_diff", collect_state_diff)
_g.add_node("verify_chain_continuity", verify_chain_continuity)
_g.add_node("sign_and_append", sign_and_append)
_g.add_node("anchor_batch", anchor_batch)
_g.add_node("on_tampering_detected", on_tampering_detected)

_g.add_edge(START, "collect_state_diff")
_g.add_edge("collect_state_diff", "verify_chain_continuity")
_g.add_conditional_edges("verify_chain_continuity", chain_router)
_g.add_edge("sign_and_append", "anchor_batch")
_g.add_edge("anchor_batch", END)
_g.add_edge("on_tampering_detected", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
