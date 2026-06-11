"""SilenRailReviewCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants and transitions from state_machine
class ReviewPhase:
    INIT = "init"
    SCOPE_DECLARED = "scope_declared"
    SIGNATURES_COLLECTED = "signatures_collected"
    DECISION_RECORDED = "decision_recorded"
    RECORD_EMITTED = "record_emitted"

def transition_to_scope_declared(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("review_state", {}).copy()
    rs.update({
        "phase": "scope_declared",
        "completionPct": 20,
        "scope": "standard-rail-safety-review"
    })
    return {"review_state": rs}

def transition_to_signatures_collected(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("review_state", {}).copy()
    rs.update({
        "phase": "signatures_collected",
        "completionPct": 60,
        "signatures": ["did:web:yamabiko.rail:safety-auth-1", "did:web:yamabiko.rail:safety-auth-2"]
    })
    return {"review_state": rs}

def transition_to_decision_recorded(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("review_state", {}).copy()
    rs.update({
        "phase": "decision_recorded",
        "completionPct": 90,
        "decision": "approved"
    })
    return {"review_state": rs}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("review_state", {}).copy()
    rs.update({
        "phase": "record_emitted",
        "completionPct": 100
    })
    return {
        "review_state": rs,
        "final_record": {
            "reviewSubjectId": rs.get("reviewSubjectId"),
            "status": "finalized",
            "decision": rs.get("decision")
        }
    }

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"review_state": {
        "phase": "init",
        "reviewSubjectId": state.get("reviewSubjectId", "YAMABIKO-R0-SCAFFOLD-BASELINE"),
        "completionPct": 0,
    }}

def _scope(s: dict[str, Any]) -> dict[str, Any]: return transition_to_scope_declared(s)
def _signatures(s: dict[str, Any]) -> dict[str, Any]: return transition_to_signatures_collected(s)
def _decision(s: dict[str, Any]) -> dict[str, Any]: return transition_to_decision_recorded(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("scope", _scope)
_g.add_node("signatures", _signatures)
_g.add_node("decision", _decision)
_g.add_node("record", _record)
_g.add_edge(START, "init")
_g.add_edge("init", "scope")
_g.add_edge("scope", "signatures")
_g.add_edge("signatures", "decision")
_g.add_edge("decision", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
