"""Frame fabrication state machine — ADR-2605252500 L1.

HSLA-590 / HSLA-780 ladder-frame robotic MIG/MAG welding. Straightness
< 1 mm/m. ≥2 robot witness on critical welds (G4).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FramePhase(Enum):
    INIT = "init"
    STEEL_LOT_VERIFIED = "steel_lot_verified"
    RAILS_POSITIONED = "rails_positioned"
    CROSS_MEMBERS_WELDED = "cross_members_welded"
    STRAIGHTNESS_QA_PASSED = "straightness_qa_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class FrameState:
    phase: FramePhase
    chassisId: str
    completionPct: int
    steelLot: dict[str, Any] | None = None
    railPositions: list[dict[str, Any]] | None = None
    weldPasses: list[dict[str, Any]] | None = None
    straightnessMmPerM: float | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_steel_lot_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = FrameState(**state.get("frame_state", {}))
    s.steelLot = {
        "grade": "HSLA-780",
        "lotId": "HSLA780-2026-05-LOT-0042",
        "certCid": "bafkreihsla...",
        "yieldStrengthMpa": 780,
        "tensileStrengthMpa": 850,
    }
    s.phase = FramePhase.STEEL_LOT_VERIFIED
    s.completionPct = 15
    return {"frame_state": s.__dict__, "next_node": "position"}


def transition_to_rails_positioned(state: dict[str, Any]) -> dict[str, Any]:
    s = FrameState(**state.get("frame_state", {}))
    s.railPositions = [
        {"rail": "left_long", "lengthMm": 9500, "offsetMm": 0},
        {"rail": "right_long", "lengthMm": 9500, "offsetMm": 1100},
    ]
    s.phase = FramePhase.RAILS_POSITIONED
    s.completionPct = 35
    return {"frame_state": s.__dict__, "next_node": "weld"}


def transition_to_cross_members_welded(state: dict[str, Any]) -> dict[str, Any]:
    s = FrameState(**state.get("frame_state", {}))
    s.weldPasses = [
        {"crossMemberIdx": 0, "process": "MIG-multi-pass", "passes": 3, "ipfsCid": "bafkreiweld0..."},
        {"crossMemberIdx": 1, "process": "MIG-multi-pass", "passes": 3, "ipfsCid": "bafkreiweld1..."},
        {"crossMemberIdx": 2, "process": "MAG-multi-pass", "passes": 3, "ipfsCid": "bafkreiweld2..."},
    ]
    s.phase = FramePhase.CROSS_MEMBERS_WELDED
    s.completionPct = 70
    return {"frame_state": s.__dict__, "next_node": "qa"}


def transition_to_straightness_qa_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = FrameState(**state.get("frame_state", {}))
    s.straightnessMmPerM = 0.6  # spec < 1.0
    s.phase = FramePhase.STRAIGHTNESS_QA_PASSED
    s.completionPct = 90
    return {"frame_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = FrameState(**state.get("frame_state", {}))
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:kasane-unit-1", "role": "weld_lead",
         "timestamp": "2026-05-26T08:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-precision-unit-1", "role": "metrology",
         "timestamp": "2026-05-26T08:00:05Z", "signature": "..."},
    ]
    s.phase = FramePhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.frameAttestation",
        "chassisId": s.chassisId,
        "steelLot": s.steelLot,
        "railPositions": s.railPositions,
        "weldPasses": s.weldPasses,
        "straightnessMmPerM": s.straightnessMmPerM,
        "specStraightnessLimitMmPerM": 1.0,
        "accept": (s.straightnessMmPerM or 0) < 1.0,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T08:00:10Z",
    }
    return {"frame_state": s.__dict__, "frame_attestation": record, "next_node": "end"}
