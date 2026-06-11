"""DynamicTestCell — ported to Kotoba WASM."""

from __future__ import annotations
from typing import Any
import wit_world
from enum import Enum

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants/functions from .state_machine
class DynamicPhase(Enum):
    INIT = "init"
    STATIC_PASSED = "static_passed"
    G12_VERIFIED = "g12_verified"
    RUN_COMPLETE = "run_complete"
    RECORD_EMITTED = "record_emitted"

def transition_to_static_test_passed(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dynamic_state", {}).copy()
    ds.update({"phase": DynamicPhase.STATIC_PASSED.value, "completionPct": 25})
    return {"dynamic_state": ds}

def transition_to_g12_kpi_verified(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dynamic_state", {}).copy()
    ds.update({"phase": DynamicPhase.G12_VERIFIED.value, "completionPct": 50})
    return {"dynamic_state": ds}

def transition_to_dynamic_run_complete(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dynamic_state", {}).copy()
    ds.update({"phase": DynamicPhase.RUN_COMPLETE.value, "completionPct": 75})
    return {"dynamic_state": ds}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dynamic_state", {}).copy()
    ds.update({"phase": DynamicPhase.RECORD_EMITTED.value, "completionPct": 100})
    return {"dynamic_state": ds, "final_record": {"trainsetId": ds.get("trainsetId"), "status": "verified"}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"dynamic_state": {
        "phase": DynamicPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "completionPct": 0,
    }}

def _static(s: dict[str, Any]) -> dict[str, Any]: return transition_to_static_test_passed(s)
def _g12(s: dict[str, Any]) -> dict[str, Any]: return transition_to_g12_kpi_verified(s)
def _run(s: dict[str, Any]) -> dict[str, Any]: return transition_to_dynamic_run_complete(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("static", _static)
_g.add_node("g12", _g12)
_g.add_node("run", _run)
_g.add_node("record", _record)
_g.add_edge(START, "init")
_g.add_edge("init", "static")
_g.add_edge("static", "g12")
_g.add_edge("g12", "run")
_g.add_edge("run", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
