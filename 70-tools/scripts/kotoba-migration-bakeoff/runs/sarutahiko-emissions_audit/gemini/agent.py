from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state_machine
class EmissionsPhase(Enum):
    INIT = "init"
    EURO7 = "euro7_scanned"
    JAPAN = "japan_pnlt_scanned"
    BHARAT = "bharat_vi_scanned"
    RECORD = "record_emitted"

def transition_to_euro7_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_state", {})
    return {"emissions_state": {**s, "phase": EmissionsPhase.EURO7.value, "completionPct": 25}}

def transition_to_japan_pnlt_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_state", {})
    return {"emissions_state": {**s, "phase": EmissionsPhase.JAPAN.value, "completionPct": 50}}

def transition_to_bharat_vi_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_state", {})
    return {"emissions_state": {**s, "phase": EmissionsPhase.BHARAT.value, "completionPct": 75}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_state", {})
    return {
        "emissions_state": {**s, "phase": EmissionsPhase.RECORD.value, "completionPct": 100},
        "emissions_record": {"chassisId": s.get("chassisId"), "status": "verified"}
    }

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"emissions_state": {
        "phase": EmissionsPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _euro7(s): return transition_to_euro7_scanned(s)
def _japan(s): return transition_to_japan_pnlt_scanned(s)
def _bharat(s): return transition_to_bharat_vi_scanned(s)
def _record(s): return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("euro7", _euro7)
_g.add_node("japan", _japan)
_g.add_node("bharat", _bharat)
_g.add_node("record", _record)
_g.add_edge(START, "init")
_g.add_edge("init", "euro7")
_g.add_edge("euro7", "japan")
_g.add_edge("japan", "bharat")
_g.add_edge("bharat", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
