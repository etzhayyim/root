"""
Structural assembly state machine.

Per ADR-2605250715 §2 (Phase 2 cadence): multi-robot coordination (Giemon shoring + Otete assembly).
8-node LangGraph with Mimi metrology witness quorum (≥2 robot Ed25519 sigs per record).

States (FSM):
  INIT → BIM_LOADED → FOUNDATION_VALIDATED → ROBOT_COORDINATED → EXECUTION
       → METROLOGY_CHECK → WITNESS_WAIT (fixed-point) → COMPLETE
                      (anomaly detected) → HALT
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class StructuralPhase(Enum):
    """Phase progression in structural assembly."""
    INIT = "init"
    BIM_LOADED = "bim_loaded"  # CAD model loaded from vendor-free source
    FOUNDATION_VALIDATED = "foundation_validated"  # Survey data vs design assumptions
    ROBOT_COORDINATED = "robot_coordinated"  # Giemon + Otete trajectory planning
    EXECUTION = "execution"  # Steel connections + concrete pours
    METROLOGY_CHECK = "metrology_check"  # Mimi plumb/level verification
    WITNESS_WAIT = "witness_wait"  # Fixed-point: wait ≥2 robot sigs
    ANOMALY_HALT = "anomaly_halt"  # Critical anomaly detected
    COMPLETE = "complete"


@dataclass
class StructuralState:
    """State snapshot for LangGraph node."""
    phase: StructuralPhase
    projectId: str
    completionPct: int  # 0–100
    bimModelCid: str | None = None  # IPFS CID of FreeCAD .fcstd or STEP
    foundationSurvey: dict[str, Any] | None = None  # From siteAttestation
    designAssumptions: dict[str, Any] | None = None  # Loads, spans, materials from BIM
    robotTrajectory: dict[str, Any] | None = None  # Giemon shoring + Otete assembly plan
    executionMetrics: dict[str, Any] | None = None  # Steel connections, concrete strength, placement dates
    metrologySurvey: dict[str, Any] | None = None  # Plumb/level deviations, as-built CAD
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None  # [{robotDid, timestamp, sig}, ...]
    photoCid: str | None = None  # IPFS CID of assembly photos
    errorMsg: str | None = None


def transition_to_bim_loaded(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → BIM_LOADED: Load CAD from vendor-free source (FreeCAD .fcstd or Open CASCADE STEP)."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Load BIM model (normally external fetch to ~~Autodesk BIM 360~~ → FreeCAD/LibreCAD community repo)
    mock_bim = {
        "model_format": "STEP (ISO 10303-21)",  # Vendor-neutral, ISO standard
        "foundation_footprint_m2": 850,
        "design_loads": {
            "dead_load_kN": 2400,
            "live_load_kN": 600,
            "wind_load_kPa": 1.2,
            "seismic_acceleration": 0.3,
        },
        "structural_elements": {
            "steel_columns": 8,
            "steel_beams": 24,
            "concrete_deck": 1,
            "shoring_posts": 12,
        },
        "material_specs": {
            "steel_grade": "SS400 (Japan) / ASTM A36 (US)",
            "concrete_target_mpa": 30,
            "bolt_grade": "8.8 (ISO 898-1)",
        },
    }

    ss.phase = StructuralPhase.BIM_LOADED
    ss.bimModelCid = "QmBimModelFreeCAD_Step_OpenCascade"
    ss.designAssumptions = mock_bim
    ss.completionPct = 5

    return {"structural_state": ss.__dict__, "next_node": "validate_foundations"}


def transition_to_foundation_validated(state: dict[str, Any]) -> dict[str, Any]:
    """BIM_LOADED → FOUNDATION_VALIDATED: Compare survey vs design assumptions."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Foundation validation (normally RPC to siteAttestation record)
    mock_validation = {
        "survey_bearing_capacity_kpa": 200,
        "design_bearing_requirement_kpa": 180,
        "validation_result": "pass",
        "soil_settlement_estimate_mm": 12,  # differential settlement check
        "settlement_acceptability": "within_limits",
        "shoring_design_matches_survey": True,
        "utility_clearances_verified": True,
    }

    ss.phase = StructuralPhase.FOUNDATION_VALIDATED
    ss.foundationSurvey = mock_validation
    ss.completionPct = 15

    return {"structural_state": ss.__dict__, "next_node": "coordinate_robots"}


