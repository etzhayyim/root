"""
Foundation excavation state machine.

Per ADR-2605250715 §3 (Phase 1 cadence): super-step checkpointer at 1–10 Hz.
8-node LangGraph with witness quorum (≥2 robot Ed25519 sigs per progress record).

States (FSM):
  INIT → SURVEY → PLANNING → EXECUTION → WITNESS_WAIT (fixed-point) → PROGRESS_RECORD → COMPLETE
                                            (anomaly detected) → HALT

Each state transition = 1 super-step (Giemon work-order).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import json


class FoundationPhase(Enum):
    """Phase progression in foundation excavation."""
    INIT = "init"
    SURVEY = "survey"  # Load site plan + soil auth
    PLANNING = "planning"  # Giemon trajectory synthesis
    EXECUTION = "execution"  # Giemon arm active excavation
    WITNESS_WAIT = "witness_wait"  # Fixed-point: wait ≥2 robot sigs
    ANOMALY_HALT = "anomaly_halt"  # Critical anomaly detected
    PROGRESS_RECORD = "progress_record"  # Emit record to MST
    COMPLETE = "complete"


@dataclass
class FoundationState:
    """State snapshot for LangGraph node."""
    phase: FoundationPhase
    siteId: str
    completionPct: int  # 0–100
    surveyData: dict[str, Any] | None = None
    excavationPlan: dict[str, Any] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None  # [{robotDid, timestamp, sig}, ...]
    photoCid: str | None = None  # IPFS CID of phase photos
    depthMapCid: str | None = None  # IPFS CID of depth map
    errorMsg: str | None = None


def transition_to_survey(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → SURVEY: Load site plan + soil classification from municipal DB."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # Mock: Load site plan (normally external RPC to municipal DB)
    mock_survey = {
        "site_coordinates": {"lat": 35.6762, "lon": 139.7674},
        "soil_classification": "N_value_20_clay",  # USDA soil type
        "existing_utilities": ["electrical_primary_3phase", "water_main_50mm", "gas_medium_pressure"],
        "hazards": ["power_line_20kv_northeast", "old_fuel_tank_subsurface"],
        "estimated_volume_m3": 1200,
    }

    fs.phase = FoundationPhase.SURVEY
    fs.surveyData = mock_survey
    fs.completionPct = 10

    return {"foundation_state": fs.__dict__, "next_node": "planning"}


def transition_to_planning(state: dict[str, Any]) -> dict[str, Any]:
    """SURVEY → PLANNING: Giemon trajectory synthesis + volume estimate."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # Mock: Generate Giemon arm trajectory (normally WASM state-machine)
    # Key: deterministic + replayable per gate G6
    mock_plan = {
        "giemon_trajectory": {
            "num_passes": 5,
            "pass_duration_seconds": [1200, 1200, 1200, 1200, 900],
            "arm_speed_mm_per_sec": 50,
            "max_depth_mm": 1200,
            "bucket_capacity_m3": 0.15,
            "estimated_completion_hours": (5 * 1200) / 3600,
        },
        "safety_zones": [
            {"type": "utilities_buffer", "distance_mm": 2000, "direction": "north"},
            {"type": "power_line_buffer", "distance_mm": 5000, "direction": "northeast"},
        ],
        "volume_check_against_survey": {"survey_m3": 1200, "plan_m3": 1200, "match": True},
    }

    fs.phase = FoundationPhase.PLANNING
    fs.excavationPlan = mock_plan
    fs.completionPct = 25

    return {"foundation_state": fs.__dict__, "next_node": "execution"}


