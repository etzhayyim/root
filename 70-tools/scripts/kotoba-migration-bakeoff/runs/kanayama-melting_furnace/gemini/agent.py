"""agent.py — MeltingFurnaceCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---
from enum import Enum

class MeltingPhase(Enum):
    INIT = "init"
    CHARGED = "charged"
    MELT_HELD = "melt_held"
    DEGAS_COMPLETE = "degas_complete"
    ALLOY_ADJUSTED = "alloy_adjusted"
    POUR_WITNESSED = "pour_witnessed"
    RECORD_EMITTED = "record_emitted"

def transition_to_charged(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.CHARGED.value, "completionPct": 20}}

def transition_to_melt_held(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.MELT_HELD.value, "completionPct": 40}}

def transition_to_degas_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.DEGAS_COMPLETE.value, "completionPct": 60}}

def transition_to_alloy_adjusted(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.ALLOY_ADJUSTED.value, "completionPct": 80}}

def transition_to_pour_witnessed(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.POUR_WITNESSED.value, "completionPct": 100}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("melting_state", {})
    return {"melting_state": {**ms, "phase": MeltingPhase.RECORD_EMITTED.value, "record_emitted": True}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"melting_state": {
        "phase": MeltingPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _charge(s: dict[str, Any]) -> dict[str, Any]: return transition_to_charged(s)
def _hold(s: dict[str, Any]) -> dict[str, Any]: return transition_to_melt_held(s)
def _degas(s: dict[str, Any]) -> dict[str, Any]: return transition_to_degas_complete(s)
def _alloy(s: dict[str, Any]) -> dict[str, Any]: return transition_to_alloy_adjusted(s)
def _pour(s: dict[str, Any]) -> dict[str, Any]: return transition_to_pour_witnessed(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# --- Graph Definition ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("charge", _charge)
_g.add_node("hold", _hold)
_g.add_node("degas", _degas)
_g.add_node("alloy", _alloy)
_g.add_node("pour", _pour)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "charge")
_g.add_edge("charge", "hold")
_g.add_edge("hold", "degas")
_g.add_edge("degas", "alloy")
_g.add_edge("alloy", "pour")
_g.add_edge("pour", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
