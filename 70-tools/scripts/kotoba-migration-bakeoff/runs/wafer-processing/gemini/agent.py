"""agent — WaferProcessingCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any, TypedDict
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state_machine.py
class WaferPhase(Enum):
    INIT = "init"
    DEPOSITION = "deposition"
    ETCH = "etch"
    IMPLANT = "implant"
    CMP = "cmp"
    VERIFIED = "verified"

def transition_to_deposition_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = state.get("wafer_state", {})
    return {"wafer_state": {**ws, "phase": WaferPhase.DEPOSITION.value, "completionPct": 20}}

def transition_to_etching_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = state.get("wafer_state", {})
    return {"wafer_state": {**ws, "phase": WaferPhase.ETCH.value, "completionPct": 40}}

def transition_to_implantation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = state.get("wafer_state", {})
    return {"wafer_state": {**ws, "phase": WaferPhase.IMPLANT.value, "completionPct": 60}}

def transition_to_cmp_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = state.get("wafer_state", {})
    return {"wafer_state": {**ws, "phase": WaferPhase.CMP.value, "completionPct": 80}}

def transition_to_wafer_verified(state: dict[str, Any]) -> dict[str, Any]:
    ws = state.get("wafer_state", {})
    return {"wafer_state": {**ws, "phase": WaferPhase.VERIFIED.value, "completionPct": 100}}

class WaferStateDict(TypedDict, total=False):
    lotId: str
    wafer_state: dict[str, Any]

def _initialize_state(state: WaferStateDict) -> WaferStateDict:
    return {
        "wafer_state": {
            "phase": WaferPhase.INIT.value,
            "lotId": state.get("lotId", "LOT-7NM-2026-0001"),
            "completionPct": 0,
        }
    }

def _deposition(state: WaferStateDict) -> WaferStateDict:
    return transition_to_deposition_complete(state)

def _etch(state: WaferStateDict) -> WaferStateDict:
    return transition_to_etching_complete(state)

def _implant(state: WaferStateDict) -> WaferStateDict:
    return transition_to_implantation_complete(state)

def _cmp(state: WaferStateDict) -> WaferStateDict:
    return transition_to_cmp_complete(state)

def _verify_wafer(state: WaferStateDict) -> WaferStateDict:
    return transition_to_wafer_verified(state)

_g = StateGraph(WaferStateDict)
_g.add_node("init", _initialize_state)
_g.add_node("deposition", _deposition)
_g.add_node("etch", _etch)
_g.add_node("implant", _implant)
_g.add_node("cmp", _cmp)
_g.add_node("verify_wafer", _verify_wafer)

_g.add_edge(START, "init")
_g.add_edge("init", "deposition")
_g.add_edge("deposition", "etch")
_g.add_edge("etch", "implant")
_g.add_edge("implant", "cmp")
_g.add_edge("cmp", "verify_wafer")
_g.add_edge("verify_wafer", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
