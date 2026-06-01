from __future__ import annotations
from typing import Any
import wit_world
from enum import Enum

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocking .state_machine as it's not provided in the environment
class InteriorPhase(Enum):
    INIT = "INIT"
    FLOOR = "FLOOR_INSTALLED"
    SEATING = "SEATING_INSTALLED"
    ACCESSIBILITY = "ACCESSIBILITY_VERIFIED"
    HVAC = "HVAC_INSTALLED"
    PIS = "PIS_CONFIGURED"
    ATTESTATION = "ATTESTATION_EMITTED"

def transition_to_floor_installed(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.FLOOR.value, "completionPct": 20}}

def transition_to_seating_installed(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.SEATING.value, "completionPct": 40}}

def transition_to_accessibility_verified(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.ACCESSIBILITY.value, "completionPct": 60}}

def transition_to_hvac_installed(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.HVAC.value, "completionPct": 80}}

def transition_to_pis_configured(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.PIS.value, "completionPct": 90}}

def transition_to_attestation_emitted(state: dict) -> dict:
    curr = state.get("interior_state", {})
    return {"interior_state": {**curr, "phase": InteriorPhase.ATTESTATION.value, "completionPct": 100}}

# Node functions ported from InteriorHvacCell
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"interior_state": {
        "phase": InteriorPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "carIndex": state.get("carIndex", 0),
        "completionPct": 0,
    }}

def _floor(s): return transition_to_floor_installed(s)
def _seating(s): return transition_to_seating_installed(s)
def _accessibility(s): return transition_to_accessibility_verified(s)
def _hvac(s): return transition_to_hvac_installed(s)
def _pis(s): return transition_to_pis_configured(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("floor", _floor)
_g.add_node("seating", _seating)
_g.add_node("accessibility", _accessibility)
_g.add_node("hvac", _hvac)
_g.add_node("pis", _pis)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "floor")
_g.add_edge("floor", "seating")
_g.add_edge("seating", "accessibility")
_g.add_edge("accessibility", "hvac")
_g.add_edge("hvac", "pis")
_g.add_edge("pis", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
