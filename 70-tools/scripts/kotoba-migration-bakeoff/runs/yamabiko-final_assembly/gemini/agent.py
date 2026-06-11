"""agent.py — FinalAssemblyCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocks for state_machine
class FinalPhase(Enum):
    INIT = "init"
    INPUTS_VERIFIED = "inputs_verified"
    BOGIE_CARBODY_MARRIED = "bogie_carbody_married"
    CAB_INTERIOR_INSTALLED = "cab_interior_installed"
    LIVERY_APPLIED = "livery_applied"
    ATTESTATION_EMITTED = "attestation_emitted"

def transition_to_inputs_verified(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("final_state", {})
    return {"final_state": {**fs, "phase": FinalPhase.INPUTS_VERIFIED.value, "completionPct": 20}}

def transition_to_bogie_carbody_married(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("final_state", {})
    return {"final_state": {**fs, "phase": FinalPhase.BOGIE_CARBODY_MARRIED.value, "completionPct": 40}}

def transition_to_cab_interior_installed(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("final_state", {})
    return {"final_state": {**fs, "phase": FinalPhase.CAB_INTERIOR_INSTALLED.value, "completionPct": 60}}

def transition_to_livery_applied(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("final_state", {})
    return {"final_state": {**fs, "phase": FinalPhase.LIVERY_APPLIED.value, "completionPct": 80}}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("final_state", {})
    return {"final_state": {**fs, "phase": FinalPhase.ATTESTATION_EMITTED.value, "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"final_state": {
        "phase": FinalPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "completionPct": 0,
    }}

def _verify(s: dict[str, Any]) -> dict[str, Any]: return transition_to_inputs_verified(s)
def _marriage(s: dict[str, Any]) -> dict[str, Any]: return transition_to_bogie_carbody_married(s)
def _cab(s: dict[str, Any]) -> dict[str, Any]: return transition_to_cab_interior_installed(s)
def _livery(s: dict[str, Any]) -> dict[str, Any]: return transition_to_livery_applied(s)
def _attestation(s: dict[str, Any]) -> dict[str, Any]: return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("verify", _verify)
_g.add_node("marriage", _marriage)
_g.add_node("cab", _cab)
_g.add_node("livery", _livery)
_g.add_node("attestation", _attestation)
_g.add_edge(START, "init")
_g.add_edge("init", "verify")
_g.add_edge("verify", "marriage")
_g.add_edge("marriage", "cab")
_g.add_edge("cab", "livery")
_g.add_edge("livery", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
