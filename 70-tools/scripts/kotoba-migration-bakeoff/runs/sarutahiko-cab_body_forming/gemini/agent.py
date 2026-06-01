from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state machine constants and transitions
class CabPhase:
    class INIT:
        value = "init"

def transition_to_sheet_lot_verified(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("cab_state", {})
    return {"cab_state": {**cs, "phase": "sheet_lot_verified", "completionPct": 20}}

def transition_to_hot_stamping_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("cab_state", {})
    return {"cab_state": {**cs, "phase": "hot_stamping_complete", "completionPct": 40}}

def transition_to_spot_welding_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("cab_state", {})
    return {"cab_state": {**cs, "phase": "spot_welding_complete", "completionPct": 60}}

def transition_to_leak_test_passed(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("cab_state", {})
    return {"cab_state": {**cs, "phase": "leak_test_passed", "completionPct": 80}}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("cab_state", {})
    return {"cab_state": {**cs, "phase": "attestation_emitted", "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"cab_state": {
        "phase": CabPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _verify(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_sheet_lot_verified(s)

def _stamp(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_hot_stamping_complete(s)

def _weld(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_spot_welding_complete(s)

def _leak(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_leak_test_passed(s)

def _attestation(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("verify", _verify)
_g.add_node("stamp", _stamp)
_g.add_node("weld", _weld)
_g.add_node("leak", _leak)
_g.add_node("attestation", _attestation)
_g.add_edge(START, "init")
_g.add_edge("init", "verify")
_g.add_edge("verify", "stamp")
_g.add_edge("stamp", "weld")
_g.add_edge("weld", "leak")
_g.add_edge("leak", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