def transition_to_robot_coordinated(state: dict[str, Any]) -> dict[str, Any]:
    """FOUNDATION_VALIDATED → ROBOT_COORDINATED: Giemon shoring + Otete assembly trajectory synthesis."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Multi-robot coordination (normally WASM state machine per gate G6 — deterministic, replayable)
    mock_trajectory = {
        "giemon_shoring_plan": {
            "phase_duration_hours": 8,
            "shoring_posts_to_place": 12,
            "post_spacing_m": 3.0,
            "max_post_load_kN": 200,
        },
        "otete_assembly_plan": {
            "steel_connections_phase_1": {
                "column_base_plates": 8,
                "column_beam_connections": 24,
                "torque_spec_nm": [450, 450, 450, 450],  # per connection type
                "estimated_duration_hours": 12,
            },
            "concrete_deck_phase_2": {
                "concrete_volume_m3": 120,
                "placement_rate_m3_per_hour": 10,
                "vibration_frequency_hz": 60,
                "slump_target_mm": 150,
            },
        },
        "safety_constraints": {
            "minimum_shoring_capacity_kN": 250,  # > max design + live load
            "plumb_tolerance_mm": 25,  # per ACI 347
            "level_tolerance_mm": 25,
        },
        "sequence_gates": [
            "foundation_curing_7_days",
            "shoring_placement_complete",
            "column_base_inspection_pass",
            "beam_connections_torqued_verified",
            "concrete_placement_complete",
            "deck_curing_7_days",
        ],
    }

    ss.phase = StructuralPhase.ROBOT_COORDINATED
    ss.robotTrajectory = mock_trajectory
    ss.completionPct = 25

    return {"structural_state": ss.__dict__, "next_node": "execute_assembly"}


def transition_to_execution(state: dict[str, Any]) -> dict[str, Any]:
    """ROBOT_COORDINATED → EXECUTION: Giemon shoring + Otete steel + concrete (mock completion)."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Simulate assembly phases (normally streamed sensor data from Giemon/Otete)
    mock_execution = {
        "shoring_placed": 12,
        "shoring_load_test_passed": True,
        "steel_columns_erected": 8,
        "column_base_connections": {
            "bolted": 8,
            "torque_verified_nm": [450, 450, 450, 450, 450, 450, 450, 450],
            "all_within_spec": True,
        },
        "beam_connections": {
            "total_connections": 24,
            "field_welded": 12,
            "high_strength_bolted": 12,
            "inspection_pass_rate_pct": 100,
        },
        "concrete_placement": {
            "volume_placed_m3": 120,
            "slump_measured_mm": 145,
            "placement_duration_hours": 11.5,
            "vibration_complete": True,
            "air_content_pct": 6.5,
        },
        "photoCid_phases": [
            "QmStructuralPhase1ShoringPhotos",
            "QmStructuralPhase2SteelPhotos",
            "QmStructuralPhase3ConcretePhotos",
        ],
    }

    ss.phase = StructuralPhase.EXECUTION
    ss.executionMetrics = mock_execution
    ss.completionPct = 60
    ss.photoCid = "QmCombined3PhaseStructuralPhotos.tar.gz"

    return {"structural_state": ss.__dict__, "next_node": "metrology_check"}


