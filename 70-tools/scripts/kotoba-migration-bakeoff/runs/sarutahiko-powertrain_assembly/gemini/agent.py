from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocking .state_machine
class PowertrainPhase(Enum):
    INIT = "init"
    FUEL_GUARD_CHECKED = "fuel_guard_checked"
    ENGINE_INSTALLED = "engine_installed"
    TRANSMISSION_COUPLED = "transmission_coupled"
    AXLES_MOUNTED = "axles_mounted"
    BRAKE_INTEGRATED = "brake_integrated"
    ATTESTATION_EMITTED = "attestation_emitted"

def transition_to_fuel_guard_checked(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.FUEL_GUARD_CHECKED.value, "completionPct": 15}}

def transition_to_engine_installed(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.ENGINE_INSTALLED.value, "completionPct": 30}}

def transition_to_transmission_coupled(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.TRANSMISSION_COUPLED.value, "completionPct": 45}}

def transition_to_axles_mounted(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.AXLES_MOUNTED.value, "completionPct": 60}}

def transition_to_brake_integrated(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.BRAKE_INTEGRATED.value, "completionPct": 75}}

def transition_to_attestation_emitted(s):
    state = s.get("powertrain_state", {})
    return {"powertrain_state": {**state, "phase": PowertrainPhase.ATTESTATION_EMITTED.value, "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"powertrain_state": {
        "phase": PowertrainPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _fuel_guard(s): return transition_to_fuel_guard_checked(s)
def _engine(s): return transition_to_engine_installed(s)
def _transmission(s): return transition_to_transmission_coupled(s)
def _axles(s): return transition_to_axles_mounted(s)
def _brake(s): return transition_to_brake_integrated(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("fuel_guard", _fuel_guard)
_g.add_node("engine", _engine)
_g.add_node("transmission", _transmission)
_g.add_node("axles", _axles)
_g.add_node("brake", _brake)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "fuel_guard")
_g.add_edge("fuel_guard", "engine")
_g.add_edge("engine", "transmission")
_g.add_edge("transmission", "axles")
_g.add_edge("axles", "brake")
_g.add_edge("brake", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
