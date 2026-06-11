from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants and functions from state_machine.py
class CastingPhase(Enum):
    INIT = "init"
    MOLD_PREPARED = "mold_prepared"
    DC_CASTING_COMPLETE = "dc_casting_complete"
    HOMOGENIZATION_COMPLETE = "homogenization_complete"
    INSPECTION_PASSED = "inspection_passed"
    RECORD_EMITTED = "record_emitted"

def transition_to_mold_prepared(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {**state.get("casting_state", {}), "phase": CastingPhase.MOLD_PREPARED.value, "completionPct": 20}}

def transition_to_dc_casting_complete(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {**state.get("casting_state", {}), "phase": CastingPhase.DC_CASTING_COMPLETE.value, "completionPct": 40}}

def transition_to_homogenization_complete(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {**state.get("casting_state", {}), "phase": CastingPhase.HOMOGENIZATION_COMPLETE.value, "completionPct": 60}}

def transition_to_inspection_passed(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {**state.get("casting_state", {}), "phase": CastingPhase.INSPECTION_PASSED.value, "completionPct": 80}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {**state.get("casting_state", {}), "phase": CastingPhase.RECORD_EMITTED.value, "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"casting_state": {
        "phase": CastingPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _prepare(s): return transition_to_mold_prepared(s)
def _cast(s): return transition_to_dc_casting_complete(s)
def _homogenize(s): return transition_to_homogenization_complete(s)
def _inspect(s): return transition_to_inspection_passed(s)
def _record(s): return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("prepare", _prepare)
_g.add_node("cast", _cast)
_g.add_node("homogenize", _homogenize)
_g.add_node("inspect", _inspect)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "prepare")
_g.add_edge("prepare", "cast")
_g.add_edge("cast", "homogenize")
_g.add_edge("homogenize", "inspect")
_g.add_edge("inspect", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