def transition_to_metrology_check(state: dict[str, Any]) -> dict[str, Any]:
    """EXECUTION → METROLOGY_CHECK or ANOMALY_HALT: Mimi plumb/level verification."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Mimi metrology laser scan (as-built survey)
    mock_metrology = {
        "column_plumb_deviations_mm": [5, 8, 3, 12, 6, 4, 7, 9],  # per column; spec ±25mm
        "max_plumb_deviation_mm": 12,
        "plumb_spec_mm": 25,
        "plumb_pass": True,
        "deck_level_deviations_mm": [-8, 6, -4, 5, 3, -2, 4, -6],  # per point; spec ±25mm
        "max_level_deviation_mm": 8,
        "level_spec_mm": 25,
        "level_pass": True,
        "concrete_surface_flatness_f_number": 20,  # ACI 117 spec F_min = 15, acceptable
        "flatness_pass": True,
        "as_built_cid": "QmAsBuiltPointCloudLAS",
    }

    ss.phase = StructuralPhase.METROLOGY_CHECK
    ss.metrologySurvey = mock_metrology
    ss.completionPct = 75

    # Check for critical deviations
    if mock_metrology["max_plumb_deviation_mm"] > 25 or mock_metrology["max_level_deviation_mm"] > 25:
        ss.phase = StructuralPhase.ANOMALY_HALT
        ss.anomalyFlags = ["plumb_overshoot"] if mock_metrology["max_plumb_deviation_mm"] > 25 else ["level_overshoot"]
        ss.errorMsg = f"Metrology out of spec: plumb {mock_metrology['max_plumb_deviation_mm']}mm, level {mock_metrology['max_level_deviation_mm']}mm"
        return {"structural_state": ss.__dict__, "next_node": "halt"}

    return {"structural_state": ss.__dict__, "next_node": "witness"}


def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    """METROLOGY_CHECK → WITNESS_WAIT (fixed-point): Collect ≥2 robot Ed25519 signatures."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Mock: Giemon + Otete witness attestation
    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:giemon-unit-1",
            "role": "shoring_executor",
            "timestamp": "2026-05-26T14:30:15Z",
            "signature": "aBc9xY2zQ7mN5pK..."  # base64 Ed25519 sig
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-2",
            "role": "assembly_executor",
            "timestamp": "2026-05-26T14:30:20Z",
            "signature": "xL9zN4bR6jD8fG..."  # base64 Ed25519 sig
        },
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-3",
            "role": "metrology_witness",
            "timestamp": "2026-05-26T14:30:25Z",
            "signature": "mP2rT5vW8aB3cH..."  # base64 Ed25519 sig
        }
    ]

    ss.robotSignatures = mock_sigs
    ss.phase = StructuralPhase.WITNESS_WAIT
    ss.completionPct = 85

    return {"structural_state": ss.__dict__, "next_node": "emit_record"}


def emit_structural_auth_record(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT → COMPLETE: Emit structuralAuthRecord to MST."""
    ss = StructuralState(**state.get("structural_state", {}))

    # Build record to write to MST
    record = {
        "projectId": ss.projectId,
        "phase": "structural_assembly",
        "completionPct": ss.completionPct,
        "recordedDate": "2026-05-26T14:31:00Z",
        "photoCid": ss.photoCid,
        "asBuiltCid": ss.metrologySurvey["as_built_cid"] if ss.metrologySurvey else None,
        "metrologyResults": ss.metrologySurvey,
        "executionSummary": ss.executionMetrics,
        "anomalyFlags": ss.anomalyFlags or [],
        "attestingRobots": [
            {
                "robotDid": sig["robotDid"],
                "role": sig["role"],
                "timestamp": sig["timestamp"],
                "signature": sig["signature"]
            }
            for sig in (ss.robotSignatures or [])
        ],
    }

    ss.phase = StructuralPhase.COMPLETE
    ss.completionPct = 100

    return {
        "structural_state": ss.__dict__,
        "structural_auth_record": record,
        "next_node": "end"
    }


def halt_on_metrology_anomaly(state: dict[str, Any]) -> dict[str, Any]:
    """ANOMALY_HALT: Halt assembly, escalate to human engineer."""
    ss = StructuralState(**state.get("structural_state", {}))

    alert_record = {
        "event": "structural_halt",
        "reason": "metrology_anomaly",
        "anomalies": ss.anomalyFlags,
        "timestamp": "2026-05-26T14:30:40Z",
        "escalation": "human_structural_engineer_review_required",
        "corrective_action": "Shoring load increase or column re-plumb required"
    }

    return {
        "structural_state": ss.__dict__,
        "alert_record": alert_record,
        "next_node": "end"
    }
