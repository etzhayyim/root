from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants/classes from .state_machine
class MockEnumValue:
    def __init__(self, value: str):
        self.value = value

class WeldInspectionPhase:
    INIT = MockEnumValue("init")
    RT_COMPLETE = MockEnumValue("rt_complete")
    UT_COMPLETE = MockEnumValue("ut_complete")
    PT_COMPLETE = MockEnumValue("pt_complete")
    SANGO_WITNESSED = MockEnumValue("sango_witnessed")
    RECORD_EMITTED = MockEnumValue("record_emitted")

# Logic from original nodes
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "weld_inspection_state": {
            "phase": WeldInspectionPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "sectionIndex": state.get("sectionIndex", 0),
            "completionPct": 0,
        }
    }

def _rt(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("weld_inspection_state", {})
    return {"weld_inspection_state": {**s, "phase": WeldInspectionPhase.RT_COMPLETE.value, "completionPct": 20}}

def _ut(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("weld_inspection_state", {})
    return {"weld_inspection_state": {**s, "phase": WeldInspectionPhase.UT_COMPLETE.value, "completionPct": 40}}

def _pt(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("weld_inspection_state", {})
    return {"weld_inspection_state": {**s, "phase": WeldInspectionPhase.PT_COMPLETE.value, "completionPct": 60}}

def _sango(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("weld_inspection_state", {})
    return {"weld_inspection_state": {**s, "phase": WeldInspectionPhase.SANGO_WITNESSED.value, "completionPct": 80}}

def _record(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("weld_inspection_state", {})
    return {
        "weld_inspection_state": {**s, "phase": WeldInspectionPhase.RECORD_EMITTED.value, "completionPct": 100},
        "weld_inspection_record": {
            "craftId": s.get("craftId"),
            "sectionIndex": s.get("sectionIndex"),
            "status": "certified"
        }
    }

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("rt", _rt)
_g.add_node("ut", _ut)
_g.add_node("pt", _pt)
_g.add_node("sango", _sango)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "rt")
_g.add_edge("rt", "ut")
_g.add_edge("ut", "pt")
_g.add_edge("pt", "sango")
_g.add_edge("sango", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
