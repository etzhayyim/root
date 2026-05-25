"""Telemetry logging state machine - ADR-2605242000."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TelemetryPhase(Enum):
    INIT = "init"
    DATA_COLLECTED = "data_collected"
    DATA_PROCESSED = "data_processed"
    RECORDS_VERIFIED = "records_verified"
    LOGGED = "logged"


@dataclass
class TelemetryState:
    phase: TelemetryPhase
    missionId: str
    completionPct: int
    startTime: str | None = None
    endTime: str | None = None
    totalDuration: float | None = None
    telemetryData: dict[str, Any] | None = None
    anomalyReport: dict[str, Any] | None = None
    missionSummary: dict[str, Any] | None = None
    ipfsCid: str | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_data_collected(state: dict[str, Any]) -> dict[str, Any]:
    ts = TelemetryState(**state.get("telemetry_state", {}))

    mock_telemetry = {
        "mission_start": "2026-05-26T10:15:30Z",
        "mission_end": "2026-05-26T10:18:45Z",
        "duration_seconds": 195,
        "total_distance_m": 350,
        "average_speed_ms": 1.18,
        "max_speed_ms": 1.50,
        "battery_consumed_pct": 8,
        "battery_start_pct": 95,
        "battery_end_pct": 87,
        "data_points_collected": 1950,
        "gps_fixes": 195,
        "lidar_scans": 195,
    }

    ts.phase = TelemetryPhase.DATA_COLLECTED
    ts.startTime = "2026-05-26T10:15:30Z"
    ts.endTime = "2026-05-26T10:18:45Z"
    ts.totalDuration = 195.0
    ts.telemetryData = mock_telemetry
    ts.completionPct = 20

    return {"telemetry_state": ts.__dict__, "next_node": "process_data"}


def transition_to_data_processed(state: dict[str, Any]) -> dict[str, Any]:
    ts = TelemetryState(**state.get("telemetry_state", {}))

    mock_processed = {
        "valid_gps_fixes": 193,
        "gps_fix_rate_pct": 98.9,
        "lidar_scan_quality": "excellent",
        "data_corruption_detected": False,
        "outlier_removal_applied": True,
        "outliers_removed": 5,
        "smoothing_filter": "kalman",
        "processing_duration_s": 2.3,
    }

    ts.phase = TelemetryPhase.DATA_PROCESSED
    ts.telemetryData = {**(ts.telemetryData or {}), **mock_processed}
    ts.completionPct = 45

    return {"telemetry_state": ts.__dict__, "next_node": "verify_records"}


def transition_to_records_verified(state: dict[str, Any]) -> dict[str, Any]:
    ts = TelemetryState(**state.get("telemetry_state", {}))

    mock_summary = {
        "mission_status": "success",
        "destination_reached": True,
        "payload_delivered": True,
        "safety_incidents": 0,
        "autonomous_decisions_made": 2,
        "human_interventions": 0,
        "total_anomalies_detected": 0,
        "verification_passed": True,
    }

    ts.phase = TelemetryPhase.RECORDS_VERIFIED
    ts.missionSummary = mock_summary
    ts.completionPct = 75

    return {"telemetry_state": ts.__dict__, "next_node": "log_records"}


def transition_to_logged(state: dict[str, Any]) -> dict[str, Any]:
    ts = TelemetryState(**state.get("telemetry_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:wadachi-unit-1",
            "role": "mission_executor",
            "timestamp": "2026-05-26T10:19:45Z",
            "signature": "wW1xX2yY3zZ4aA5b...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:sora-unit-1",
            "role": "telemetry_auditor",
            "timestamp": "2026-05-26T10:19:50Z",
            "signature": "cC6dD7eE8fF9gG0h...",
        },
    ]

    ts.phase = TelemetryPhase.LOGGED
    ts.ipfsCid = "QmWadachiMissionTelemetry20260526101945"
    ts.robotSignatures = mock_sigs
    ts.completionPct = 100

    return {
        "telemetry_state": ts.__dict__,
        "mission_complete_record": {
            "missionId": ts.missionId,
            "startTime": ts.startTime,
            "endTime": ts.endTime,
            "totalDuration": ts.totalDuration,
            "telemetryData": ts.telemetryData,
            "missionSummary": ts.missionSummary,
            "ipfsCid": ts.ipfsCid,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
