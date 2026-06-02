"""Bogie assembly state machine — ADR-2605252600 L2.

Cast steel bogie frame (igata Wave 2 R3+ source) + air spring + tread brake +
axle + wheel set + traction motor (PMSM / IM).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BogiePhase(Enum):
    INIT = "init"
    FRAME_PREPARED = "frame_prepared"
    WHEEL_SET_MOUNTED = "wheel_set_mounted"
    MOTOR_INSTALLED = "motor_installed"
    BRAKE_INTEGRATED = "brake_integrated"
    AIR_SPRING_INSTALLED = "air_spring_installed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class BogieState:
    phase: BogiePhase
    trainsetId: str
    bogieIndex: int
    completionPct: int
    frameLot: dict[str, Any] | None = None
    wheelSetLot: dict[str, Any] | None = None
    motorLot: dict[str, Any] | None = None
    brakeSystem: dict[str, Any] | None = None
    airSpring: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_frame_prepared(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.frameLot = {"source": "external-cast-steel-R1", "note": "R3+ source from igata Wave 2", "lotId": "BOGIE-FRAME-0011"}
    s.phase = BogiePhase.FRAME_PREPARED
    s.completionPct = 15
    return {"bogie_state": s.__dict__, "next_node": "wheel"}


def transition_to_wheel_set_mounted(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.wheelSetLot = {"lotId": "WHEELSET-0011", "wheelDiameterMm": 860, "axleLoadT": 17}
    s.phase = BogiePhase.WHEEL_SET_MOUNTED
    s.completionPct = 35
    return {"bogie_state": s.__dict__, "next_node": "motor"}


def transition_to_motor_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.motorLot = {"type": "PMSM", "powerKw": 305, "ratedVoltageV": 1100, "lotId": "TRACTION-MOTOR-0011"}
    s.phase = BogiePhase.MOTOR_INSTALLED
    s.completionPct = 60
    return {"bogie_state": s.__dict__, "next_node": "brake"}


def transition_to_brake_integrated(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.brakeSystem = {"type": "tread-disc-hybrid", "regenerativeAllowed": True, "emergencyDecelMsps": 1.3}
    s.phase = BogiePhase.BRAKE_INTEGRATED
    s.completionPct = 78
    return {"bogie_state": s.__dict__, "next_node": "air"}


def transition_to_air_spring_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.airSpring = {"primary": "coil", "secondary": "air-bellows", "levelingControl": True}
    s.phase = BogiePhase.AIR_SPRING_INSTALLED
    s.completionPct = 90
    return {"bogie_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = BogieState(**state.get("bogie_state", {}))
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:wadasa-unit-1", "role": "bogie_lead",
         "timestamp": "2026-05-26T10:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-precision-unit-1", "role": "alignment",
         "timestamp": "2026-05-26T10:00:05Z", "signature": "..."},
    ]
    s.phase = BogiePhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.bogieAttestation",
        "trainsetId": s.trainsetId,
        "bogieIndex": s.bogieIndex,
        "frameLot": s.frameLot,
        "wheelSetLot": s.wheelSetLot,
        "motorLot": s.motorLot,
        "brakeSystem": s.brakeSystem,
        "airSpring": s.airSpring,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T10:00:10Z",
    }
    return {"bogie_state": s.__dict__, "bogie_attestation": record, "next_node": "end"}
