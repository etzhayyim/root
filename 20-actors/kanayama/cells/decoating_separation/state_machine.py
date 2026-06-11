"""De-coating + separation state machine — ADR-2605252400 L2.

~500°C rotary de-coater (lacquer + paint burnoff with off-gas capture + filter),
rotary shredder, magnetic + eddy-current separation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DecoatingPhase(Enum):
    INIT = "init"
    DECOATER_HEATED = "decoater_heated"
    LACQUER_BURNOFF_COMPLETE = "lacquer_burnoff_complete"
    SHRED_COMPLETE = "shred_complete"
    MAGNETIC_SEPARATION_COMPLETE = "magnetic_separation_complete"
    EDDY_CURRENT_SEPARATION_COMPLETE = "eddy_current_separation_complete"
    RECORD_EMITTED = "record_emitted"


@dataclass
class DecoatingState:
    phase: DecoatingPhase
    lotId: str
    completionPct: int
    decoaterTempC: int | None = None
    offGasCaptureCid: str | None = None
    shredFractionMm: dict[str, Any] | None = None
    magneticFraction: dict[str, Any] | None = None
    nonAlFraction: dict[str, Any] | None = None
    cleanAlMassKg: float | None = None


def transition_to_decoater_heated(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.decoaterTempC = 500
    s.phase = DecoatingPhase.DECOATER_HEATED
    s.completionPct = 15
    return {"decoating_state": s.__dict__, "next_node": "burnoff"}


def transition_to_lacquer_burnoff_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.offGasCaptureCid = "bafkreioffgas..."
    s.phase = DecoatingPhase.LACQUER_BURNOFF_COMPLETE
    s.completionPct = 40
    return {"decoating_state": s.__dict__, "next_node": "shred"}


def transition_to_shred_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.shredFractionMm = {"size_distribution_mm": [5, 10, 20, 50], "fines_pct": 8}
    s.phase = DecoatingPhase.SHRED_COMPLETE
    s.completionPct = 60
    return {"decoating_state": s.__dict__, "next_node": "magnetic"}


def transition_to_magnetic_separation_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.magneticFraction = {"removedFeKg": 1.4, "diversionPath": "kanayama-wave2-feedstock-bin"}
    s.phase = DecoatingPhase.MAGNETIC_SEPARATION_COMPLETE
    s.completionPct = 75
    return {"decoating_state": s.__dict__, "next_node": "eddy"}


def transition_to_eddy_current_separation_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.nonAlFraction = {"removedCuKg": 0.6, "removedSteelTrimsKg": 0.2}
    s.cleanAlMassKg = 470.0
    s.phase = DecoatingPhase.EDDY_CURRENT_SEPARATION_COMPLETE
    s.completionPct = 90
    return {"decoating_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = DecoatingState(**state.get("decoating_state", {}))
    s.phase = DecoatingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.decoatingAttestation",
        "lotId": s.lotId,
        "decoaterTempC": s.decoaterTempC,
        "offGasCaptureCid": s.offGasCaptureCid,
        "shredFractionMm": s.shredFractionMm,
        "magneticFraction": s.magneticFraction,
        "nonAlFraction": s.nonAlFraction,
        "cleanAlMassKg": s.cleanAlMassKg,
        "recordedAt": "2026-05-26T09:30:00Z",
    }
    return {"decoating_state": s.__dict__, "decoating_attestation": record, "next_node": "end"}
