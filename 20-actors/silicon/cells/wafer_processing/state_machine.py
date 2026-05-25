"""Wafer processing state machine - ADR-2605242500."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class WaferPhase(Enum):
    INIT = "init"
    DEPOSITION_COMPLETE = "deposition_complete"
    ETCHING_COMPLETE = "etching_complete"
    IMPLANTATION_COMPLETE = "implantation_complete"
    CMP_COMPLETE = "cmp_complete"
    WAFER_VERIFIED = "wafer_verified"


@dataclass
class WaferState:
    phase: WaferPhase
    lotId: str
    completionPct: int
    depositionData: dict[str, Any] | None = None
    etchingData: dict[str, Any] | None = None
    implantData: dict[str, Any] | None = None
    cmpData: dict[str, Any] | None = None
    metrologyScan: dict[str, Any] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_deposition_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))

    mock_deposition = {
        "material": "SiO2",
        "thickness_nm": 180,
        "deposition_method": "PECVD",
        "growth_rate_nm_min": 3.2,
        "uniformity_pct": 97.8,
        "refractive_index": 1.46,
    }

    ws.phase = WaferPhase.DEPOSITION_COMPLETE
    ws.depositionData = mock_deposition
    ws.completionPct = 20

    return {"wafer_state": ws.__dict__, "next_node": "etch"}


def transition_to_etching_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))

    mock_etching = {
        "etch_process": "plasma_dry_etch",
        "etchant_gas": "C4F6_O2_Ar",
        "etch_depth_nm": 175,
        "selectivity_ratio": 8.2,
        "line_edge_roughness_nm": 2.1,
        "etch_uniformity_pct": 96.5,
        "undercut_nm": 0.5,
    }

    ws.phase = WaferPhase.ETCHING_COMPLETE
    ws.etchingData = mock_etching
    ws.completionPct = 40

    return {"wafer_state": ws.__dict__, "next_node": "implant"}


def transition_to_implantation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))

    mock_implant = {
        "dopant_species": "B+",
        "implant_energy_kev": 20,
        "implant_dose_cm2": 1e13,
        "junction_depth_nm": 85,
        "sheet_resistance_ohm_sq": 450,
        "doping_uniformity_pct": 98.1,
    }

    ws.phase = WaferPhase.IMPLANTATION_COMPLETE
    ws.implantData = mock_implant
    ws.completionPct = 60

    return {"wafer_state": ws.__dict__, "next_node": "cmp"}


def transition_to_cmp_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))

    mock_cmp = {
        "cmp_process": "chemical_mechanical_polish",
        "polish_pad": "IC1000_mm",
        "slurry_type": "colloidal_silica",
        "removal_rate_nm_min": 45,
        "within_wafer_uniformity_pct": 98.3,
        "polish_time_minutes": 3.8,
        "residual_thickness_nm": 5,
    }

    ws.phase = WaferPhase.CMP_COMPLETE
    ws.cmpData = mock_cmp
    ws.completionPct = 80

    return {"wafer_state": ws.__dict__, "next_node": "verify_wafer"}


def transition_to_wafer_verified(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))

    mock_metrology = {
        "thickness_nm": 5.2,
        "thickness_uniformity_pct": 98.5,
        "defect_count": 0,
        "defect_density_per_cm2": 0,
        "layer_stackup_correct": True,
        "wafer_release_approved": True,
    }

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-2",
            "role": "wafer_metrology",
            "timestamp": "2026-05-26T15:45:30Z",
            "signature": "xX1yY2zZ3aA4bB5c...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-3",
            "role": "process_handler",
            "timestamp": "2026-05-26T15:45:35Z",
            "signature": "dD6eE7fF8gG9hH0i...",
        },
    ]

    ws.phase = WaferPhase.WAFER_VERIFIED
    ws.metrologyScan = mock_metrology
    ws.robotSignatures = mock_sigs
    ws.completionPct = 100

    return {
        "wafer_state": ws.__dict__,
        "wafer_processing_record": {
            "lotId": ws.lotId,
            "deposition": ws.depositionData,
            "etching": ws.etchingData,
            "implantation": ws.implantData,
            "cmp": ws.cmpData,
            "metrology": ws.metrologyScan,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
