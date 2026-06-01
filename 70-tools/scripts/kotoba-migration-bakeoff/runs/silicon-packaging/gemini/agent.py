"""Packaging cell port to Kotoba WASM."""

from __future__ import annotations
from typing import Any
import enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state machine
class PackagingPhase(enum.Enum):
    INIT = "init"
    DIE_ATTACHED = "die_attached"
    WIRE_BONDING_COMPLETE = "wire_bonding_complete"
    ENCAPSULATION_COMPLETE = "encapsulation_complete"
    PACKAGE_TESTED = "package_tested"

def transition_to_die_attached(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("packaging_state", {}).copy()
    s.update({"phase": PackagingPhase.DIE_ATTACHED.value, "completionPct": 25})
    return {"packaging_state": s}

def transition_to_wire_bonding_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("packaging_state", {}).copy()
    s.update({"phase": PackagingPhase.WIRE_BONDING_COMPLETE.value, "completionPct": 50})
    return {"packaging_state": s}

def transition_to_encapsulation_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("packaging_state", {}).copy()
    s.update({"phase": PackagingPhase.ENCAPSULATION_COMPLETE.value, "completionPct": 75})
    return {"packaging_state": s}

def transition_to_package_tested(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("packaging_state", {}).copy()
    s.update({"phase": PackagingPhase.PACKAGE_TESTED.value, "completionPct": 100})
    return {"packaging_state": s}

# Node functions
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "packaging_state": {
            "phase": PackagingPhase.INIT.value,
            "packageId": state.get("packageId", "PKG-7NM-2026-0001"),
            "completionPct": 0,
        }
    }

def _attach_die(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_die_attached(state)

def _wire_bond(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_wire_bonding_complete(state)

def _encapsulate(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_encapsulation_complete(state)

def _final_test(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_package_tested(state)

# Graph builder
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("attach_die", _attach_die)
_g.add_node("wire_bond", _wire_bond)
_g.add_node("encapsulate", _encapsulate)
_g.add_node("final_test", _final_test)

_g.add_edge(START, "init")
_g.add_edge("init", "attach_die")
_g.add_edge("attach_die", "wire_bond")
_g.add_edge("wire_bond", "encapsulate")
_g.add_edge("encapsulate", "final_test")
_g.add_edge("final_test", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
