"""HullRingFabricationCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocking .state_machine
class MockEnum:
    def __init__(self, value: str):
        self.value = value

class HullRingPhase:
    INIT = MockEnum("init")
    MATERIAL_VERIFIED = MockEnum("material_verified")
    PLATE_ROLLED = MockEnum("plate_rolled")
    RING_FRAME_WELDED = MockEnum("ring_frame_welded")
    ROUNDNESS_QA = MockEnum("roundness_qa")
    ATTESTATION_EMITTED = MockEnum("attestation_emitted")

def transition_to_material_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("hull_ring_state", {})
    return {"hull_ring_state": {**s, "phase": HullRingPhase.MATERIAL_VERIFIED.value, "completionPct": 20}}

def transition_to_plate_rolled(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("hull_ring_state", {})
    return {"hull_ring_state": {**s, "phase": HullRingPhase.PLATE_ROLLED.value, "completionPct": 40}}

def transition_to_ring_frame_welded(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("hull_ring_state", {})
    return {"hull_ring_state": {**s, "phase": HullRingPhase.RING_FRAME_WELDED.value, "completionPct": 60}}

def transition_to_roundness_qa(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("hull_ring_state", {})
    return {"hull_ring_state": {**s, "phase": HullRingPhase.ROUNDNESS_QA.value, "completionPct": 80}}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("hull_ring_state", {})
    return {"hull_ring_state": {**s, "phase": HullRingPhase.ATTESTATION_EMITTED.value, "completionPct": 100}}

# Node functions
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "hull_ring_state": {
            "phase": HullRingPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "ringIndex": state.get("ringIndex", 0),
            "completionPct": 0,
        }
    }

def _verify_material(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_material_verified(state)

def _rolling(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_plate_rolled(state)

def _ring_weld(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_ring_frame_welded(state)

def _roundness_qa(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_roundness_qa(state)

def _attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_attestation_emitted(state)

# Graph Builder
_g = StateGraph(dict)
_g.add_node("init", _initialize_state)
_g.add_node("verify_material", _verify_material)
_g.add_node("rolling", _rolling)
_g.add_node("ring_weld", _ring_weld)
_g.add_node("roundness_qa", _roundness_qa)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "verify_material")
_g.add_edge("verify_material", "rolling")
_g.add_edge("rolling", "ring_weld")
_g.add_edge("ring_weld", "roundness_qa")
_g.add_edge("roundness_qa", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
