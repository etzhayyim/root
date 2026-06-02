"""Cold rolling + finishing state machine — ADR-2605252400 L5b.

Cold rolling + temper to 0.27 mm can-stock coil + Migaki surface inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ColdRollingPhase(Enum):
    INIT = "init"
    HOT_BAND_LOADED = "hot_band_loaded"
    COLD_PASSES_COMPLETE = "cold_passes_complete"
    TEMPER_COMPLETE = "temper_complete"
    SURFACE_INSPECTION_COMPLETE = "surface_inspection_complete"
    COIL_QUALIFIED = "coil_qualified"
    RECORD_EMITTED = "record_emitted"


@dataclass
class ColdRollingState:
    phase: ColdRollingPhase
    lotId: str
    completionPct: int
    inputHotBandCoilId: str | None = None
    coldPasses: list[dict[str, Any]] | None = None
    finalGaugeMm: float | None = None
    temper: str | None = None
    migakiInspectionFindings: list[dict[str, Any]] | None = None
    coilId: str | None = None
    coilMassKg: float | None = None
    qualificationAccept: bool | None = None


def transition_to_hot_band_loaded(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.inputHotBandCoilId = "KANAYAMA-HBC-2026-05-26-0001"
    s.phase = ColdRollingPhase.HOT_BAND_LOADED
    s.completionPct = 10
    return {"cold_rolling_state": s.__dict__, "next_node": "cold"}


def transition_to_cold_passes_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.coldPasses = [
        {"pass": 1, "in_mm": 3.0, "out_mm": 1.5},
        {"pass": 2, "in_mm": 1.5, "out_mm": 0.8},
        {"pass": 3, "in_mm": 0.8, "out_mm": 0.45},
        {"pass": 4, "in_mm": 0.45, "out_mm": 0.27},
    ]
    s.finalGaugeMm = 0.27
    s.phase = ColdRollingPhase.COLD_PASSES_COMPLETE
    s.completionPct = 45
    return {"cold_rolling_state": s.__dict__, "next_node": "temper"}


def transition_to_temper_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.temper = "H19"
    s.phase = ColdRollingPhase.TEMPER_COMPLETE
    s.completionPct = 65
    return {"cold_rolling_state": s.__dict__, "next_node": "migaki"}


def transition_to_surface_inspection_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.migakiInspectionFindings = []
    s.phase = ColdRollingPhase.SURFACE_INSPECTION_COMPLETE
    s.completionPct = 80
    return {"cold_rolling_state": s.__dict__, "next_node": "qualify"}


def transition_to_coil_qualified(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.coilId = "KANAYAMA-COIL-2026-05-26-0001"
    s.coilMassKg = 12450.0
    s.qualificationAccept = True
    s.phase = ColdRollingPhase.COIL_QUALIFIED
    s.completionPct = 92
    return {"cold_rolling_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = ColdRollingState(**state.get("cold_rolling_state", {}))
    s.phase = ColdRollingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.coilQualificationRecord",
        "lotId": s.lotId,
        "inputHotBandCoilId": s.inputHotBandCoilId,
        "coldPasses": s.coldPasses,
        "finalGaugeMm": s.finalGaugeMm,
        "temper": s.temper,
        "migakiInspectionFindings": s.migakiInspectionFindings,
        "coilId": s.coilId,
        "coilMassKg": s.coilMassKg,
        "qualificationAccept": s.qualificationAccept,
        "intendedProduct": "can-body-stock-AA3104",
        "recordedAt": "2026-05-26T16:30:00Z",
    }
    return {
        "cold_rolling_state": s.__dict__,
        "coil_qualification_record": record,
        "next_node": "end",
    }
