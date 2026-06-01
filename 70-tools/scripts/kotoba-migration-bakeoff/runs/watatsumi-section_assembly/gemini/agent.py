"""SectionAssemblyCell port to Kotoba WASM."""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- MOCKS ---

class Phase:
    def __init__(self, value: str):
        self.value = value

class SectionAssemblyPhase:
    INIT = Phase("init")
    RINGS_VERIFIED = Phase("rings_verified")
    RINGS_STACKED = Phase("rings_stacked")
    FRAMES_INSTALLED = Phase("frames_installed")
    PENETRATORS_INSTALLED = Phase("penetrators_installed")
    ATTESTATION_EMITTED = Phase("attestation_emitted")

def transition_to_rings_verified(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("section_assembly_state", {})
    return {"section_assembly_state": {**curr, "phase": SectionAssemblyPhase.RINGS_VERIFIED.value, "completionPct": 20}}

def transition_to_rings_stacked(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("section_assembly_state", {})
    return {"section_assembly_state": {**curr, "phase": SectionAssemblyPhase.RINGS_STACKED.value, "completionPct": 40}}

def transition_to_frames_installed(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("section_assembly_state", {})
    return {"section_assembly_state": {**curr, "phase": SectionAssemblyPhase.FRAMES_INSTALLED.value, "completionPct": 60}}

def transition_to_penetrators_installed(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("section_assembly_state", {})
    return {"section_assembly_state": {**curr, "phase": SectionAssemblyPhase.PENETRATORS_INSTALLED.value, "completionPct": 80}}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    curr = state.get("section_assembly_state", {})
    return {"section_assembly_state": {**curr, "phase": SectionAssemblyPhase.ATTESTATION_EMITTED.value, "completionPct": 100, "attestation": "MOCK_ATTESTATION_HASH"}}

# --- NODES ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_assembly_state": {
            "phase": SectionAssemblyPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "sectionIndex": state.get("sectionIndex", 0),
            "completionPct": 0,
        }
    }

def _verify_rings(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_rings_verified(state)

def _stack(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_rings_stacked(state)

def _frames(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_frames_installed(state)

def _penetrators(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_penetrators_installed(state)

def _attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_attestation_emitted(state)

# --- GRAPH ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("verify_rings", _verify_rings)
_g.add_node("stack", _stack)
_g.add_node("frames", _frames)
_g.add_node("penetrators", _penetrators)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "verify_rings")
_g.add_edge("verify_rings", "stack")
_g.add_edge("stack", "frames")
_g.add_edge("frames", "penetrators")
_g.add_edge("penetrators", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

# --- WIT ---

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
