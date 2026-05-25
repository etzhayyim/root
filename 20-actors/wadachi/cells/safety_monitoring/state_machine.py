"""Safety monitoring state machine - ADR-2605242000."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SafetyPhase(Enum):
    INIT = "init"
    SENSORS_CHECKED = "sensors_checked"
    HAZARDS_ASSESSED = "hazards_assessed"
    SAFETY_PROTOCOL_SET = "safety_protocol_set"
    SAFETY_VERIFIED = "safety_verified"


@dataclass
class SafetyState:
    phase: SafetyPhase
    missionId: str
    completionPct: int
    sensorStatus: dict[str, Any] | None = None
    hazardAssessment: dict[str, Any] | None = None
    safetyProtocol: dict[str, Any] | None = None
    emergencyStops: list[dict[str, Any]] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_sensors_checked(state: dict[str, Any]) -> dict[str, Any]:
    ss = SafetyState(**state.get("safety_state", {}))

    mock_sensors = {
        "gps_status": "rtk_fixed",
        "lidar_operational": True,
        "imu_calibrated": True,
        "camera_working": True,
        "battery_healthy": True,
        "communication_rssi_dbm": -65,
    }

    ss.phase = SafetyPhase.SENSORS_CHECKED
    ss.sensorStatus = mock_sensors
    ss.completionPct = 20

    return {"safety_state": ss.__dict__, "next_node": "assess_hazards"}


def transition_to_hazards_assessed(state: dict[str, Any]) -> dict[str, Any]:
    ss = SafetyState(**state.get("safety_state", {}))

    mock_hazards = {
        "weather_condition": "clear",
        "visibility_m": 100,
        "road_surface_condition": "dry",
        "pedestrian_density": "low",
        "active_construction_nearby": True,
        "speed_limit_kmh": 10,
        "overall_risk_level": "medium",
    }

    ss.phase = SafetyPhase.HAZARDS_ASSESSED
    ss.hazardAssessment = mock_hazards
    ss.completionPct = 45

    return {"safety_state": ss.__dict__, "next_node": "set_protocol"}


def transition_to_safety_protocol_set(state: dict[str, Any]) -> dict[str, Any]:
    ss = SafetyState(**state.get("safety_state", {}))

    mock_protocol = {
        "max_speed_ms": 1.5,
        "minimum_stopping_distance_m": 3.0,
        "obstacle_detection_radius_m": 8,
        "emergency_stop_enabled": True,
        "geofence_enforcement": True,
        "communication_heartbeat_hz": 10,
        "manual_override_enabled": False,
    }

    mock_estops = [
        {
            "type": "lidar_proximity",
            "threshold_m": 0.5,
            "action": "immediate_halt",
        },
        {
            "type": "rtk_signal_loss",
            "threshold_s": 2,
            "action": "return_to_origin",
        },
        {
            "type": "battery_critical",
            "threshold_pct": 10,
            "action": "return_to_origin",
        },
    ]

    ss.phase = SafetyPhase.SAFETY_PROTOCOL_SET
    ss.safetyProtocol = mock_protocol
    ss.emergencyStops = mock_estops
    ss.completionPct = 70

    return {"safety_state": ss.__dict__, "next_node": "witness"}


def transition_to_safety_verified(state: dict[str, Any]) -> dict[str, Any]:
    ss = SafetyState(**state.get("safety_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:wadachi-unit-1",
            "role": "safety_monitor",
            "timestamp": "2026-05-26T10:19:15Z",
            "signature": "kK1lL2mM3nN4oO5p...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:sora-unit-1",
            "role": "safety_auditor",
            "timestamp": "2026-05-26T10:19:20Z",
            "signature": "qQ6rR7sS8tT9uU0v...",
        },
    ]

    ss.phase = SafetyPhase.SAFETY_VERIFIED
    ss.robotSignatures = mock_sigs
    ss.completionPct = 100

    return {
        "safety_state": ss.__dict__,
        "safety_record": {
            "missionId": ss.missionId,
            "sensorStatus": ss.sensorStatus,
            "hazardAssessment": ss.hazardAssessment,
            "safetyProtocol": ss.safetyProtocol,
            "emergencyStops": ss.emergencyStops,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
