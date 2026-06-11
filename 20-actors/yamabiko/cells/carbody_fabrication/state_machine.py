"""Carbody fabrication state machine — ADR-2605252600 L1.

FSW (Friction Stir Welding) Al 6N01 / A6005C double-skin extrusion carbody.
≥2 robot witness (G4). Hitachi A-Train class methodology.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CarbodyPhase(Enum):
    INIT = "init"
    EXTRUSION_VERIFIED = "extrusion_verified"
    FSW_SEAMS_COMPLETE = "fsw_seams_complete"
    SPOT_WELDS_COMPLETE = "spot_welds_complete"
    DIMENSIONAL_QA_PASSED = "dimensional_qa_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CarbodyState:
    phase: CarbodyPhase
    trainsetId: str
    carIndex: int
    completionPct: int
    extrusionLot: dict[str, Any] | None = None
    fswSeams: list[dict[str, Any]] | None = None
    spotWelds: dict[str, Any] | None = None
    dimensionalQa: dict[str, Any] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_extrusion_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = CarbodyState(**state.get("carbody_state", {}))
    s.extrusionLot = {
        "alloy": "Al-6N01",
        "lotId": "AL6N01-2026-05-LOT-0042",
        "doubleSkin": True,
        "thicknessMm": 2.5,
        "certCid": "bafkreialextrude...",
    }
    s.phase = CarbodyPhase.EXTRUSION_VERIFIED
    s.completionPct = 15
    return {"carbody_state": s.__dict__, "next_node": "fsw"}


def transition_to_fsw_seams_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CarbodyState(**state.get("carbody_state", {}))
    s.fswSeams = [
        {"seam": "side-floor", "lengthM": 24.5, "tool_rpm": 800, "feed_mm_per_min": 600, "videoCid": "bafkreifsw1..."},
        {"seam": "side-roof", "lengthM": 24.5, "tool_rpm": 800, "feed_mm_per_min": 600, "videoCid": "bafkreifsw2..."},
        {"seam": "end-front", "lengthM": 3.2, "tool_rpm": 750, "feed_mm_per_min": 550, "videoCid": "bafkreifsw3..."},
        {"seam": "end-rear", "lengthM": 3.2, "tool_rpm": 750, "feed_mm_per_min": 550, "videoCid": "bafkreifsw4..."},
    ]
    s.phase = CarbodyPhase.FSW_SEAMS_COMPLETE
    s.completionPct = 50
    return {"carbody_state": s.__dict__, "next_node": "spot"}


def transition_to_spot_welds_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = CarbodyState(**state.get("carbody_state", {}))
    s.spotWelds = {"totalSpots": 1800, "robotPasses": 3, "videoCid": "bafkreispot..."}
    s.phase = CarbodyPhase.SPOT_WELDS_COMPLETE
    s.completionPct = 70
    return {"carbody_state": s.__dict__, "next_node": "qa"}


def transition_to_dimensional_qa_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = CarbodyState(**state.get("carbody_state", {}))
    s.dimensionalQa = {
        "lengthMm": 25000, "lengthSpecMm": 25000, "lengthTolMm": 5,
        "widthMm": 3380, "widthSpecMm": 3380, "widthTolMm": 3,
        "heightMm": 3650, "heightSpecMm": 3650, "heightTolMm": 3,
        "accept": True,
    }
    s.phase = CarbodyPhase.DIMENSIONAL_QA_PASSED
    s.completionPct = 90
    return {"carbody_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = CarbodyState(**state.get("carbody_state", {}))
    s.robotSignatures = [
        {"robotDid": "did:web:etzhayyim.com:tsugite-unit-1", "role": "fsw_lead",
         "timestamp": "2026-05-26T08:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-precision-unit-1", "role": "metrology",
         "timestamp": "2026-05-26T08:00:05Z", "signature": "..."},
    ]
    s.phase = CarbodyPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.carbodyAttestation",
        "trainsetId": s.trainsetId,
        "carIndex": s.carIndex,
        "extrusionLot": s.extrusionLot,
        "fswSeams": s.fswSeams,
        "spotWelds": s.spotWelds,
        "dimensionalQa": s.dimensionalQa,
        "attestingRobots": s.robotSignatures,
        "recordedAt": "2026-05-26T08:00:10Z",
    }
    return {"carbody_state": s.__dict__, "carbody_attestation": record, "next_node": "end"}
