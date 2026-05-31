"""BogieAssemblyCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---

class BogiePhase:
    INIT = "init"
    FRAME_PREPARED = "frame_prepared"
    WHEEL_SET_MOUNTED = "wheel_set_mounted"
    MOTOR_INSTALLED = "motor_installed"
    BRAKE_INTEGRATED = "brake_integrated"
    AIR_SPRING_INSTALLED = "air_spring_installed"
    ATTESTATION_EMITTED = "attestation_emitted"

def transition_to_frame_prepared(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.FRAME_PREPARED, "completionPct": 15})
    return {"bogie_state": bogie_state}

def transition_to_wheel_set_mounted(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.WHEEL_SET_MOUNTED, "completionPct": 35})
    return {"bogie_state": bogie_state}

def transition_to_motor_installed(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.MOTOR_INSTALLED, "completionPct": 55})
    return {"bogie_state": bogie_state}

def transition_to_brake_integrated(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.BRAKE_INTEGRATED, "completionPct": 75})
    return {"bogie_state": bogie_state}

def transition_to_air_spring_installed(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.AIR_SPRING_INSTALLED, "completionPct": 90})
    return {"bogie_state": bogie_state}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    bogie_state = state.get("bogie_state", {}).copy()
    bogie_state.update({"phase": BogiePhase.ATTESTATION_EMITTED, "completionPct": 100})
    return {
        "bogie_state": bogie_state,
        "bogie_attestation_record": {
            "trainsetId": bogie_state.get("trainsetId"),
            "bogieIndex": bogie_state.get("bogieIndex"),
            "status": "ASSEMBLY_COMPLETE"
        }
    }

# --- Graph Definition ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"bogie_state": {
        "phase": BogiePhase.INIT,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "bogieIndex": state.get("bogieIndex", 0),
        "completionPct": 0,
    }}

def _frame(s): return transition_to_frame_prepared(s)
def _wheel(s): return transition_to_wheel_set_mounted(s)
def _motor(s): return transition_to_motor_installed(s)
def _brake(s): return transition_to_brake_integrated(s)
def _air(s): return transition_to_air_spring_installed(s)
def _attestation(s): return transition_to_attestation_emitted(s)

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("frame", _frame)
_g.add_node("wheel", _wheel)
_g.add_node("motor", _motor)
_g.add_node("brake", _brake)
_g.add_node("air", _air)
_g.add_node("attestation", _attestation)
_g.add_edge(START, "init")
_g.add_edge("init", "frame")
_g.add_edge("frame", "wheel")
_g.add_edge("wheel", "motor")
_g.add_edge("motor", "brake")
_g.add_edge("brake", "air")
_g.add_edge("air", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
