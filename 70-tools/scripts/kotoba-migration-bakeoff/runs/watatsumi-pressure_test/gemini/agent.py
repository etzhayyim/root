"""PressureTestCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine logic ---

class MockValue:
    def __init__(self, val: str):
        self.value = val

class PressureTestPhase:
    INIT = MockValue("INIT")

def _update_pts(state: dict[str, Any], phase: str, pct: int) -> dict[str, Any]:
    pts = state.get("pressure_test_state", {}).copy()
    pts.update({"phase": phase, "completionPct": pct})
    return {"pressure_test_state": pts}

def transition_to_design_depth_verified(s: dict[str, Any]) -> dict[str, Any]:
    return _update_pts(s, "DESIGN_DEPTH_VERIFIED", 20)

def transition_to_dock_lowering(s: dict[str, Any]) -> dict[str, Any]:
    return _update_pts(s, "DOCK_LOWERING", 40)

def transition_to_pressurization(s: dict[str, Any]) -> dict[str, Any]:
    return _update_pts(s, "PRESSURIZATION", 60)

def transition_to_hold(s: dict[str, Any]) -> dict[str, Any]:
    return _update_pts(s, "HOLD", 80)

def transition_to_depressurization(s: dict[str, Any]) -> dict[str, Any]:
    return _update_pts(s, "DEPRESSURIZATION", 95)

def transition_to_record_emitted(s: dict[str, Any]) -> dict[str, Any]:
    res = _update_pts(s, "RECORD_EMITTED", 100)
    res["pressure_test_record"] = {"status": "SUCCESS"}
    return res

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "pressure_test_state": {
            "phase": PressureTestPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _verify_depth(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_design_depth_verified(s)

def _dock(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_dock_lowering(s)

def _pressurize(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_pressurization(s)

def _hold(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_hold(s)

def _depressurize(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_depressurization(s)

def _record(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(s)

# --- Graph Construction ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("verify_depth", _verify_depth)
_g.add_node("dock", _dock)
_g.add_node("pressurize", _pressurize)
_g.add_node("hold", _hold)
_g.add_node("depressurize", _depressurize)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "verify_depth")
_g.add_edge("verify_depth", "dock")
_g.add_edge("dock", "pressurize")
_g.add_edge("pressurize", "hold")
_g.add_edge("hold", "depressurize")
_g.add_edge("depressurize", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
