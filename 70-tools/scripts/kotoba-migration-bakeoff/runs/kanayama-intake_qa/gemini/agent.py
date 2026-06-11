from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mock state_machine ---

class MockEnum:
    def __init__(self, value):
        self.value = value

class IntakePhase:
    INIT = MockEnum("init")
    WEIGHED = MockEnum("weighed")
    SCANNED = MockEnum("scanned")
    DECIDED = MockEnum("decided")
    RECORDED = MockEnum("recorded")

def transition_to_bale_weighed(state: dict[str, Any]) -> dict[str, Any]:
    return {"intake_state": {**state.get("intake_state", {}), "phase": IntakePhase.WEIGHED.value, "completionPct": 25}}

def transition_to_contamination_scanned(state: dict[str, Any]) -> dict[str, Any]:
    return {"intake_state": {**state.get("intake_state", {}), "phase": IntakePhase.SCANNED.value, "completionPct": 50}}

def transition_to_accept_or_reject_decided(state: dict[str, Any]) -> dict[str, Any]:
    return {"intake_state": {**state.get("intake_state", {}), "phase": IntakePhase.DECIDED.value, "completionPct": 75}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    return {"intake_state": {**state.get("intake_state", {}), "phase": IntakePhase.RECORDED.value, "completionPct": 100}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"intake_state": {
        "phase": IntakePhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _weigh(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_bale_weighed(state)

def _scan(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_contamination_scanned(state)

def _decide(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_accept_or_reject_decided(state)

def _record(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(state)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("weigh", _weigh)
_g.add_node("scan", _scan)
_g.add_node("decide", _decide)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "weigh")
_g.add_edge("weigh", "scan")
_g.add_edge("scan", "decide")
_g.add_edge("decide", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

# --- Wit World ---

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
