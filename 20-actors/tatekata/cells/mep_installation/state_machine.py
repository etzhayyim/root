"""
MEP installation state machine.

Per ADR-2605250715 §2 (Phase 3 cadence): Otete arm routes ductwork, conduit, piping.
8-node LangGraph with pressure-test witness quorum (≥2 robot Ed25519 sigs).

States (FSM):
  INIT → ROUTE_DUCTWORK → ROUTE_CONDUIT → ROUTE_PIPING → PRESSURE_TEST
       → WITNESS_WAIT (fixed-point) → COMPLETE
                    (test fail) → HALT
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MepPhase(Enum):
    """Phase progression in MEP installation."""
    INIT = "init"
    DUCTWORK_ROUTED = "ductwork_routed"  # HVAC Otete arm trajectory
    CONDUIT_ROUTED = "conduit_routed"  # Electrical Otete arm trajectory
    PIPING_ROUTED = "piping_routed"  # Water/gas Otete arm trajectory
    PRESSURE_TEST = "pressure_test"  # Pneumatic/hydro testing
    WITNESS_WAIT = "witness_wait"  # Fixed-point: wait ≥2 robot sigs
    TEST_FAIL = "test_fail"  # Pressure test anomaly detected
    COMPLETE = "complete"


@dataclass
class MepState:
    """State snapshot for LangGraph node."""
    phase: MepPhase
    projectId: str
    completionPct: int  # 0–100
    hvacPlan: dict[str, Any] | None = None  # Ductwork routing
    electricalPlan: dict[str, Any] | None = None  # Conduit routing
    plumbingPlan: dict[str, Any] | None = None  # Piping routing
    testResults: dict[str, Any] | None = None  # Pressure test data
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None  # [{robotDid, timestamp, sig}, ...]
    photoCid: str | None = None  # IPFS CID of MEP installation photos
    errorMsg: str | None = None


def transition_to_ductwork_routed(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → DUCTWORK_ROUTED: HVAC Otete arm trajectory synthesis."""
    ms = MepState(**state.get("mep_state", {}))

    mock_hvac = {
        "main_trunk_length_m": 180,
        "branch_ducts_count": 12,
        "supply_cfm": 4500,
        "return_cfm": 4000,
        "filter_location": "return_plenum",
        "duct_insulation_r_value": 8,
        "sealed_duct_test_passed": True,
        "leakage_rate_cfm_at_25pa": 45,  # spec ≤50 CFM@25Pa per ASHRAE 90.1
    }

    ms.phase = MepPhase.DUCTWORK_ROUTED
    ms.hvacPlan = mock_hvac
    ms.completionPct = 20

    return {"mep_state": ms.__dict__, "next_node": "route_conduit"}


def transition_to_conduit_routed(state: dict[str, Any]) -> dict[str, Any]:
    """DUCTWORK_ROUTED → CONDUIT_ROUTED: Electrical Otete arm trajectory."""
    ms = MepState(**state.get("mep_state", {}))

    mock_electrical = {
        "main_service_amperage": 200,
        "conduit_total_length_m": 420,
        "wire_pulls_completed": 12,
        "panel_breakers_installed": 24,
        "ground_resistance_ohms": 2.5,  # spec ≤5 ohms per NEC
        "insulation_test_passed": True,
        "hi_pot_test_kv": 1500,
    }

    ms.phase = MepPhase.CONDUIT_ROUTED
    ms.electricalPlan = mock_electrical
    ms.completionPct = 40

    return {"mep_state": ms.__dict__, "next_node": "route_piping"}


def transition_to_piping_routed(state: dict[str, Any]) -> dict[str, Any]:
    """CONDUIT_ROUTED → PIPING_ROUTED: Water/gas Otete arm trajectory."""
    ms = MepState(**state.get("mep_state", {}))

    mock_plumbing = {
        "water_service_size_mm": 25,
        "water_piping_length_m": 210,
        "supply_pressure_bar": 2.5,
        "hot_water_setpoint_c": 60,
        "gas_service_size_mm": 19,
        "gas_piping_fittings_sealed": True,
        "sanitaryDwvPipingLength_m": 180,
        "storm_drainPipingLength_m": 95,
        "trap_priming_devices_installed": True,
    }

    ms.phase = MepPhase.PIPING_ROUTED
    ms.plumbingPlan = mock_plumbing
    ms.completionPct = 60

    return {"mep_state": ms.__dict__, "next_node": "pressure_test"}


