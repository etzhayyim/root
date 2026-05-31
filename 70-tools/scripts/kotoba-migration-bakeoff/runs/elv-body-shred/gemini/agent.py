"""ElvBodyShredCell — ElvBodyShredCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any, TypedDict
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---

class BodyShredPhase:
    INIT = "INIT"
    HULK_LOADED = "HULK_LOADED"
    SHREDDED = "SHREDDED"
    SORTED = "SORTED"
    KANAYAMA_HANDOFF = "KANAYAMA_HANDOFF"
    SILICON_HANDOFF = "SILICON_HANDOFF"
    ATTESTATION_EMITTED = "ATTESTATION_EMITTED"

    def __init__(self, value: str):
        self.value = value

# Mock values as strings for simple implementation
BodyShredPhase.INIT = "INIT"
BodyShredPhase.HULK_LOADED = "HULK_LOADED"
BodyShredPhase.SHREDDED = "SHREDDED"
BodyShredPhase.SORTED = "SORTED"
BodyShredPhase.KANAYAMA_HANDOFF = "KANAYAMA_HANDOFF"
BodyShredPhase.SILICON_HANDOFF = "SILICON_HANDOFF"
BodyShredPhase.ATTESTATION_EMITTED = "ATTESTATION_EMITTED"

def transition_to_hulk_loaded(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.HULK_LOADED
    s["completionPct"] = 10
    return {"body_shred_state": s}

def transition_to_shredded(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.SHREDDED
    s["completionPct"] = 40
    return {"body_shred_state": s}

def transition_to_sorted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.SORTED
    s["completionPct"] = 60
    return {"body_shred_state": s}

def transition_to_kanayama_handoff(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.KANAYAMA_HANDOFF
    s["completionPct"] = 80
    return {"body_shred_state": s}

def transition_to_silicon_handoff(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.SILICON_HANDOFF
    s["completionPct"] = 90
    return {"body_shred_state": s}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("body_shred_state", {}).copy()
    s["phase"] = BodyShredPhase.ATTESTATION_EMITTED
    s["completionPct"] = 100
    return {"body_shred_state": s}

# --- State Definition ---

class ElvBodyShredStateDict(TypedDict, total=False):
    vehicleId: str
    body_shred_state: dict[str, Any]

# --- Node Functions ---

def _initialize_state(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return {
        "body_shred_state": {
            "phase": BodyShredPhase.INIT,
            "vehicleId": state.get("vehicleId", "HODOKI-VEHICLE-0001"),
            "completionPct": 0,
        }
    }

def _load(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_hulk_loaded(state)

def _shred(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_shredded(state)

def _sort(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_sorted(state)

def _kanayama(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_kanayama_handoff(state)

def _silicon(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_silicon_handoff(state)

def _attestation(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return transition_to_attestation_emitted(state)

# --- Graph Construction ---

_g = StateGraph(ElvBodyShredStateDict)
_g.add_node("init", _initialize_state)
_g.add_node("load", _load)
_g.add_node("shred", _shred)
_g.add_node("sort", _sort)
_g.add_node("kanayama", _kanayama)
_g.add_node("silicon", _silicon)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "load")
_g.add_edge("load", "shred")
_g.add_edge("shred", "sort")
_g.add_edge("sort", "kanayama")
_g.add_edge("kanayama", "silicon")
_g.add_edge("silicon", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
