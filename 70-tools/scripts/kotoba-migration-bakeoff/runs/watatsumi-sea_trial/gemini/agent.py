"""SeaTrialCell — watatsumi R0 Pregel cell (L5c) compiled to WASM.

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

# Mock constants from .state_machine
class SeaTrialPhase:
    INIT = "init"
    DOCK = "dock"
    HARBOR = "harbor"
    DEEP_WATER = "deep_water"
    RECORD = "record"

def transition_to_dock_trial(state: dict[str, Any]) -> dict[str, Any]:
    st = state.get("sea_trial_state", {})
    return {
        "sea_trial_state": {
            **st,
            "phase": "dock",
            "completionPct": 25,
            "safety_check": True
        }
    }

def transition_to_harbor_dive(state: dict[str, Any]) -> dict[str, Any]:
    st = state.get("sea_trial_state", {})
    return {
        "sea_trial_state": {
            **st,
            "phase": "harbor",
            "completionPct": 50,
            "buoyancy_stable": True
        }
    }

def transition_to_deep_water_trial(state: dict[str, Any]) -> dict[str, Any]:
    st = state.get("sea_trial_state", {})
    return {
        "sea_trial_state": {
            **st,
            "phase": "deep_water",
            "completionPct": 85,
            "pressure_hull_check": "PASS"
        }
    }

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    st = state.get("sea_trial_state", {})
    return {
        "sea_trial_state": {**st, "phase": "record", "completionPct": 100},
        "sea_trial_final_record": {
            "craftId": st.get("craftId"),
            "status": "CERTIFIED",
            "log": "IMCA D-001 equivalent protocols satisfied."
        }
    }

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "sea_trial_state": {
            "phase": "init",
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _dock(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_dock_trial(s)

def _harbor(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_harbor_dive(s)

def _deep_water(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_deep_water_trial(s)

def _record(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("dock", _dock)
_g.add_node("harbor", _harbor)
_g.add_node("deep_water", _deep_water)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "dock")
_g.add_edge("dock", "harbor")
_g.add_edge("harbor", "deep_water")
_g.add_edge("deep_water", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
