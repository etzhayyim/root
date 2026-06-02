"""Melting furnace state machine — ADR-2605252400 L3.

Twin-chamber Al furnace ~720°C with N₂/Cl₂ degas + salt-flux refining + alloy
adjust to 3xxx (body) / 5xxx (end stock). Witness quorum ≥2 robots per pour (G4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MeltingPhase(Enum):
    INIT = "init"
    CHARGED = "charged"
    MELT_HELD = "melt_held"
    DEGAS_COMPLETE = "degas_complete"
    ALLOY_ADJUSTED = "alloy_adjusted"
    POUR_WITNESSED = "pour_witnessed"
    RECORD_EMITTED = "record_emitted"


@dataclass
class MeltingState:
    phase: MeltingPhase
    lotId: str
    completionPct: int
    chargeMassKg: float | None = None
    furnaceTempC: int | None = None
    degasGas: str | None = None
    saltFluxKg: float | None = None
    alloyComposition: dict[str, Any] | None = None
    pourMassKg: float | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_charged(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.chargeMassKg = 470.0
    s.phase = MeltingPhase.CHARGED
    s.completionPct = 15
    return {"melting_state": s.__dict__, "next_node": "hold"}


def transition_to_melt_held(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.furnaceTempC = 720
    s.phase = MeltingPhase.MELT_HELD
    s.completionPct = 40
    return {"melting_state": s.__dict__, "next_node": "degas"}


def transition_to_degas_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.degasGas = "N2"
    s.saltFluxKg = 6.4
    s.phase = MeltingPhase.DEGAS_COMPLETE
    s.completionPct = 60
    return {"melting_state": s.__dict__, "next_node": "alloy"}


def transition_to_alloy_adjusted(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.alloyComposition = {
        "designation": "AA3104 (can body)",
        "Mn_pct": 0.95, "Mg_pct": 1.10, "Fe_pct": 0.40, "Si_pct": 0.25,
        "Cu_pct": 0.15, "Zn_pct": 0.10, "Al_pct": "balance",
    }
    s.phase = MeltingPhase.ALLOY_ADJUSTED
    s.completionPct = 80
    return {"melting_state": s.__dict__, "next_node": "pour"}


def transition_to_pour_witnessed(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.pourMassKg = 462.0
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:kamado-unit-1", "role": "furnace_tender",
         "timestamp": "2026-05-26T11:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:yokin-unit-1", "role": "pour_manipulator",
         "timestamp": "2026-05-26T11:00:05Z", "signature": "..."},
    ]
    s.phase = MeltingPhase.POUR_WITNESSED
    s.completionPct = 92
    return {"melting_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = MeltingState(**state.get("melting_state", {}))
    s.phase = MeltingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.meltingAttestation",
        "lotId": s.lotId,
        "chargeMassKg": s.chargeMassKg,
        "furnaceTempC": s.furnaceTempC,
        "degasGas": s.degasGas,
        "saltFluxKg": s.saltFluxKg,
        "alloyComposition": s.alloyComposition,
        "pourMassKg": s.pourMassKg,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T11:00:10Z",
    }
    return {"melting_state": s.__dict__, "melting_attestation": record, "next_node": "end"}
