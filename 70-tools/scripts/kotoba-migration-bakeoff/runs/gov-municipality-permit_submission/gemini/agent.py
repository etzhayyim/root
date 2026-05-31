"""
PermitSubmissionCell — PermitSubmissionCell compiled to WASM.

Port of `original_cell.py`
onto the WASM-native `kotoba_langgraph` API so it compiles to a kotoba-node component.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mock state_machine.py logic ---
class PermitPhase:
    INIT = "INIT"
    JURISDICTION_IDENTIFIED = "JURISDICTION_IDENTIFIED"
    TEMPLATE_SELECTED = "TEMPLATE_SELECTED"
    APPLICATION_PREPARED = "APPLICATION_PREPARED"
    SUBMITTED = "SUBMITTED"

class PermitState:
    def __init__(self, phase: str, projectId: str, completionPct: int):
        self.phase = phase
        self.projectId = projectId
        self.completionPct = completionPct

def transition_to_jurisdiction_identified(state: dict[str, Any]) -> dict[str, Any]:
    ps = state.get("permit_state", {}).copy()
    ps["phase"] = PermitPhase.JURISDICTION_IDENTIFIED
    ps["completionPct"] = 25
    ps["jurisdictionId"] = "tokyo-minato"
    return {"permit_state": ps, "next_node": "template"}

def transition_to_template_selected(state: dict[str, Any]) -> dict[str, Any]:
    ps = state.get("permit_state", {}).copy()
    ps["phase"] = PermitPhase.TEMPLATE_SELECTED
    ps["completionPct"] = 50
    ps["templateId"] = "standard-permit-v1"
    return {"permit_state": ps, "next_node": "prepare"}

def transition_to_application_prepared(state: dict[str, Any]) -> dict[str, Any]:
    ps = state.get("permit_state", {}).copy()
    ps["phase"] = PermitPhase.APPLICATION_PREPARED
    ps["completionPct"] = 75
    ps["preparedAt"] = "2026-05-31T10:00:00Z"
    return {"permit_state": ps, "next_node": "submit"}

def transition_to_submitted(state: dict[str, Any]) -> dict[str, Any]:
    ps = state.get("permit_state", {}).copy()
    ps["phase"] = PermitPhase.SUBMITTED
    ps["completionPct"] = 100
    ps["permitApplicationId"] = "PERMIT-777"
    return {"permit_state": ps, "next_node": "end"}

# --- Node functions ---
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Initialize permit state from input."""
    projectId = state.get("projectId", "unknown")
    init_state = PermitState(
        phase=PermitPhase.INIT,
        projectId=projectId,
        completionPct=0,
    )
    return {"permit_state": init_state.__dict__, "next_node": "jurisdiction"}

def _jurisdiction_identified(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → JURISDICTION_IDENTIFIED: Lookup jurisdiction."""
    return transition_to_jurisdiction_identified(state)

def _template_selected(state: dict[str, Any]) -> dict[str, Any]:
    """JURISDICTION_IDENTIFIED → TEMPLATE_SELECTED: Match template."""
    return transition_to_template_selected(state)

def _application_prepared(state: dict[str, Any]) -> dict[str, Any]:
    """TEMPLATE_SELECTED → APPLICATION_PREPARED: Fill application."""
    return transition_to_application_prepared(state)

def _submitted(state: dict[str, Any]) -> dict[str, Any]:
    """APPLICATION_PREPARED → SUBMITTED: RPC submit to jurisdiction."""
    return transition_to_submitted(state)

# --- Graph construction ---
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("jurisdiction", _jurisdiction_identified)
_g.add_node("template", _template_selected)
_g.add_node("prepare", _application_prepared)
_g.add_node("submit", _submitted)

_g.add_edge(START, "init")
_g.add_edge("init", "jurisdiction")
_g.add_edge("jurisdiction", "template")
_g.add_edge("template", "prepare")
_g.add_edge("prepare", "submit")
_g.add_edge("submit", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
