"""Final marriage state machine — ADR-2605252500 L4.

Chassis lowering + cab drop + powertrain mount + electrical harness connection.
≥2 robot witness on critical fastener torque (G4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MarriagePhase(Enum):
    INIT = "init"
    INPUTS_VERIFIED = "inputs_verified"
    CHASSIS_LOWERED = "chassis_lowered"
    CAB_DROPPED = "cab_dropped"
    POWERTRAIN_MOUNTED = "powertrain_mounted"
    HARNESS_CONNECTED = "harness_connected"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class MarriageState:
    phase: MarriagePhase
    chassisId: str
    completionPct: int
    inputs: dict[str, Any] | None = None
    criticalTorques: list[dict[str, Any]] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_inputs_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    s.inputs = {
        "frameAttestationCid": "bafkreiframeatt...",
        "powertrainAttestationCid": "bafkreiptatt...",
        "cabBodyAttestationCid": "bafkreicabatt...",
    }
    s.phase = MarriagePhase.INPUTS_VERIFIED
    s.completionPct = 15
    return {"marriage_state": s.__dict__, "next_node": "lower"}


def transition_to_chassis_lowered(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    s.phase = MarriagePhase.CHASSIS_LOWERED
    s.completionPct = 35
    return {"marriage_state": s.__dict__, "next_node": "cab"}


def transition_to_cab_dropped(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    s.criticalTorques = [
        {"fastener": "cab_mount_1", "torqueNm": 320, "specNm": 320, "tolerancePct": 5},
        {"fastener": "cab_mount_2", "torqueNm": 315, "specNm": 320, "tolerancePct": 5},
        {"fastener": "cab_mount_3", "torqueNm": 322, "specNm": 320, "tolerancePct": 5},
        {"fastener": "cab_mount_4", "torqueNm": 318, "specNm": 320, "tolerancePct": 5},
    ]
    s.phase = MarriagePhase.CAB_DROPPED
    s.completionPct = 55
    return {"marriage_state": s.__dict__, "next_node": "powertrain"}


def transition_to_powertrain_mounted(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    extra = [
        {"fastener": "engine_mount_left", "torqueNm": 450, "specNm": 450, "tolerancePct": 5},
        {"fastener": "engine_mount_right", "torqueNm": 448, "specNm": 450, "tolerancePct": 5},
        {"fastener": "transmission_mount", "torqueNm": 280, "specNm": 280, "tolerancePct": 5},
    ]
    s.criticalTorques = (s.criticalTorques or []) + extra
    s.phase = MarriagePhase.POWERTRAIN_MOUNTED
    s.completionPct = 75
    return {"marriage_state": s.__dict__, "next_node": "harness"}


def transition_to_harness_connected(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    s.phase = MarriagePhase.HARNESS_CONNECTED
    s.completionPct = 90
    return {"marriage_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = MarriageState(**state.get("marriage_state", {}))
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:otete-heavy-unit-1", "role": "marriage_lead",
         "timestamp": "2026-05-26T13:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-precision-unit-1", "role": "alignment_witness",
         "timestamp": "2026-05-26T13:00:05Z", "signature": "..."},
    ]
    s.phase = MarriagePhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.marriageAttestation",
        "chassisId": s.chassisId,
        "inputs": s.inputs,
        "criticalTorques": s.criticalTorques,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T13:00:10Z",
    }
    return {"marriage_state": s.__dict__, "marriage_attestation": record, "next_node": "end"}
