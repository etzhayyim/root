"""Paint finishing state machine — ADR-2605252500 L5a.

KTL primer + base coat + clear coat (water-based, VOC <100 g/L). G8 VOC limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PaintPhase(Enum):
    INIT = "init"
    PRETREATMENT_DONE = "pretreatment_done"
    KTL_PRIMER_APPLIED = "ktl_primer_applied"
    BASE_COAT_APPLIED = "base_coat_applied"
    CLEAR_COAT_APPLIED = "clear_coat_applied"
    CURED = "cured"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class PaintState:
    phase: PaintPhase
    chassisId: str
    completionPct: int
    pretreatmentResult: dict[str, Any] | None = None
    layers: list[dict[str, Any]] | None = None
    vocGPerL: float | None = None
    cureRecord: dict[str, Any] | None = None


def transition_to_pretreatment_done(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    s.pretreatmentResult = {"degreased": True, "phosphatedNm": 1.2, "rinseRounds": 3}
    s.phase = PaintPhase.PRETREATMENT_DONE
    s.completionPct = 15
    return {"paint_state": s.__dict__, "next_node": "ktl"}


def transition_to_ktl_primer_applied(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    s.layers = [{"layer": "ktl-primer", "thicknessUm": 22, "filmCid": "bafkreiktl..."}]
    s.phase = PaintPhase.KTL_PRIMER_APPLIED
    s.completionPct = 35
    return {"paint_state": s.__dict__, "next_node": "base"}


def transition_to_base_coat_applied(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    (s.layers or []).append({"layer": "base-coat", "thicknessUm": 18, "color": "OEM-default-grey"})
    s.phase = PaintPhase.BASE_COAT_APPLIED
    s.completionPct = 55
    return {"paint_state": s.__dict__, "next_node": "clear"}


def transition_to_clear_coat_applied(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    (s.layers or []).append({"layer": "clear-coat", "thicknessUm": 40})
    s.vocGPerL = 92  # spec <100 g/L
    s.phase = PaintPhase.CLEAR_COAT_APPLIED
    s.completionPct = 75
    return {"paint_state": s.__dict__, "next_node": "cure"}


def transition_to_cured(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    s.cureRecord = {"tempC": 140, "durationMinutes": 30, "tunnelType": "IR + convection"}
    s.phase = PaintPhase.CURED
    s.completionPct = 90
    return {"paint_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = PaintState(**state.get("paint_state", {}))
    s.phase = PaintPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.paintAttestation",
        "chassisId": s.chassisId,
        "pretreatmentResult": s.pretreatmentResult,
        "layers": s.layers,
        "vocGPerL": s.vocGPerL,
        "vocLimitGPerL": 100,
        "g8Accept": (s.vocGPerL or 999) < 100,
        "cureRecord": s.cureRecord,
        "recordedAt": "2026-05-26T15:00:00Z",
    }
    return {"paint_state": s.__dict__, "paint_attestation": record, "next_node": "end"}
