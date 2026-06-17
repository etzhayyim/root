"""Homologation binder state machine — ADR-2605252600 L5c terminal.

EN 50126/50128/50129 (RAMS) / 日本鉄道事業法 / FRA Tier I-III. Aggregates all
upstream attestations + issues per-trainset DID. G2 + G13 enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HomologationPhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    SERIAL_ASSIGNED = "serial_assigned"
    TRAINSET_DID_ISSUED = "trainset_did_issued"
    HOMOLOGATION_AUTHORITY_REVIEW = "homologation_authority_review"
    KOTOBA_DATOMIC_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"


@dataclass
class HomologationState:
    phase: HomologationPhase
    trainsetId: str
    completionPct: int
    upstreamRecords: dict[str, str] | None = None
    serial: str | None = None
    trainsetDid: str | None = None
    authorityReview: dict[str, Any] | None = None
    kotoba_datomicAnchor: dict[str, Any] | None = None


def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.upstreamRecords = {
        "carbodyAttestations": "bafkreicarbodybundle...",
        "bogieAttestations": "bafkreibogibundle...",
        "interiorAttestations": "bafkreiintbundle...",
        "tractionElectricalAttestation": "bafkreitr...",
        "finalAssemblyAttestation": "bafkreifinal...",
        "dynamicTestRecord": "bafkreidyn...",
        "acousticEmissionsAuditRecord": "bafkreiac...",
    }
    s.phase = HomologationPhase.RECORDS_COLLECTED
    s.completionPct = 20
    return {"homologation_state": s.__dict__, "next_node": "serial"}


def transition_to_serial_assigned(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.serial = "ETZYAMABIKO-2026-05-0001"
    s.phase = HomologationPhase.SERIAL_ASSIGNED
    s.completionPct = 40
    return {"homologation_state": s.__dict__, "next_node": "did"}


def transition_to_trainset_did_issued(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.trainsetDid = f"did:web:etzhayyim.com:yamabiko:trainset:{s.serial}"
    s.phase = HomologationPhase.TRAINSET_DID_ISSUED
    s.completionPct = 55
    return {"homologation_state": s.__dict__, "next_node": "authority"}


def transition_to_homologation_authority_review(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.authorityReview = {
        "ramsStandards": ["EN 50126", "EN 50128", "EN 50129"],
        "jurisdiction": "JP",
        "homologationRegime": "日本 鉄道事業法",
        "authorityDid": "did:web:etzhayyim.com:authority:mlit-jp",
        "decision": "ISSUE_TYPE_APPROVAL",
        "timestamp": "2026-05-27T13:00:00Z",
    }
    s.phase = HomologationPhase.HOMOLOGATION_AUTHORITY_REVIEW
    s.completionPct = 75
    return {"homologation_state": s.__dict__, "next_node": "anchor"}


def transition_to_kotoba_datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.kotoba_datomicAnchor = {
        "membraneNamespace": "com.etzhayyim.yamabiko",
        "anchorTxHash": "0xYAMABIKOHOMOLOGATION...",
        "l2Chain": "Base Sepolia (R0 dry-run)",
        "anchorBlockNumber": 0,
        "g2Compliant": True,
        "openTrainsetRegistry": True,
    }
    s.phase = HomologationPhase.KOTOBA_DATOMIC_ANCHORED
    s.completionPct = 90
    return {"homologation_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = HomologationState(**state.get("homologation_state", {}))
    s.phase = HomologationPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.homologationRecord",
        "trainsetId": s.trainsetId,
        "serial": s.serial,
        "trainsetDid": s.trainsetDid,
        "upstreamRecords": s.upstreamRecords,
        "authorityReview": s.authorityReview,
        "kotoba-datomicAnchor": s.kotoba_datomicAnchor,
        "recordedAt": "2026-05-27T13:30:00Z",
    }
    return {"homologation_state": s.__dict__, "homologation_record": record, "next_node": "end"}
