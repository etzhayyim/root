"""Hot rolling state machine — ADR-2605252400 L5a.

Multi-pass hot rolling ~500°C, slab → hot band ~3 mm.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HotRollingPhase(Enum):
    INIT = "init"
    SLAB_REHEATED = "slab_reheated"
    ROUGH_ROLL_COMPLETE = "rough_roll_complete"
    FINISH_ROLL_COMPLETE = "finish_roll_complete"
    COILED = "coiled"
    RECORD_EMITTED = "record_emitted"


@dataclass
class HotRollingState:
    phase: HotRollingPhase
    lotId: str
    completionPct: int
    reheatTempC: int | None = None
    passes: list[dict[str, Any]] | None = None
    finalGaugeMm: float | None = None
    hotBandCoilId: str | None = None
    hotBandMassKg: float | None = None


def transition_to_slab_reheated(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.reheatTempC = 510
    s.phase = HotRollingPhase.SLAB_REHEATED
    s.completionPct = 15
    return {"hot_rolling_state": s.__dict__, "next_node": "rough"}


def transition_to_rough_roll_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.passes = [
        {"pass": 1, "in_mm": 600, "out_mm": 400, "tempC": 510},
        {"pass": 2, "in_mm": 400, "out_mm": 250, "tempC": 495},
        {"pass": 3, "in_mm": 250, "out_mm": 120, "tempC": 480},
        {"pass": 4, "in_mm": 120, "out_mm": 60, "tempC": 470},
    ]
    s.phase = HotRollingPhase.ROUGH_ROLL_COMPLETE
    s.completionPct = 50
    return {"hot_rolling_state": s.__dict__, "next_node": "finish"}


def transition_to_finish_roll_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    extra = [
        {"pass": 5, "in_mm": 60, "out_mm": 25, "tempC": 460},
        {"pass": 6, "in_mm": 25, "out_mm": 10, "tempC": 440},
        {"pass": 7, "in_mm": 10, "out_mm": 5, "tempC": 410},
        {"pass": 8, "in_mm": 5, "out_mm": 3, "tempC": 380},
    ]
    s.passes = (s.passes or []) + extra
    s.finalGaugeMm = 3.0
    s.phase = HotRollingPhase.FINISH_ROLL_COMPLETE
    s.completionPct = 75
    return {"hot_rolling_state": s.__dict__, "next_node": "coil"}


def transition_to_coiled(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.hotBandCoilId = "KANAYAMA-HBC-2026-05-26-0001"
    s.hotBandMassKg = 12700.0  # slight loss to scale + side trim
    s.phase = HotRollingPhase.COILED
    s.completionPct = 90
    return {"hot_rolling_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.phase = HotRollingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.rollingAttestation",
        "lotId": s.lotId,
        "reheatTempC": s.reheatTempC,
        "passes": s.passes,
        "finalGaugeMm": s.finalGaugeMm,
        "hotBandCoilId": s.hotBandCoilId,
        "hotBandMassKg": s.hotBandMassKg,
        "rollingStage": "hot",
        "recordedAt": "2026-05-26T14:30:00Z",
    }
    return {"hot_rolling_state": s.__dict__, "rolling_attestation": record, "next_node": "end"}
