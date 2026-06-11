"""DC casting state machine — ADR-2605252400 L4.

Direct Chill (DC) slab casting — typical Al slab 1m × 2m × 8m. Followed by
homogenization 540-580°C × 12-24h.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CastingPhase(Enum):
    INIT = "init"
    MOLD_PREPARED = "mold_prepared"
    DC_CASTING_COMPLETE = "dc_casting_complete"
    HOMOGENIZATION_COMPLETE = "homogenization_complete"
    INSPECTION_PASSED = "inspection_passed"
    RECORD_EMITTED = "record_emitted"


@dataclass
class CastingState:
    phase: CastingPhase
    lotId: str
    completionPct: int
    slabDimensionsMm: dict[str, int] | None = None
    castingTempC: int | None = None
    chillWaterFlowLpm: int | None = None
    homogenizationTempC: int | None = None
    homogenizationHours: int | None = None
    inspectionFindings: list[dict[str, Any]] | None = None
    slabMassKg: float | None = None


def transition_to_mold_prepared(state: dict[str, Any]) -> dict[str, Any]:
    s = CastingState(**state.get("casting_state", {}))
    s.slabDimensionsMm = {"width": 1000, "thickness": 600, "length": 8000}
    s.phase = CastingPhase.MOLD_PREPARED
    s.completionPct = 15
    return {"casting_state": s.__dict__, "next_node": "cast"}


def transition_to_dc_casting_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CastingState(**state.get("casting_state", {}))
    s.castingTempC = 690
    s.chillWaterFlowLpm = 1800
    s.phase = CastingPhase.DC_CASTING_COMPLETE
    s.completionPct = 45
    return {"casting_state": s.__dict__, "next_node": "homogenize"}


def transition_to_homogenization_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CastingState(**state.get("casting_state", {}))
    s.homogenizationTempC = 560
    s.homogenizationHours = 18
    s.phase = CastingPhase.HOMOGENIZATION_COMPLETE
    s.completionPct = 70
    return {"casting_state": s.__dict__, "next_node": "inspect"}


def transition_to_inspection_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = CastingState(**state.get("casting_state", {}))
    s.inspectionFindings = []
    s.slabMassKg = 12960.0  # 1.0m × 0.6m × 8.0m × 2700 kg/m³
    s.phase = CastingPhase.INSPECTION_PASSED
    s.completionPct = 90
    return {"casting_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = CastingState(**state.get("casting_state", {}))
    s.phase = CastingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.dcCastingAttestation",
        "lotId": s.lotId,
        "slabDimensionsMm": s.slabDimensionsMm,
        "castingTempC": s.castingTempC,
        "chillWaterFlowLpm": s.chillWaterFlowLpm,
        "homogenizationTempC": s.homogenizationTempC,
        "homogenizationHours": s.homogenizationHours,
        "inspectionFindings": s.inspectionFindings,
        "slabMassKg": s.slabMassKg,
        "recordedAt": "2026-05-26T13:00:00Z",
    }
    return {"casting_state": s.__dict__, "dc_casting_attestation": record, "next_node": "end"}
