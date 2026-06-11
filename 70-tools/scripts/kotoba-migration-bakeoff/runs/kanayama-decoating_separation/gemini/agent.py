"""agent.py — DecoatingSeparationCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state_machine dependencies
class DecoatingPhase(Enum):
    INIT = "INIT"
    HEATED = "HEATED"
    BURNOFF_COMPLETE = "BURNOFF_COMPLETE"
    SHRED_COMPLETE = "SHRED_COMPLETE"
    MAGNETIC_COMPLETE = "MAGNETIC_COMPLETE"
    EDDY_COMPLETE = "EDDY_COMPLETE"
    RECORD_EMITTED = "RECORD_EMITTED"

def transition_to_decoater_heated(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {"decoating_state": {**ds, "phase": DecoatingPhase.HEATED.value, "completionPct": 15}}

def transition_to_lacquer_burnoff_complete(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {"decoating_state": {**ds, "phase": DecoatingPhase.BURNOFF_COMPLETE.value, "completionPct": 30}}

def transition_to_shred_complete(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {"decoating_state": {**ds, "phase": DecoatingPhase.SHRED_COMPLETE.value, "completionPct": 50}}

def transition_to_magnetic_separation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {"decoating_state": {**ds, "phase": DecoatingPhase.MAGNETIC_COMPLETE.value, "completionPct": 70}}

def transition_to_eddy_current_separation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {"decoating_state": {**ds, "phase": DecoatingPhase.EDDY_COMPLETE.value, "completionPct": 90}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("decoating_state", {})
    return {
        "decoating_state": {**ds, "phase": DecoatingPhase.RECORD_EMITTED.value, "completionPct": 100},
        "output_record": {"lotId": ds.get("lotId"), "status": "processed"}
    }

# Node functions (Module-level)
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"decoating_state": {
        "phase": DecoatingPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _heat(s: dict[str, Any]) -> dict[str, Any]: return transition_to_decoater_heated(s)
def _burnoff(s: dict[str, Any]) -> dict[str, Any]: return transition_to_lacquer_burnoff_complete(s)
def _shred(s: dict[str, Any]) -> dict[str, Any]: return transition_to_shred_complete(s)
def _magnetic(s: dict[str, Any]) -> dict[str, Any]: return transition_to_magnetic_separation_complete(s)
def _eddy(s: dict[str, Any]) -> dict[str, Any]: return transition_to_eddy_current_separation_complete(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# Graph Builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("heat", _heat)
_g.add_node("burnoff", _burnoff)
_g.add_node("shred", _shred)
_g.add_node("magnetic", _magnetic)
_g.add_node("eddy", _eddy)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "heat")
_g.add_edge("heat", "burnoff")
_g.add_edge("burnoff", "shred")
_g.add_edge("shred", "magnetic")
_g.add_edge("magnetic", "eddy")
_g.add_edge("eddy", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
