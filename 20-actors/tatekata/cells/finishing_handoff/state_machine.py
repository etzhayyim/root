"""
Finishing handoff state machine.

Per ADR-2605250715 §2 (Phase 4 cadence): surface prep, drywall, paint, trim.
7-node LangGraph with finishing witness quorum (≥2 robot Ed25519 sigs).

States:
  INIT → PREP_SURFACES → DRYWALL_TAPE_MUD → PAINT_SEAL → TRIM_INSTALL
       → WITNESS_WAIT → COMPLETE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FinishingPhase(Enum):
    """Phase progression in finishing handoff."""
    INIT = "init"
    SURFACES_PREPPED = "surfaces_prepped"
    DRYWALL_COMPLETE = "drywall_complete"
    PAINT_COMPLETE = "paint_complete"
    TRIM_INSTALLED = "trim_installed"
    WITNESS_WAIT = "witness_wait"
    COMPLETE = "complete"


@dataclass
class FinishingState:
    """State snapshot for LangGraph node."""
    phase: FinishingPhase
    projectId: str
    completionPct: int  # 0–100
    prepSummary: dict[str, Any] | None = None
    drywallSummary: dict[str, Any] | None = None
    paintSummary: dict[str, Any] | None = None
    trimSummary: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None
    photoCid: str | None = None


def transition_to_prep_complete(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → SURFACES_PREPPED: Giemon substrate cleaning."""
    fs = FinishingState(**state.get("finishing_state", {}))

    mock_prep = {
        "floor_area_m2": 850,
        "drywall_sheets_installed": 120,
        "tape_lengths_m": 1200,
        "mud_coats_applied": 3,
        "joint_smoothness_grit": 120,
    }

    fs.phase = FinishingPhase.SURFACES_PREPPED
    fs.prepSummary = mock_prep
    fs.completionPct = 20

    return {"finishing_state": fs.__dict__, "next_node": "drywall"}


def transition_to_drywall_complete(state: dict[str, Any]) -> dict[str, Any]:
    """SURFACES_PREPPED → DRYWALL_COMPLETE: Tape, mud, sand cycle."""
    fs = FinishingState(**state.get("finishing_state", {}))

    mock_drywall = {
        "drywall_inspection_passed": True,
        "sanding_dust_levels_mg_m3": 2.5,  # spec ≤5 mg/m³
        "final_surface_smoothness": "ready_for_paint",
    }

    fs.phase = FinishingPhase.DRYWALL_COMPLETE
    fs.drywallSummary = mock_drywall
    fs.completionPct = 40

    return {"finishing_state": fs.__dict__, "next_node": "paint"}


def transition_to_paint_complete(state: dict[str, Any]) -> dict[str, Any]:
    """DRYWALL_COMPLETE → PAINT_COMPLETE: Primer + finish coats."""
    fs = FinishingState(**state.get("finishing_state", {}))

    mock_paint = {
        "primer_coverage_m2": 850,
        "finish_coats_applied": 2,
        "paint_type": "low_voc_latex",
        "cure_time_hours": 24,
        "surface_finish_gloss": "eggshell",
    }

    fs.phase = FinishingPhase.PAINT_COMPLETE
    fs.paintSummary = mock_paint
    fs.completionPct = 70

    return {"finishing_state": fs.__dict__, "next_node": "trim"}


def transition_to_trim_installed(state: dict[str, Any]) -> dict[str, Any]:
    """PAINT_COMPLETE → TRIM_INSTALLED: Baseboard, casing, crown."""
    fs = FinishingState(**state.get("finishing_state", {}))

    mock_trim = {
        "baseboard_length_m": 520,
        "door_casings_installed": 12,
        "window_casings_installed": 8,
        "crown_molding_length_m": 180,
        "nail_spacing_mm": 300,
        "caulk_application_complete": True,
    }

    fs.phase = FinishingPhase.TRIM_INSTALLED
    fs.trimSummary = mock_trim
    fs.completionPct = 85

    return {"finishing_state": fs.__dict__, "next_node": "witness"}


def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    """TRIM_INSTALLED → WITNESS_WAIT: Collect ≥2 robot Ed25519 signatures."""
    fs = FinishingState(**state.get("finishing_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:giemon-unit-1",
            "role": "prep_executor",
            "timestamp": "2026-05-26T17:45:00Z",
            "signature": "qM8nR3sT6uV9wX..."
        },
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-3",
            "role": "finishing_inspector",
            "timestamp": "2026-05-26T17:45:05Z",
            "signature": "yL2aB5cD8eF1gH..."
        }
    ]

    fs.robotSignatures = mock_sigs
    fs.phase = FinishingPhase.WITNESS_WAIT
    fs.completionPct = 95

    return {"finishing_state": fs.__dict__, "next_node": "emit"}


def emit_finishing_record(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT → COMPLETE: Emit finishingRecord to MST."""
    fs = FinishingState(**state.get("finishing_state", {}))

    record = {
        "projectId": fs.projectId,
        "phase": "finishing_handoff",
        "completionPct": fs.completionPct,
        "recordedDate": "2026-05-26T17:45:30Z",
        "prepSummary": fs.prepSummary,
        "drywallSummary": fs.drywallSummary,
        "paintSummary": fs.paintSummary,
        "trimSummary": fs.trimSummary,
        "attestingRobots": [
            {
                "robotDid": sig["robotDid"],
                "role": sig["role"],
                "timestamp": sig["timestamp"],
                "signature": sig["signature"]
            }
            for sig in (fs.robotSignatures or [])
        ],
    }

    fs.phase = FinishingPhase.COMPLETE
    fs.completionPct = 100

    return {
        "finishing_state": fs.__dict__,
        "finishing_record": record,
        "next_node": "end"
    }
