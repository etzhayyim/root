"""FinalMarriageCell — sarutahiko R0 Pregel cell (L4) ported to Kotoba WASM.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants and transitions from .state_machine
class MarriagePhaseValue:
    def __init__(self, value: str):
        self.value = value

class MarriagePhase:
    INIT = MarriagePhaseValue("init")
    VERIFIED = MarriagePhaseValue("inputs_verified")
    LOWERED = MarriagePhaseValue("chassis_lowered")
    CAB = MarriagePhaseValue("cab_dropped")
    POWERTRAIN = MarriagePhaseValue("powertrain_mounted")
    HARNESS = MarriagePhaseValue("harness_connected")
    ATTESTATION = MarriagePhaseValue("attestation_emitted")

def transition_to_inputs_verified(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.VERIFIED.value, "completionPct": 20})
    return {"marriage_state": ms}

def transition_to_chassis_lowered(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.LOWERED.value, "completionPct": 40})
    return {"marriage_state": ms}

def transition_to_cab_dropped(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.CAB.value, "completionPct": 60})
    return {"marriage_state": ms}

def transition_to_powertrain_mounted(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.POWERTRAIN.value, "completionPct": 80})
    return {"marriage_state": ms}

def transition_to_harness_connected(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.HARNESS.value, "completionPct": 95})
    return {"marriage_state": ms}

def transition_to_attestation_emitted(state: dict) -> dict:
    ms = state.get("marriage_state", {}).copy()
    ms.update({"phase": MarriagePhase.ATTESTATION.value, "completionPct": 100})
    return {"marriage_state": ms}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"marriage_state": {
        "phase": MarriagePhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _verify(s): return transition_to_inputs_verified(s)
def _lower(s): return transition_to_chassis_lowered(s)
def _cab(s): return transition_to_cab_dropped(s)
def _powertrain(s): return transition_to_powertrain_mounted(s)
def _harness(s): return transition_to_harness_connected(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("verify", _verify)
_g.add_node("lower", _lower)
_g.add_node("cab", _cab)
_g.add_node("powertrain", _powertrain)
_g.add_node("harness", _harness)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "verify")
_g.add_edge("verify", "lower")
_g.add_edge("lower", "cab")
_g.add_edge("cab", "powertrain")
_g.add_edge("powertrain", "harness")
_g.add_edge("harness", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