def transition_to_execution(state: dict[str, Any]) -> dict[str, Any]:
    """PLANNING → EXECUTION: Giemon active excavation (mock 5 passes)."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # Simulate 5 excavation passes (each = 1 work-order)
    # In real system: send work-order to Giemon firmware, stream sensor data (depth, accelerometer, etc.)
    mock_execution = {
        "passes_completed": 5,
        "sensor_telemetry": {
            "final_depth_mm": 1195,
            "final_surface_area_m2": 850,
            "bucket_cycles": 187,
            "avg_arm_torque_nm": [120, 130, 125, 140, 135],
            "vibration_acceptable": True,
        },
        "photoCid_passes": [
            "QmSensorPass1PhotoTar",
            "QmSensorPass2PhotoTar",
            "QmSensorPass3PhotoTar",
            "QmSensorPass4PhotoTar",
            "QmSensorPass5PhotoTar",
        ],
        "depthMapCid": "QmDepthMap32bitFloatGeoTIFF",
    }

    fs.phase = FoundationPhase.EXECUTION
    fs.completionPct = 75
    fs.photoCid = "QmCombined5PassPhotos.tar.gz"
    fs.depthMapCid = mock_execution["depthMapCid"]

    return {"foundation_state": fs.__dict__, "next_node": "anomaly_check"}


def check_for_anomalies(state: dict[str, Any]) -> dict[str, Any]:
    """EXECUTION → ANOMALY_HALT or WITNESS_WAIT: Scan anomaly flags."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # Mock: Scan sensor data for anomalies (arm torque spike, vibration, depth overshoot, etc.)
    mock_anomalies = []

    # Example: depth overshoot check
    final_depth = 1195
    spec_depth = 1200
    overshoot_mm = spec_depth - final_depth
    if overshoot_mm < -50:  # >50mm overshoot
        mock_anomalies.append(f"depth_overshoot_{overshoot_mm}mm")

    # Example: vibration check
    # (In real: RMS acceleration on accelerometer)
    max_vibration_g = 2.1
    if max_vibration_g > 2.0:
        mock_anomalies.append(f"vibration_spike_{max_vibration_g}g")

    fs.anomalyFlags = mock_anomalies if mock_anomalies else []

    if len(mock_anomalies) > 0:
        fs.phase = FoundationPhase.ANOMALY_HALT
        fs.errorMsg = f"Critical anomalies detected: {'; '.join(mock_anomalies)}"
        return {"foundation_state": fs.__dict__, "next_node": "halt"}

    fs.phase = FoundationPhase.WITNESS_WAIT
    fs.completionPct = 80
    return {"foundation_state": fs.__dict__, "next_node": "witness_attestation"}


def wait_for_witness_sigs(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT (fixed-point): Collect ≥2 robot Ed25519 signatures.

    In real system: This blocks until swarm broadcast (ADR-2605191524)
    delivers attestations from Otete + Mimi (or other robots).
    Mock: Assume sigs arrive immediately.
    """
    fs = FoundationState(**state.get("foundation_state", {}))

    # Mock: Pretend Giemon + Otete signed this progress record
    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:giemon-unit-1",
            "timestamp": "2026-05-26T09:45:32Z",
            "signature": "gSP5y7w8vK2mQ..." # base64 Ed25519 sig
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-2",
            "timestamp": "2026-05-26T09:45:35Z",
            "signature": "xL9zN4bR6jD..." # base64 Ed25519 sig
        }
    ]

    fs.robotSignatures = mock_sigs
    fs.phase = FoundationPhase.PROGRESS_RECORD
    fs.completionPct = 90

    return {"foundation_state": fs.__dict__, "next_node": "emit_record"}


def emit_progress_record(state: dict[str, Any]) -> dict[str, Any]:
    """PROGRESS_RECORD: Emit constructionProgressRecord to MST."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # Build record that will be written to MST
    record = {
        "projectId": fs.siteId,
        "phase": "foundation_excavation",
        "completionPct": fs.completionPct,
        "recordedDate": "2026-05-26T09:46:00Z",
        "photoCid": fs.photoCid,
        "depthMapCid": fs.depthMapCid,
        "anomalyFlags": fs.anomalyFlags or [],
        "attestingRobots": [sig["robotDid"] for sig in (fs.robotSignatures or [])],
    }

    fs.phase = FoundationPhase.COMPLETE

    return {
        "foundation_state": fs.__dict__,
        "constructed_record": record,
        "next_node": "end"
    }


def halt_on_anomaly(state: dict[str, Any]) -> dict[str, Any]:
    """ANOMALY_HALT: Halt execution, emit alert, escalate to human."""
    fs = FoundationState(**state.get("foundation_state", {}))

    # In real system: send alert, halt Giemon firmware, wait for human intervention
    alert_record = {
        "event": "construction_halt",
        "reason": "anomaly_detected",
        "anomalies": fs.anomalyFlags,
        "timestamp": "2026-05-26T09:45:40Z",
        "escalation": "human_review_required"
    }

    return {
        "foundation_state": fs.__dict__,
        "alert_record": alert_record,
        "next_node": "end"
    }
