"""
Commissioning state machine.

Per ADR-2605250715 §2 (Phase 5 cadence): final systems test, defect walkdown, waste log.
6-node LangGraph with final project sign-off (≥2 robot + human witness).

States:
  INIT → FINAL_SYSTEMS_TEST → DEFECT_WALKDOWN → WASTE_INVENTORY
       → SIGN_OFF → COMPLETE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CommissioningPhase(Enum):
    """Phase progression in commissioning."""
    INIT = "init"
    SYSTEMS_TESTED = "systems_tested"
    DEFECTS_IDENTIFIED = "defects_identified"
    WASTE_LOGGED = "waste_logged"
    SIGNED_OFF = "signed_off"
    COMPLETE = "complete"


@dataclass
class CommissioningState:
    """State snapshot for LangGraph node."""
    phase: CommissioningPhase
    projectId: str
    completionPct: int  # 0–100
    systemsTestResults: dict[str, Any] | None = None
    defectWalkdown: dict[str, Any] | None = None
    wasteInventory: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None
    punchList: list[str] | None = None
    photoCid: str | None = None


def transition_to_systems_tested(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → SYSTEMS_TESTED: HVAC, electrical, plumbing verification."""
    cs = CommissioningState(**state.get("commissioning_state", {}))

    mock_tests = {
        "hvac_airflow_cfm": 4450,
        "hvac_spec_cfm": 4500,
        "hvac_test_passed": True,
        "electrical_load_amps": 145,
        "electrical_spec_amps": 200,
        "electrical_test_passed": True,
        "water_pressure_bar": 2.4,
        "water_spec_bar": 2.5,
        "water_test_passed": True,
        "gas_odor_detection": False,
        "gas_test_passed": True,
    }

    cs.phase = CommissioningPhase.SYSTEMS_TESTED
    cs.systemsTestResults = mock_tests
    cs.completionPct = 25

    return {"commissioning_state": cs.__dict__, "next_node": "walkdown"}


def transition_to_defect_walkdown(state: dict[str, Any]) -> dict[str, Any]:
    """SYSTEMS_TESTED → DEFECTS_IDENTIFIED: Photo survey + punch-list."""
    cs = CommissioningState(**state.get("commissioning_state", {}))

    mock_defects = {
        "cracks_foundation": 0,
        "cracks_drywall": 2,
        "paint_blemishes": 1,
        "trim_gaps_mm": 3,  # spec ≤5mm
        "door_operation": "smooth",
        "window_operation": "smooth",
        "hardware_finish": "acceptable",
    }

    punch_list = [
        "Fill 2 small drywall cracks with spackle and sand",
        "Touch up 1 paint blemish in bedroom",
    ]

    cs.phase = CommissioningPhase.DEFECTS_IDENTIFIED
    cs.defectWalkdown = mock_defects
    cs.punchList = punch_list
    cs.completionPct = 50

    return {"commissioning_state": cs.__dict__, "next_node": "waste"}


def transition_to_waste_inventory(state: dict[str, Any]) -> dict[str, Any]:
    """DEFECTS_IDENTIFIED → WASTE_LOGGED: Material waste categorization."""
    cs = CommissioningState(**state.get("commissioning_state", {}))

    mock_waste = {
        "drywall_scrap_kg": 240,
        "drywall_reused_pct": 85,
        "drywall_landfill_pct": 15,
        "metal_scrap_kg": 85,
        "metal_recycled_pct": 95,
        "metal_landfill_pct": 5,
        "wood_scrap_kg": 120,
        "wood_reused_pct": 60,
        "wood_chipped_pct": 30,
        "wood_landfill_pct": 10,
        "hazardous_waste_kg": 5,
        "hazardous_disposal_compliant": True,
    }

    cs.phase = CommissioningPhase.WASTE_LOGGED
    cs.wasteInventory = mock_waste
    cs.completionPct = 75

    return {"commissioning_state": cs.__dict__, "next_node": "signoff"}


def transition_to_project_signoff(state: dict[str, Any]) -> dict[str, Any]:
    """WASTE_LOGGED → SIGNED_OFF: Human project manager + ≥2 robot sigs."""
    cs = CommissioningState(**state.get("commissioning_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-3",
            "role": "final_inspector",
            "timestamp": "2026-05-26T18:30:00Z",
            "signature": "zI4jK7lM0nO3pQ..."
        },
        {
            "robotDid": "did:web:etzhayyim.com:giemon-unit-1",
            "role": "site_supervisor",
            "timestamp": "2026-05-26T18:30:05Z",
            "signature": "rS6tU9vW2xY5zA..."
        }
    ]

    cs.robotSignatures = mock_sigs
    cs.phase = CommissioningPhase.SIGNED_OFF
    cs.completionPct = 95

    return {"commissioning_state": cs.__dict__, "next_node": "emit"}


def emit_project_closure_record(state: dict[str, Any]) -> dict[str, Any]:
    """SIGNED_OFF → COMPLETE: Emit projectClosure record to MST."""
    cs = CommissioningState(**state.get("commissioning_state", {}))

    record = {
        "projectId": cs.projectId,
        "phase": "commissioning",
        "completionPct": 100,
        "closureDate": "2026-05-26T18:30:30Z",
        "systemsTestResults": cs.systemsTestResults,
        "punchList": cs.punchList,
        "wasteInventory": cs.wasteInventory,
        "attestingRobots": [
            {
                "robotDid": sig["robotDid"],
                "role": sig["role"],
                "timestamp": sig["timestamp"],
                "signature": sig["signature"]
            }
            for sig in (cs.robotSignatures or [])
        ],
    }

    cs.phase = CommissioningPhase.COMPLETE
    cs.completionPct = 100

    return {
        "commissioning_state": cs.__dict__,
        "project_closure_record": record,
        "next_node": "end"
    }