def transition_to_pressure_test(state: dict[str, Any]) -> dict[str, Any]:
    """PIPING_ROUTED → PRESSURE_TEST or TEST_FAIL: Hydro/pneumatic testing."""
    ms = MepState(**state.get("mep_state", {}))

    # Mock pressure test results
    mock_test = {
        "water_system_test_psi": 150,
        "water_hold_time_minutes": 30,
        "water_leak_observed_ml": 0,
        "water_test_passed": True,
        "gas_system_test_psi": 10,
        "gas_hold_time_hours": 1,
        "gas_leakage_detected": False,
        "gas_test_passed": True,
        "drain_system_smoke_test_passed": True,
    }

    ms.phase = MepPhase.PRESSURE_TEST
    ms.testResults = mock_test
    ms.completionPct = 75

    # Check for test failures
    if not (mock_test["water_test_passed"] and mock_test["gas_test_passed"] and mock_test["drain_system_smoke_test_passed"]):
        ms.phase = MepPhase.TEST_FAIL
        ms.anomalyFlags = ["pressure_test_failure"]
        ms.errorMsg = "Pressure test failed: water/gas/drain system leakage detected"
        return {"mep_state": ms.__dict__, "next_node": "halt"}

    return {"mep_state": ms.__dict__, "next_node": "witness"}


def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    """PRESSURE_TEST → WITNESS_WAIT: Collect ≥2 robot Ed25519 signatures."""
    ms = MepState(**state.get("mep_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-2",
            "role": "hvac_executor",
            "timestamp": "2026-05-26T16:20:30Z",
            "signature": "pL7mN2qR5uT8vW..."
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-3",
            "role": "electrical_executor",
            "timestamp": "2026-05-26T16:20:35Z",
            "signature": "xK3yZ8aB1cD4eF..."
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-4",
            "role": "plumbing_executor",
            "timestamp": "2026-05-26T16:20:40Z",
            "signature": "gH5iJ9kL2mN3oP..."
        }
    ]

    ms.robotSignatures = mock_sigs
    ms.phase = MepPhase.WITNESS_WAIT
    ms.completionPct = 85

    return {"mep_state": ms.__dict__, "next_node": "emit_record"}


def emit_mep_signoff_record(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT → COMPLETE: Emit mepSignoffRecord to MST."""
    ms = MepState(**state.get("mep_state", {}))

    record = {
        "projectId": ms.projectId,
        "phase": "mep_installation",
        "completionPct": ms.completionPct,
        "recordedDate": "2026-05-26T16:21:00Z",
        "hvacSummary": ms.hvacPlan,
        "electricalSummary": ms.electricalPlan,
        "plumbingSummary": ms.plumbingPlan,
        "testResults": ms.testResults,
        "anomalyFlags": ms.anomalyFlags or [],
        "attestingRobots": [
            {
                "robotDid": sig["robotDid"],
                "role": sig["role"],
                "timestamp": sig["timestamp"],
                "signature": sig["signature"]
            }
            for sig in (ms.robotSignatures or [])
        ],
    }

    ms.phase = MepPhase.COMPLETE
    ms.completionPct = 100

    return {
        "mep_state": ms.__dict__,
        "mep_signoff_record": record,
        "next_node": "end"
    }


def halt_on_test_failure(state: dict[str, Any]) -> dict[str, Any]:
    """TEST_FAIL: Halt MEP, escalate to mechanical/electrical/plumbing contractor."""
    ms = MepState(**state.get("mep_state", {}))

    alert_record = {
        "event": "mep_halt",
        "reason": "pressure_test_failure",
        "anomalies": ms.anomalyFlags,
        "timestamp": "2026-05-26T16:20:50Z",
        "escalation": "contractor_review_required",
        "corrective_action": "Retest after repairs complete"
    }

    return {
        "mep_state": ms.__dict__,
        "alert_record": alert_record,
        "next_node": "end"
    }
