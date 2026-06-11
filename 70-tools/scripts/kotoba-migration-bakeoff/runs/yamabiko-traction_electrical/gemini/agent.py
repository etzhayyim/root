"""agent.py — TractionElectricalCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine constants and transitions ---

class TractionPhase(enum.Enum):
    INIT = "init"
    PROPULSION_GUARD_CHECKED = "propulsion_guard_checked"
    PANTOGRAPH_INSTALLED = "pantograph_installed"
    INVERTER_INSTALLED = "inverter_installed"
    ATP_ATO_FLASHED = "atp_ato_flashed"
    OPEN_SOURCE_VERIFIED = "open_source_verified"
    ATTESTATION_EMITTED = "attestation_emitted"

def transition_to_propulsion_guard_checked(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.PROPULSION_GUARD_CHECKED.value, "completionPct": 15})
    return {"traction_state": s}

def transition_to_pantograph_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.PANTOGRAPH_INSTALLED.value, "completionPct": 30})
    return {"traction_state": s}

def transition_to_inverter_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.INVERTER_INSTALLED.value, "completionPct": 50})
    return {"traction_state": s}

def transition_to_atp_ato_flashed(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.ATP_ATO_FLASHED.value, "completionPct": 70})
    return {"traction_state": s}

def transition_to_open_source_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.OPEN_SOURCE_VERIFIED.value, "completionPct": 90})
    return {"traction_state": s}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("traction_state", {}).copy()
    s.update({"phase": TractionPhase.ATTESTATION_EMITTED.value, "completionPct": 100})
    return {
        "traction_state": s,
        "traction_attestation_record": {
            "trainsetId": s.get("trainsetId"),
            "status": "certified",
            "atp_ato_version": "v1.0.0-open",
            "propulsion_guard": "active"
        }
    }

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"traction_state": {
        "phase": TractionPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "completionPct": 0,
    }}

def _propulsion(s): return transition_to_propulsion_guard_checked(s)
def _pantograph(s): return transition_to_pantograph_installed(s)
def _inverter(s): return transition_to_inverter_installed(s)
def _atp(s): return transition_to_atp_ato_flashed(s)
def _verify(s): return transition_to_open_source_verified(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("propulsion", _propulsion)
_g.add_node("pantograph", _pantograph)
_g.add_node("inverter", _inverter)
_g.add_node("atp", _atp)
_g.add_node("verify", _verify)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "propulsion")
_g.add_edge("propulsion", "pantograph")
_g.add_edge("pantograph", "inverter")
_g.add_edge("inverter", "atp")
_g.add_edge("atp", "verify")
_g.add_edge("verify", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
