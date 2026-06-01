"""agent.py — MaskLithographyCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocking .state_machine components
MaskState = dict

class MaskPhase(Enum):
    INIT = "init"
    DESIGN_LOADED = "design_loaded"
    PHOTORESIST_APPLIED = "photoresist_applied"
    EXPOSURE_COMPLETE = "exposure_complete"
    DEVELOPMENT_COMPLETE = "development_complete"
    VERIFIED = "verified"

def transition_to_mask_design_loaded(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("mask_state", {})
    return {"mask_state": {**ms, "phase": MaskPhase.DESIGN_LOADED.value, "completionPct": 20}}

def transition_to_photoresist_applied(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("mask_state", {})
    return {"mask_state": {**ms, "phase": MaskPhase.PHOTORESIST_APPLIED.value, "completionPct": 40}}

def transition_to_exposure_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("mask_state", {})
    return {"mask_state": {**ms, "phase": MaskPhase.EXPOSURE_COMPLETE.value, "completionPct": 60}}

def transition_to_development_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("mask_state", {})
    return {"mask_state": {**ms, "phase": MaskPhase.DEVELOPMENT_COMPLETE.value, "completionPct": 80}}

def transition_to_mask_verified(state: dict[str, Any]) -> dict[str, Any]:
    ms = state.get("mask_state", {})
    return {"mask_state": {**ms, "phase": MaskPhase.VERIFIED.value, "completionPct": 100}}

# Node functions (Module-level)
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "mask_state": {
            "phase": MaskPhase.INIT.value,
            "waferId": state.get("waferId", "WAFER-7NM-2026-0001"),
            "completionPct": 0,
        }
    }

def _load_design(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_mask_design_loaded(state)

def _apply_photoresist(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_photoresist_applied(state)

def _exposure(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_exposure_complete(state)

def _develop(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_development_complete(state)

def _verify_mask(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_mask_verified(state)

# Graph builder at MODULE level
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("load_design", _load_design)
_g.add_node("apply_photoresist", _apply_photoresist)
_g.add_node("exposure", _exposure)
_g.add_node("develop", _develop)
_g.add_node("verify_mask", _verify_mask)

_g.add_edge(START, "init")
_g.add_edge("init", "load_design")
_g.add_edge("load_design", "apply_photoresist")
_g.add_edge("apply_photoresist", "exposure")
_g.add_edge("exposure", "develop")
_g.add_edge("develop", "verify_mask")
_g.add_edge("verify_mask", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
