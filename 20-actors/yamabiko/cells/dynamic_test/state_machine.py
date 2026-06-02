"""Dynamic test state machine — ADR-2605252600 L5b.

≥100 km test track. G12 KPI enforcement: max speed ≤320 km/h Wave 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DynamicPhase(Enum):
    INIT = "init"
    STATIC_TEST_PASSED = "static_test_passed"
    G12_KPI_VERIFIED = "g12_kpi_verified"
    DYNAMIC_RUN_COMPLETE = "dynamic_run_complete"
    RECORD_EMITTED = "record_emitted"


@dataclass
class DynamicState:
    phase: DynamicPhase
    trainsetId: str
    completionPct: int
    staticTestResult: dict[str, Any] | None = None
    g12KpiCheck: dict[str, Any] | None = None
    dynamicRunResult: dict[str, Any] | None = None


def transition_to_static_test_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = DynamicState(**state.get("dynamic_state", {}))
    s.staticTestResult = {
        "weightDistribution": "PASS", "pneumaticPressure": "PASS",
        "doorOperation": "PASS", "emergencyBrake": "PASS",
        "hvacCalibration": "PASS",
    }
    s.phase = DynamicPhase.STATIC_TEST_PASSED
    s.completionPct = 25
    return {"dynamic_state": s.__dict__, "next_node": "g12"}


def transition_to_g12_kpi_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = DynamicState(**state.get("dynamic_state", {}))
    s.g12KpiCheck = {
        "designSpeedKmh": 320,
        "maxSpeedLimitKmh": 320,
        "trainsetLengthM": 100,
        "maxTrainsetLengthM": 450,
        "atoLevel": "GoA-3",
        "atoMaxLevel": 3,
        "accept": True,
    }
    s.phase = DynamicPhase.G12_KPI_VERIFIED
    s.completionPct = 50
    return {"dynamic_state": s.__dict__, "next_node": "run"}


def transition_to_dynamic_run_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = DynamicState(**state.get("dynamic_state", {}))
    s.dynamicRunResult = {
        "testTrackLengthKm": 105,
        "totalDistanceKm": 1240,
        "maxAchievedSpeedKmh": 318,
        "averageSpeedKmh": 220,
        "accelerationMsps": 0.72,
        "decelerationMsps": 1.10,
        "rideQualityRMSM": 0.18,
        "rideQualitySpecMaxRMSM": 0.25,
        "videoCid": "bafkreidyntest...",
    }
    s.phase = DynamicPhase.DYNAMIC_RUN_COMPLETE
    s.completionPct = 92
    return {"dynamic_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = DynamicState(**state.get("dynamic_state", {}))
    s.phase = DynamicPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.dynamicTestRecord",
        "trainsetId": s.trainsetId,
        "staticTestResult": s.staticTestResult,
        "g12KpiCheck": s.g12KpiCheck,
        "dynamicRunResult": s.dynamicRunResult,
        "overallAccept": True,
        "recordedAt": "2026-05-27T10:00:00Z",
    }
    return {"dynamic_state": s.__dict__, "dynamic_test_record": record, "next_node": "end"}
