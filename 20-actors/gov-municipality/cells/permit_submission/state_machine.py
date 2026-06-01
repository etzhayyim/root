"""Permit submission state machine - ADR-2605250800."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    ps.applicationData = {**ps.applicationData, **mock_submission}
    ps.completionPct = 100
    return {
        "permit_state": ps.__dict__,
        "permit_application_record": {
            "projectId": ps.projectId,
            "permitApplicationId": ps.permitApplicationId,
        },
        "next_node": "end"
    }
