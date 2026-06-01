"""agent.py — EmissionsAcousticAuditCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for state_machine.py ---
class AcousticPhase(Enum):
    INIT = "init"
    WAYSIDE_NOISE = "wayside_noise_measured"
    VIBRATION = "vibration_measured"
    EMC = "emc_verified"
    RECORD = "record_emitted"

def transition_to_wayside_noise_measured(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("acoustic_state", {})
    return {"acoustic_state": {**curr, "phase": AcousticPhase.WAYSIDE_NOISE.value, "completionPct": 25}}

def transition_to_vibration_measured(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("acoustic_state", {})
    return {"acoustic_state": {**curr, "phase": AcousticPhase.VIBRATION.value, "completionPct": 50}}

def transition_to_emc_verified(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("acoustic_state", {})
    return {"acoustic_state": {**curr, "phase": AcousticPhase.EMC.value, "completionPct": 75}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("acoustic_state", {})
    return {
        "acoustic_state": {**curr, "phase": AcousticPhase.RECORD.value, "completionPct": 100},
        "audit_record": {
            "trainsetId": curr.get("trainsetId"),
            "status": "verified",
            "audit_type": "emissions_acoustic"
        }
    }

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"acoustic_state": {
        "phase": AcousticPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "completionPct": 0,
    }}

def _noise(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_wayside_noise_measured(state)

def _vibration(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_vibration_measured(state)

def _emc(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_emc_verified(state)

def _record(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(state)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("noise", _noise)
_g.add_node("vibration", _vibration)
_g.add_node("emc", _emc)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "noise")
_g.add_edge("noise", "vibration")
_g.add_edge("vibration", "emc")
_g.add_edge("emc", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
