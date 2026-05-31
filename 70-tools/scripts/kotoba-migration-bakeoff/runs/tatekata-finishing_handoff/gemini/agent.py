from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---

class FinishingPhase:
    INIT = "INIT"
    SURFACES_PREPPED = "SURFACES_PREPPED"
    DRYWALL_COMPLETE = "DRYWALL_COMPLETE"
    PAINT_COMPLETE = "PAINT_COMPLETE"
    TRIM_INSTALLED = "TRIM_INSTALLED"
    WITNESS_WAIT = "WITNESS_WAIT"
    COMPLETE = "COMPLETE"

class FinishingState:
    def __init__(self, phase: str, projectId: str, completionPct: int):
        self.phase = phase
        self.projectId = projectId
        self.completionPct = completionPct

def transition_to_prep_complete(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.SURFACES_PREPPED
    fs["completionPct"] = 20
    return {"finishing_state": fs, "next_node": "drywall"}

def transition_to_drywall_complete(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.DRYWALL_COMPLETE
    fs["completionPct"] = 40
    return {"finishing_state": fs, "next_node": "paint"}

def transition_to_paint_complete(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.PAINT_COMPLETE
    fs["completionPct"] = 60
    return {"finishing_state": fs, "next_node": "trim"}

def transition_to_trim_installed(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.TRIM_INSTALLED
    fs["completionPct"] = 80
    return {"finishing_state": fs, "next_node": "witness"}

def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.WITNESS_WAIT
    fs["completionPct"] = 90
    fs["witness_signatures"] = ["did:robot:giemon-001", "did:robot:tatekata-002"]
    return {"finishing_state": fs, "next_node": "emit"}

def emit_finishing_record(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("finishing_state", {}).copy()
    fs["phase"] = FinishingPhase.COMPLETE
    fs["completionPct"] = 100
    record = {
        "projectId": fs.get("projectId"),
        "status": "MST_VERIFIED",
        "signatures": fs.get("witness_signatures", []),
        "occupancy_clearance": True
    }
    return {"finishing_state": fs, "finishingRecord": record, "next_node": END}

# --- Node Functions ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Initialize finishing state from input."""
    projectId = state.get("projectId", "unknown")
    init_state = FinishingState(
        phase=FinishingPhase.INIT,
        projectId=projectId,
        completionPct=0,
    )
    return {"finishing_state": init_state.__dict__, "next_node": "prep"}

def _prep_surfaces(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → SURFACES_PREPPED: Giemon substrate cleaning."""
    return transition_to_prep_complete(state)

def _drywall_tape_mud(state: dict[str, Any]) -> dict[str, Any]:
    """SURFACES_PREPPED → DRYWALL_COMPLETE: Tape, mud, sand."""
    return transition_to_drywall_complete(state)

def _paint_seal(state: dict[str, Any]) -> dict[str, Any]:
    """DRYWALL_COMPLETE → PAINT_COMPLETE: Primer + finish coats."""
    return transition_to_paint_complete(state)

def _trim_install(state: dict[str, Any]) -> dict[str, Any]:
    """PAINT_COMPLETE → TRIM_INSTALLED: Baseboard, casing, crown."""
    return transition_to_trim_installed(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    """TRIM_INSTALLED → WITNESS_WAIT: Collect ≥2 robot sigs."""
    return transition_to_witness_attestation(state)

def _emit_record(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT → COMPLETE: Emit finishingRecord to MST."""
    return emit_finishing_record(state)

# --- Graph Definition ---

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("prep", _prep_surfaces)
_g.add_node("drywall", _drywall_tape_mud)
_g.add_node("paint", _paint_seal)
_g.add_node("trim", _trim_install)
_g.add_node("witness", _witness_attestation)
_g.add_node("emit", _emit_record)

_g.add_edge(START, "init")
_g.add_edge("init", "prep")
_g.add_edge("prep", "drywall")
_g.add_edge("drywall", "paint")
_g.add_edge("paint", "trim")
_g.add_edge("trim", "witness")
_g.add_edge("witness", "emit")
_g.add_edge("emit", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
