"""PermitSubmissionCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Constants & State Machine (Mocked from .state_machine) ---

class PermitPhase(Enum):
    INIT = "init"
    JURISDICTION_IDENTIFIED = "jurisdiction_identified"
    TEMPLATE_SELECTED = "template_selected"
    APPLICATION_PREPARED = "application_prepared"
    SUBMITTED = "submitted"

@dataclass
class PermitState:
    phase: PermitPhase
    projectId: str
    completionPct: int
    jurisdiction: str | None = None
    buildingType: str | None = None
    siteLocation: dict[str, Any] | None = None
    applicationData: dict[str, Any] | None = None
    permitApplicationId: str | None = None
    submissionTimestamp: str | None = None

def transition_to_jurisdiction_identified(state: dict[str, Any]) -> dict[str, Any]:
    ps = PermitState(**state.get("permit_state", {}))
    mock_jurisdiction = {
        "jurisdiction_type": "Japan",
        "prefecture": "Tokyo",
    }
    ps.phase = PermitPhase.JURISDICTION_IDENTIFIED
    ps.jurisdiction = "Japan-Tokyo"
    ps.siteLocation = mock_jurisdiction
    ps.completionPct = 20
    return {"permit_state": ps.__dict__, "next_node": "template"}

def transition_to_template_selected(state: dict[str, Any]) -> dict[str, Any]:
    ps = PermitState(**state.get("permit_state", {}))
    mock_template = {
        "template_id": "japan-tokyo-residential-2026",
        "building_type_enum": ["residential", "commercial"],
        "required_forms": ["Form1", "Form2"],
    }
    ps.phase = PermitPhase.TEMPLATE_SELECTED
    ps.buildingType = "residential"
    ps.applicationData = mock_template
    ps.completionPct = 40
    return {"permit_state": ps.__dict__, "next_node": "prepare"}

def transition_to_application_prepared(state: dict[str, Any]) -> dict[str, Any]:
    ps = PermitState(**state.get("permit_state", {}))
    mock_application = {
        "applicant_name": "Developer",
        "site_address": "Tokyo",
        "gfa_m2": 2400,
    }
    ps.phase = PermitPhase.APPLICATION_PREPARED
    ps.applicationData = {**(ps.applicationData or {}), **mock_application}
    ps.completionPct = 70
    return {"permit_state": ps.__dict__, "next_node": "submit"}

def transition_to_submitted(state: dict[str, Any]) -> dict[str, Any]:
    ps = PermitState(**state.get("permit_state", {}))
    mock_submission = {
        "permitApplicationId": f"TOKYO-2026-{ps.projectId[-8:]}",
        "submissionDate": "2026-05-26T10:00:00Z",
        "status": "under_review",
    }
    ps.phase = PermitPhase.SUBMITTED
    ps.permitApplicationId = mock_submission["permitApplicationId"]
    ps.submissionTimestamp = mock_submission["submissionDate"]
    ps.applicationData = {**(ps.applicationData or {}), **mock_submission}
    ps.completionPct = 100
    return {
        "permit_state": ps.__dict__,
        "permit_application_record": {
            "projectId": ps.projectId,
            "permitApplicationId": ps.permitApplicationId,
        },
        "next_node": "end"
    }

# --- Node Functions ---

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
    return transition_to_jurisdiction_identified(state)

def _template_selected(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_template_selected(state)

def _application_prepared(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_application_prepared(state)

def _submitted(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_submitted(state)

# --- Graph Construction ---

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
