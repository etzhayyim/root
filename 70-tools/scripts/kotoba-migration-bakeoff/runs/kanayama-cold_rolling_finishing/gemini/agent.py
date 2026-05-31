"""ColdRollingFinishingCell — kanayama R0 Pregel cell (L5b). R0 scaffold.
Compiled to WASM for Kotoba.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for state_machine ---
class ColdRollingPhase(Enum):
    INIT = "init"
    HOT_BAND_LOADED = "hot_band_loaded"
    COLD_PASSES_COMPLETE = "cold_passes_complete"
    TEMPER_COMPLETE = "temper_complete"
    SURFACE_INSPECTION_COMPLETE = "surface_inspection_complete"
    COIL_QUALIFIED = "coil_qualified"
    RECORD_EMITTED = "record_emitted"

def transition_to_hot_band_loaded(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.HOT_BAND_LOADED.value, "completionPct": 20}}

def transition_to_cold_passes_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.COLD_PASSES_COMPLETE.value, "completionPct": 40}}

def transition_to_temper_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.TEMPER_COMPLETE.value, "completionPct": 60}}

def transition_to_surface_inspection_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.SURFACE_INSPECTION_COMPLETE.value, "completionPct": 80}}

def transition_to_coil_qualified(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.COIL_QUALIFIED.value, "completionPct": 90}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("cold_rolling_state", {})
    return {"cold_rolling_state": {**s, "phase": ColdRollingPhase.RECORD_EMITTED.value, "completionPct": 100}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"cold_rolling_state": {
        "phase": ColdRollingPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _load(s): return transition_to_hot_band_loaded(s)
def _cold(s): return transition_to_cold_passes_complete(s)
def _temper(s): return transition_to_temper_complete(s)
def _migaki(s): return transition_to_surface_inspection_complete(s)
def _qualify(s): return transition_to_coil_qualified(s)
def _record(s): return transition_to_record_emitted(s)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("load", _load)
_g.add_node("cold", _cold)
_g.add_node("temper", _temper)
_g.add_node("migaki", _migaki)
_g.add_node("qualify", _qualify)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "load")
_g.add_edge("load", "cold")
_g.add_edge("cold", "temper")
_g.add_edge("temper", "migaki")
_g.add_edge("migaki", "qualify")
_g.add_edge("qualify", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
