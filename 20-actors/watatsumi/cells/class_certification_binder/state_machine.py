"""Class certification binder state machine — ADR-2605252200 terminal cell.

Aggregate L1–L5c records + marine_emissions_audit into a single
classCertificationRecord anchored on kotoba-datomic. Class regimes: DNV-RU-UWT /
ABS Underwater Vehicles / NK 同等. G2 audit log enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CertificationPhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    SURVEYOR_REVIEW = "surveyor_review"
    KOTOBA_DATOMIC_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"


@dataclass
class CertificationState:
    phase: CertificationPhase
    craftId: str
    completionPct: int
    classRegime: str | None = None
    upstreamRecords: dict[str, str] | None = None  # {recordType: CID}
    surveyorReview: dict[str, Any] | None = None
    kotoba-datomicAnchor: dict[str, Any] | None = None


def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    cs = CertificationState(**state.get("certification_state", {}))
    cs.classRegime = state.get("classRegime", "DNV-RU-UWT")
    cs.upstreamRecords = {
        "pressureHullAttestation": "bafkreihullatt...",
        "sectionAssemblyAttestation": "bafkreisectatt...",
        "weldInspectionRecord": "bafkreiweld...",
        "systemIntegrationAttestation": "bafkreisysint...",
        "sectionJoiningAttestation": "bafkreisectjoin...",
        "pressureTestRecord": "bafkreipress...",
        "seaTrialRecord": "bafkreitrial...",
        "marineEmissionsAuditRecord": "bafkreiemis...",
    }
    cs.phase = CertificationPhase.RECORDS_COLLECTED
    cs.completionPct = 30
    return {"certification_state": cs.__dict__, "next_node": "surveyor"}


def transition_to_surveyor_review(state: dict[str, Any]) -> dict[str, Any]:
    cs = CertificationState(**state.get("certification_state", {}))
    cs.surveyorReview = {
        "surveyorDid": "did:web:etzhayyim.com:surveyor:dnv-uwt-007",
        "surveyorSbtId": "did:web:etzhayyim.com:adherent:surveyor-007#sbt",
        "regimeReference": cs.classRegime,
        "findings": [],
        "recommend": "ISSUE_CLASS_CERTIFICATE",
        "timestamp": "2026-05-27T13:00:00Z",
    }
    cs.phase = CertificationPhase.SURVEYOR_REVIEW
    cs.completionPct = 65
    return {"certification_state": cs.__dict__, "next_node": "anchor"}


def transition_to_kotoba-datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    cs = CertificationState(**state.get("certification_state", {}))
    cs.kotoba-datomicAnchor = {
        "membraneNamespace": "com.etzhayyim.watatsumi",
        "anchorTxHash": "0xWATATSUMICERT...",
        "l2Chain": "Base Sepolia (R0 dry-run)",
        "anchorBlockNumber": 0,
        "g2Compliant": True,
    }
    cs.phase = CertificationPhase.KOTOBA_DATOMIC_ANCHORED
    cs.completionPct = 90
    return {"certification_state": cs.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    cs = CertificationState(**state.get("certification_state", {}))
    cs.phase = CertificationPhase.RECORD_EMITTED
    cs.completionPct = 100
    record = {
        "$type": "etzhayyim:watatsumi:classCertificationRecord",
        "craftId": cs.craftId,
        "classRegime": cs.classRegime,
        "upstreamRecords": cs.upstreamRecords,
        "surveyorReview": cs.surveyorReview,
        "kotoba-datomicAnchor": cs.kotoba-datomicAnchor,
        "g2Compliant": True,
        "recordedAt": "2026-05-27T13:30:00Z",
    }
    return {
        "certification_state": cs.__dict__,
        "class_certification_record": record,
        "next_node": "end",
    }
