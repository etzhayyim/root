"""VIN attestation binder state machine — ADR-2605252500 terminal cell, G2 + G13.

Aggregate all upstream attestations into per-VIN vehicleManufactureRecord.
Issues per-VIN DID `did:web:etzhayyim.com:sarutahiko:vehicle:<vin>` and anchors
on kotoba-datomic (G2 open VIN registry).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BinderPhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    VIN_ASSIGNED = "vin_assigned"
    VEHICLE_DID_ISSUED = "vehicle_did_issued"
    YATACHAIN_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"


@dataclass
class BinderState:
    phase: BinderPhase
    chassisId: str
    completionPct: int
    upstreamRecords: dict[str, str] | None = None
    vin: str | None = None
    vehicleDid: str | None = None
    kotoba-datomicAnchor: dict[str, Any] | None = None


def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    s = BinderState(**state.get("binder_state", {}))
    s.upstreamRecords = {
        "frameAttestation": "bafkreiframe...",
        "powertrainAttestation": "bafkreipt...",
        "cabBodyAttestation": "bafkreicab...",
        "marriageAttestation": "bafkreimarry...",
        "paintAttestation": "bafkreipaint...",
        "electricalAttestation": "bafkreielec...",
        "roadTestRecord": "bafkreiroad...",
        "emissionsAuditRecord": "bafkreiemis...",
    }
    s.phase = BinderPhase.RECORDS_COLLECTED
    s.completionPct = 25
    return {"binder_state": s.__dict__, "next_node": "vin"}


def transition_to_vin_assigned(state: dict[str, Any]) -> dict[str, Any]:
    s = BinderState(**state.get("binder_state", {}))
    s.vin = "ETZSARUTAHIKO00000A0001"  # 17-char VIN equivalent
    s.phase = BinderPhase.VIN_ASSIGNED
    s.completionPct = 50
    return {"binder_state": s.__dict__, "next_node": "did"}


def transition_to_vehicle_did_issued(state: dict[str, Any]) -> dict[str, Any]:
    s = BinderState(**state.get("binder_state", {}))
    s.vehicleDid = f"did:web:etzhayyim.com:sarutahiko:vehicle:{s.vin}"
    s.phase = BinderPhase.VEHICLE_DID_ISSUED
    s.completionPct = 70
    return {"binder_state": s.__dict__, "next_node": "anchor"}


def transition_to_kotoba-datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    s = BinderState(**state.get("binder_state", {}))
    s.kotoba-datomicAnchor = {
        "membraneNamespace": "com.etzhayyim.sarutahiko",
        "anchorTxHash": "0xSARUTAHIKOVINBINDER...",
        "l2Chain": "Base Sepolia (R0 dry-run)",
        "anchorBlockNumber": 0,
        "g2Compliant": True,
        "openVinRegistry": True,
    }
    s.phase = BinderPhase.YATACHAIN_ANCHORED
    s.completionPct = 90
    return {"binder_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = BinderState(**state.get("binder_state", {}))
    s.phase = BinderPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "etzhayyim:sarutahiko:vehicleManufactureRecord",
        "chassisId": s.chassisId,
        "vin": s.vin,
        "vehicleDid": s.vehicleDid,
        "upstreamRecords": s.upstreamRecords,
        "kotoba-datomicAnchor": s.kotoba-datomicAnchor,
        "recordedAt": "2026-05-26T20:00:00Z",
    }
    return {"binder_state": s.__dict__, "vehicle_manufacture_record": record, "next_node": "end"}
