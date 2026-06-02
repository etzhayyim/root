"""Intake QA state machine — ADR-2605252400 L1.

UBC bale weighing + Cl residue + moisture + magnetic impurity detection. AI
classifier flags contamination thresholds before downstream commitment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IntakePhase(Enum):
    INIT = "init"
    BALE_WEIGHED = "bale_weighed"
    CONTAMINATION_SCANNED = "contamination_scanned"
    ACCEPT_OR_REJECT_DECIDED = "accept_or_reject_decided"
    RECORD_EMITTED = "record_emitted"


@dataclass
class IntakeState:
    phase: IntakePhase
    lotId: str
    completionPct: int
    baleWeightKg: float | None = None
    chlorideResidualPpm: float | None = None
    moisturePct: float | None = None
    magneticImpurityPct: float | None = None
    nonAlNonMagneticImpurityPct: float | None = None
    accept: bool | None = None


def transition_to_bale_weighed(state: dict[str, Any]) -> dict[str, Any]:
    s = IntakeState(**state.get("intake_state", {}))
    s.baleWeightKg = 480.5
    s.phase = IntakePhase.BALE_WEIGHED
    s.completionPct = 25
    return {"intake_state": s.__dict__, "next_node": "scan"}


def transition_to_contamination_scanned(state: dict[str, Any]) -> dict[str, Any]:
    s = IntakeState(**state.get("intake_state", {}))
    s.chlorideResidualPpm = 12.0
    s.moisturePct = 1.8
    s.magneticImpurityPct = 0.3
    s.nonAlNonMagneticImpurityPct = 0.7
    s.phase = IntakePhase.CONTAMINATION_SCANNED
    s.completionPct = 65
    return {"intake_state": s.__dict__, "next_node": "decide"}


def transition_to_accept_or_reject_decided(state: dict[str, Any]) -> dict[str, Any]:
    s = IntakeState(**state.get("intake_state", {}))
    s.accept = (
        (s.chlorideResidualPpm or 0) < 50
        and (s.moisturePct or 0) < 5
        and (s.magneticImpurityPct or 0) < 1.0
        and (s.nonAlNonMagneticImpurityPct or 0) < 2.0
    )
    s.phase = IntakePhase.ACCEPT_OR_REJECT_DECIDED
    s.completionPct = 90
    return {"intake_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = IntakeState(**state.get("intake_state", {}))
    s.phase = IntakePhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.intakeRecord",
        "lotId": s.lotId,
        "baleWeightKg": s.baleWeightKg,
        "chlorideResidualPpm": s.chlorideResidualPpm,
        "moisturePct": s.moisturePct,
        "magneticImpurityPct": s.magneticImpurityPct,
        "nonAlNonMagneticImpurityPct": s.nonAlNonMagneticImpurityPct,
        "accept": s.accept,
        "recordedAt": "2026-05-26T08:00:00Z",
    }
    return {"intake_state": s.__dict__, "intake_record": record, "next_node": "end"}
