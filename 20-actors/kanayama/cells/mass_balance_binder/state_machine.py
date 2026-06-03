"""Mass-balance binder state machine — ADR-2605252400 terminal cell, G2 + G14.

Aggregate L1–L5b + cross-cutting records into a single mass-balance audit
record:

    input_mass = output_metal + dross + emission_mass

≥98% closure required (G12 KPI). Anchored on kotoba-datomic (G2 audit log).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BalancePhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    MASS_BALANCE_COMPUTED = "mass_balance_computed"
    YATACHAIN_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"


@dataclass
class BalanceState:
    phase: BalancePhase
    lotId: str
    completionPct: int
    upstreamRecords: dict[str, str] | None = None
    inputMassKg: float | None = None
    outputMetalKg: float | None = None
    drossMassKg: float | None = None
    emissionMassKg: float | None = None
    closurePct: float | None = None
    accept: bool | None = None
    kotoba-datomicAnchor: dict[str, Any] | None = None


def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    s = BalanceState(**state.get("balance_state", {}))
    s.upstreamRecords = {
        "intakeRecord": "bafkreiintake...",
        "decoatingAttestation": "bafkreidecoat...",
        "meltingAttestation": "bafkreimelt...",
        "drossRecoveryRecord": "bafkreidross...",
        "dcCastingAttestation": "bafkreicast...",
        "rollingAttestation": "bafkreiroll...",
        "coilQualificationRecord": "bafkreicoil...",
        "airEmissionsAuditRecord": "bafkreiemis...",
    }
    s.phase = BalancePhase.RECORDS_COLLECTED
    s.completionPct = 25
    return {"balance_state": s.__dict__, "next_node": "compute"}


def transition_to_mass_balance_computed(state: dict[str, Any]) -> dict[str, Any]:
    s = BalanceState(**state.get("balance_state", {}))
    s.inputMassKg = 480.5
    s.outputMetalKg = 462.0 + 3.6  # main pour + dross-recovered secondary
    s.drossMassKg = 8.0 - 3.6  # gross dross minus recovered = net waste
    s.emissionMassKg = 4.7  # off-gas captured + scrubbed mass
    total_out = (s.outputMetalKg or 0) + (s.drossMassKg or 0) + (s.emissionMassKg or 0)
    s.closurePct = round(total_out / (s.inputMassKg or 1) * 100, 2)
    s.accept = (s.closurePct or 0) >= 98.0
    s.phase = BalancePhase.MASS_BALANCE_COMPUTED
    s.completionPct = 60
    return {"balance_state": s.__dict__, "next_node": "anchor"}


def transition_to_kotoba-datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    s = BalanceState(**state.get("balance_state", {}))
    s.kotoba-datomicAnchor = {
        "membraneNamespace": "com.etzhayyim.kanayama",
        "anchorTxHash": "0xKANAYAMABALANCE...",
        "l2Chain": "Base Sepolia (R0 dry-run)",
        "anchorBlockNumber": 0,
        "g2Compliant": True,
    }
    s.phase = BalancePhase.YATACHAIN_ANCHORED
    s.completionPct = 90
    return {"balance_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = BalanceState(**state.get("balance_state", {}))
    s.phase = BalancePhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "etzhayyim:kanayama:massBalanceBinderRecord",
        "lotId": s.lotId,
        "upstreamRecords": s.upstreamRecords,
        "inputMassKg": s.inputMassKg,
        "outputMetalKg": s.outputMetalKg,
        "drossMassKg": s.drossMassKg,
        "emissionMassKg": s.emissionMassKg,
        "closurePct": s.closurePct,
        "g2Limit": 98.0,
        "accept": s.accept,
        "kotoba-datomicAnchor": s.kotoba-datomicAnchor,
        "recordedAt": "2026-05-26T18:00:00Z",
    }
    return {
        "balance_state": s.__dict__,
        "mass_balance_binder_record": record,
        "next_node": "end",
    }
