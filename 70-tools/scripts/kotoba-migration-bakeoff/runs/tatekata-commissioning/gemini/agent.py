"""CommissioningCell compiled to WASM.

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

# Mock constants/logic from .state_machine
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    projectId = state.get("projectId", "unknown")
    return {
        "commissioning_state": {
            "phase": "init",
            "projectId": projectId,
            "completionPct": 0,
        },
        "next_node": "test"
    }

def _final_systems_test(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("commissioning_state", {})
    return {
        "commissioning_state": {**cs, "phase": "systems_tested", "completionPct": 20},
        "next_node": "walkdown"
    }

def _defect_walkdown(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("commissioning_state", {})
    return {
        "commissioning_state": {**cs, "phase": "defects_identified", "completionPct": 40},
        "next_node": "waste"
    }

def _waste_inventory(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("commissioning_state", {})
    return {
        "commissioning_state": {**cs, "phase": "waste_logged", "completionPct": 60},
        "next_node": "signoff"
    }

def _project_signoff(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("commissioning_state", {})
    return {
        "commissioning_state": {**cs, "phase": "signed_off", "completionPct": 80},
        "next_node": "emit"
    }

def _emit_record(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("commissioning_state", {})
    return {
        "commissioning_state": {**cs, "phase": "complete", "completionPct": 100},
        "projectClosure": {
            "projectId": cs.get("projectId"),
            "status": "closed",
            "witness_signed": True
        },
        "next_node": "end"
    }

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("test", _final_systems_test)
_g.add_node("walkdown", _defect_walkdown)
_g.add_node("waste", _waste_inventory)
_g.add_node("signoff", _project_signoff)
_g.add_node("emit", _emit_record)

_g.add_edge(START, "init")
_g.add_edge("init", "test")
_g.add_edge("test", "walkdown")
_g.add_edge("walkdown", "waste")
_g.add_edge("waste", "signoff")
_g.add_edge("signoff", "emit")
_g.add_edge("emit", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
