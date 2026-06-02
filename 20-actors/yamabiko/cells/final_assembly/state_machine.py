"""Final assembly state machine — ADR-2605252600 L5a.

Carbody + bogie + interior + traction electrical marriage + cab + livery.
≥2 robot witness on critical fasteners (G4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FinalPhase(Enum):
    INIT = "init"
    INPUTS_VERIFIED = "inputs_verified"
    BOGIE_CARBODY_MARRIED = "bogie_carbody_married"
    CAB_INTERIOR_INSTALLED = "cab_interior_installed"
    LIVERY_APPLIED = "livery_applied"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class FinalState:
    phase: FinalPhase
    trainsetId: str
    completionPct: int
    inputs: dict[str, Any] | None = None
    marriage: dict[str, Any] | None = None
    livery: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_inputs_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = FinalState(**state.get("final_state", {}))
    s.inputs = {
        "carbodyCids": ["bafkreicar1...", "bafkreicar2...", "bafkreicar3...", "bafkreicar4..."],
        "bogieCids": ["bafkreibog1...", "bafkreibog2...", "bafkreibog3...", "bafkreibog4...", "bafkreibog5...", "bafkreibog6...", "bafkreibog7...", "bafkreibog8..."],
        "interiorCids": ["bafkreiint1...", "bafkreiint2...", "bafkreiint3...", "bafkreiint4..."],
        "tractionCid": "bafkreitr...",
    }
    s.phase = FinalPhase.INPUTS_VERIFIED
    s.completionPct = 15
    return {"final_state": s.__dict__, "next_node": "marriage"}


def transition_to_bogie_carbody_married(state: dict[str, Any]) -> dict[str, Any]:
    s = FinalState(**state.get("final_state", {}))
    s.marriage = {
        "carCount": 4,
        "bogiesPerCar": 2,
        "marriageFastenerTorqueNm": 850,
        "marriageFastenerSpecNm": 850,
    }
    s.phase = FinalPhase.BOGIE_CARBODY_MARRIED
    s.completionPct = 50
    return {"final_state": s.__dict__, "next_node": "cab"}


def transition_to_cab_interior_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = FinalState(**state.get("final_state", {}))
    s.phase = FinalPhase.CAB_INTERIOR_INSTALLED
    s.completionPct = 75
    return {"final_state": s.__dict__, "next_node": "livery"}


def transition_to_livery_applied(state: dict[str, Any]) -> dict[str, Any]:
    s = FinalState(**state.get("final_state", {}))
    s.livery = {
        "scheme": "OEM-default-white-with-route-band",
        "n6AdvertisingFreeAccept": True,
        "vocGPerL": 88,
    }
    s.phase = FinalPhase.LIVERY_APPLIED
    s.completionPct = 90
    return {"final_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = FinalState(**state.get("final_state", {}))
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:otete-heavy-unit-1", "role": "marriage_lead",
         "timestamp": "2026-05-26T16:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-precision-unit-1", "role": "alignment",
         "timestamp": "2026-05-26T16:00:05Z", "signature": "..."},
    ]
    s.phase = FinalPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.finalAssemblyAttestation",
        "trainsetId": s.trainsetId,
        "inputs": s.inputs,
        "marriage": s.marriage,
        "livery": s.livery,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T16:00:10Z",
    }
    return {"final_state": s.__dict__, "final_assembly_attestation": record, "next_node": "end"}
