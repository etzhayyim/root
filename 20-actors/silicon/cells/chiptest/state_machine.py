"""Chip testing state machine - ADR-2605242500."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ChiptestPhase(Enum):
    INIT = "init"
    CONTACT_PROBE_ENGAGED = "contact_probe_engaged"
    PARAMETRIC_TEST_COMPLETE = "parametric_test_complete"
    FUNCTIONAL_TEST_COMPLETE = "functional_test_complete"
    CHIP_GRADED = "chip_graded"


@dataclass
class ChiptestState:
    phase: ChiptestPhase
    dieId: str
    completionPct: int
    probeData: dict[str, Any] | None = None
    parametricResults: dict[str, Any] | None = None
    functionalResults: dict[str, Any] | None = None
    yieldGrade: str | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_contact_probe_engaged(state: dict[str, Any]) -> dict[str, Any]:
    cs = ChiptestState(**state.get("chiptest_state", {}))

    mock_probe = {
        "contact_resistance_ohm": 0.8,
        "probe_temperature_c": 28,
        "contact_force_grams": 450,
        "probe_count_active": 486,
        "probe_card_calibration": "pass",
    }

    cs.phase = ChiptestPhase.CONTACT_PROBE_ENGAGED
    cs.probeData = mock_probe
    cs.completionPct = 20

    return {"chiptest_state": cs.__dict__, "next_node": "parametric_test"}


def transition_to_parametric_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = ChiptestState(**state.get("chiptest_state", {}))

    mock_parametric = {
        "vdd_nominal_v": 0.85,
        "leakage_current_ua": 45,
        "ring_oscillator_freq_ghz": 2.8,
        "threshold_voltage_v": 0.42,
        "gain_v_v": 85,
        "parameters_pass_rate_pct": 99.2,
    }

    cs.phase = ChiptestPhase.PARAMETRIC_TEST_COMPLETE
    cs.parametricResults = mock_parametric
    cs.completionPct = 50

    return {"chiptest_state": cs.__dict__, "next_node": "functional_test"}


def transition_to_functional_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = ChiptestState(**state.get("chiptest_state", {}))

    mock_functional = {
        "test_pattern": "LFSR_3500_vectors",
        "test_duration_minutes": 8.5,
        "failure_count": 0,
        "functional_pass_rate_pct": 100.0,
        "speed_grade": "A",
        "power_dissipation_mw": 125,
    }

    cs.phase = ChiptestPhase.FUNCTIONAL_TEST_COMPLETE
    cs.functionalResults = mock_functional
    cs.completionPct = 75

    return {"chiptest_state": cs.__dict__, "next_node": "grade_chip"}


def transition_to_chip_graded(state: dict[str, Any]) -> dict[str, Any]:
    cs = ChiptestState(**state.get("chiptest_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-3",
            "role": "test_equipment_controller",
            "timestamp": "2026-05-26T16:20:15Z",
            "signature": "jJ1kK2lL3mM4nN5o...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-4",
            "role": "test_handler",
            "timestamp": "2026-05-26T16:20:20Z",
            "signature": "pP6qQ7rR8sS9tT0u...",
        },
    ]

    cs.phase = ChiptestPhase.CHIP_GRADED
    cs.yieldGrade = "A"
    cs.robotSignatures = mock_sigs
    cs.completionPct = 100

    return {
        "chiptest_state": cs.__dict__,
        "chiptest_record": {
            "dieId": cs.dieId,
            "parametricResults": cs.parametricResults,
            "functionalResults": cs.functionalResults,
            "yieldGrade": cs.yieldGrade,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
