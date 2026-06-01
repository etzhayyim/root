"""Mask lithography state machine - ADR-2605242500."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MaskPhase(Enum):
    INIT = "init"
    MASK_DESIGN_LOADED = "mask_design_loaded"
    PHOTORESIST_APPLIED = "photoresist_applied"
    EXPOSURE_COMPLETE = "exposure_complete"
    DEVELOPMENT_COMPLETE = "development_complete"
    MASK_VERIFIED = "mask_verified"


@dataclass
class MaskState:
    phase: MaskPhase
    waferId: str
    completionPct: int
    designCid: str | None = None
    photoresistData: dict[str, Any] | None = None
    exposureData: dict[str, Any] | None = None
    developmentData: dict[str, Any] | None = None
    metrologyScan: dict[str, Any] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_mask_design_loaded(state: dict[str, Any]) -> dict[str, Any]:
    ms = MaskState(**state.get("mask_state", {}))

    mock_design = {
        "design_file_format": "GDSII",
        "feature_size_nm": 7,
        "layer_count": 8,
        "pattern_density_pct": 62,
        "design_rule_violations": 0,
    }

    ms.phase = MaskPhase.MASK_DESIGN_LOADED
    ms.designCid = "QmMaskDesign7nm20260526"
    ms.completionPct = 15

    return {"mask_state": ms.__dict__, "next_node": "apply_photoresist"}


def transition_to_photoresist_applied(state: dict[str, Any]) -> dict[str, Any]:
    ms = MaskState(**state.get("mask_state", {}))

    mock_resist = {
        "resist_type": "EUV_chemically_amplified",
        "film_thickness_nm": 85,
        "bake_temperature_c": 130,
        "bake_duration_s": 180,
        "coverage_uniformity_pct": 98.5,
    }

    ms.phase = MaskPhase.PHOTORESIST_APPLIED
    ms.photoresistData = mock_resist
    ms.completionPct = 30

    return {"mask_state": ms.__dict__, "next_node": "exposure"}


def transition_to_exposure_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = MaskState(**state.get("mask_state", {}))

    mock_exposure = {
        "light_source": "EUV_13.5nm",
        "exposure_dose_mj_cm2": 24.5,
        "exposure_time_s": 15,
        "focus_offset_nm": 0.8,
        "best_focus_position_nm": 45,
        "dose_uniformity_pct": 97.2,
    }

    ms.phase = MaskPhase.EXPOSURE_COMPLETE
    ms.exposureData = mock_exposure
    ms.completionPct = 50

    return {"mask_state": ms.__dict__, "next_node": "develop"}


def transition_to_development_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = MaskState(**state.get("mask_state", {}))

    mock_develop = {
        "developer_chemical": "TMAH_2.38%",
        "development_time_s": 45,
        "development_temperature_c": 25,
        "line_width_nm": 7.2,
        "line_edge_roughness_nm": 1.8,
        "feature_uniformity_pct": 96.8,
    }

    ms.phase = MaskPhase.DEVELOPMENT_COMPLETE
    ms.developmentData = mock_develop
    ms.completionPct = 70

    return {"mask_state": ms.__dict__, "next_node": "verify_mask"}


def transition_to_mask_verified(state: dict[str, Any]) -> dict[str, Any]:
    ms = MaskState(**state.get("mask_state", {}))

    mock_metrology = {
        "cd_metrology_nm": 7.15,
        "cd_uniformity_3_sigma_nm": 0.45,
        "pattern_placement_nm": 2.5,
        "defect_count": 0,
        "defect_density_per_mm2": 0,
        "mask_qualification_pass": True,
    }

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-1",
            "role": "lithography_verifier",
            "timestamp": "2026-05-26T14:30:45Z",
            "signature": "lL1mM2nN3oO4pP5q...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-2",
            "role": "process_monitor",
            "timestamp": "2026-05-26T14:30:50Z",
            "signature": "rR6sS7tT8uU9vV0w...",
        },
    ]

    ms.phase = MaskPhase.MASK_VERIFIED
    ms.metrologyScan = mock_metrology
    ms.robotSignatures = mock_sigs
    ms.completionPct = 100

    return {
        "mask_state": ms.__dict__,
        "mask_lithography_record": {
            "waferId": ms.waferId,
            "designCid": ms.designCid,
            "metrology": ms.metrologyScan,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
