"""Dross recovery state machine — ADR-2605252400 L3 cross-cutting + G14.

Salt-cake processing → secondary Al recovery + K-salt recycled. Standalone
disposal is §2(g) violation; this cell ensures G14 closed-loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DrossPhase(Enum):
    INIT = "init"
    DROSS_COLLECTED = "dross_collected"
    SALT_CAKE_PROCESSED = "salt_cake_processed"
    SECONDARY_AL_RECOVERED = "secondary_al_recovered"
    K_SALT_RECYCLED = "k_salt_recycled"
    RECORD_EMITTED = "record_emitted"


@dataclass
class DrossState:
    phase: DrossPhase
    lotId: str
    completionPct: int
    drossMassKg: float | None = None
    saltCakeMassKg: float | None = None
    secondaryAlRecoveredKg: float | None = None
    kSaltRecycledKg: float | None = None
    landfillResidueKg: float | None = None  # G14: target = 0


def transition_to_dross_collected(state: dict[str, Any]) -> dict[str, Any]:
    s = DrossState(**state.get("dross_state", {}))
    s.drossMassKg = 8.0
    s.phase = DrossPhase.DROSS_COLLECTED
    s.completionPct = 20
    return {"dross_state": s.__dict__, "next_node": "salt_cake"}


def transition_to_salt_cake_processed(state: dict[str, Any]) -> dict[str, Any]:
    s = DrossState(**state.get("dross_state", {}))
    s.saltCakeMassKg = 6.4
    s.phase = DrossPhase.SALT_CAKE_PROCESSED
    s.completionPct = 45
    return {"dross_state": s.__dict__, "next_node": "al"}


def transition_to_secondary_al_recovered(state: dict[str, Any]) -> dict[str, Any]:
    s = DrossState(**state.get("dross_state", {}))
    s.secondaryAlRecoveredKg = 3.6
    s.phase = DrossPhase.SECONDARY_AL_RECOVERED
    s.completionPct = 70
    return {"dross_state": s.__dict__, "next_node": "k_salt"}


def transition_to_k_salt_recycled(state: dict[str, Any]) -> dict[str, Any]:
    s = DrossState(**state.get("dross_state", {}))
    s.kSaltRecycledKg = 2.6
    s.landfillResidueKg = 0.2  # G14 target = ≤1% of input
    s.phase = DrossPhase.K_SALT_RECYCLED
    s.completionPct = 90
    return {"dross_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = DrossState(**state.get("dross_state", {}))
    s.phase = DrossPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "etzhayyim:kanayama:drossRecoveryRecord",
        "lotId": s.lotId,
        "drossMassKg": s.drossMassKg,
        "saltCakeMassKg": s.saltCakeMassKg,
        "secondaryAlRecoveredKg": s.secondaryAlRecoveredKg,
        "kSaltRecycledKg": s.kSaltRecycledKg,
        "landfillResidueKg": s.landfillResidueKg,
        "g14CircularAccept": (s.landfillResidueKg or 0) < 0.5,
        "recordedAt": "2026-05-26T11:15:00Z",
    }
    return {"dross_state": s.__dict__, "dross_recovery_record": record, "next_node": "end"}
