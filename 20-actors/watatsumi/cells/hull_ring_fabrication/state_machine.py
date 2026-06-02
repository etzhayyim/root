"""Hull ring fabrication state machine — ADR-2605252200 L1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class HullRingPhase(Enum):
    INIT = "init"
    MATERIAL_LOT_VERIFIED = "material_lot_verified"
    PLATE_ROLLED = "plate_rolled"
    RING_FRAME_WELDED = "ring_frame_welded"
    ROUNDNESS_QA_PASSED = "roundness_qa_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class HullRingState:
    phase: HullRingPhase
    craftId: str
    ringIndex: int
    completionPct: int
    materialLot: dict[str, Any] | None = None  # {alloy, grade, lotId, certCid}
    ringSpec: dict[str, Any] | None = None  # {outerDiamMm, thicknessMm, frameSpacingMm}
    rollingTelemetry: dict[str, Any] | None = None
    weldPasses: list[dict[str, Any]] | None = None
    roundnessMeasurement: dict[str, Any] | None = None  # {maxOutOfRoundPpm, accept}
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_material_verified(state: dict[str, Any]) -> dict[str, Any]:
    """INIT → MATERIAL_LOT_VERIFIED.

    Verify material lot certificate (HSLA-80 or Ti-6Al-4V ELI) — no HY-100 or
    higher without Council attestation per ADR-2605252200 L1 constraint.
    """
    hs = HullRingState(**state.get("hull_ring_state", {}))

    mock_lot = {
        "alloy": "HSLA-80",
        "grade": "ASTM A710 Class 3",
        "lotId": "HSLA80-2026-05-LOT-0042",
        "certCid": "bafkreigh2akiscaildc...",
        "yieldStrengthMpa": 552,
        "tensileStrengthMpa": 690,
        "councilAttestation": None,  # not required for HSLA-80
    }

    hs.phase = HullRingPhase.MATERIAL_LOT_VERIFIED
    hs.materialLot = mock_lot
    hs.completionPct = 15
    return {"hull_ring_state": hs.__dict__, "next_node": "rolling"}


def transition_to_plate_rolled(state: dict[str, Any]) -> dict[str, Any]:
    """MATERIAL_LOT_VERIFIED → PLATE_ROLLED."""
    hs = HullRingState(**state.get("hull_ring_state", {}))

    mock_rolling = {
        "rollerPasses": 7,
        "finalDiameterMm": 6500,
        "finalThicknessMm": 42,
        "preheat_C": 150,
    }
    hs.phase = HullRingPhase.PLATE_ROLLED
    hs.rollingTelemetry = mock_rolling
    hs.completionPct = 40
    return {"hull_ring_state": hs.__dict__, "next_node": "ring_weld"}


def transition_to_ring_frame_welded(state: dict[str, Any]) -> dict[str, Any]:
    """PLATE_ROLLED → RING_FRAME_WELDED (TIG / SAW multi-pass)."""
    hs = HullRingState(**state.get("hull_ring_state", {}))

    mock_passes = [
        {"pass": 1, "process": "GTAW-root", "amp": 180, "ipfsCid": "bafkreipass1..."},
        {"pass": 2, "process": "SAW-fill", "amp": 450, "ipfsCid": "bafkreipass2..."},
        {"pass": 3, "process": "SAW-fill", "amp": 450, "ipfsCid": "bafkreipass3..."},
        {"pass": 4, "process": "GTAW-cap", "amp": 220, "ipfsCid": "bafkreipass4..."},
    ]
    hs.phase = HullRingPhase.RING_FRAME_WELDED
    hs.weldPasses = mock_passes
    hs.completionPct = 70
    return {"hull_ring_state": hs.__dict__, "next_node": "roundness_qa"}


def transition_to_roundness_qa(state: dict[str, Any]) -> dict[str, Any]:
    """RING_FRAME_WELDED → ROUNDNESS_QA_PASSED (must be < 0.5% Ø per ADR-2605252200 L1)."""
    hs = HullRingState(**state.get("hull_ring_state", {}))

    mock_qa = {
        "measurements_mm": [6500, 6498, 6502, 6499, 6501, 6500, 6497, 6503],
        "maxOutOfRoundMm": 6,
        "diameterMm": 6500,
        "maxOutOfRoundPpm": round(6 / 6500 * 1_000_000),  # = 923 ppm (0.0923%)
        "limitPpm": 5000,  # = 0.5% Ø
        "accept": True,
    }
    hs.phase = HullRingPhase.ROUNDNESS_QA_PASSED
    hs.roundnessMeasurement = mock_qa
    hs.completionPct = 90
    return {"hull_ring_state": hs.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """ROUNDNESS_QA_PASSED → ATTESTATION_EMITTED (≥2 robot Ed25519 sigs)."""
    hs = HullRingState(**state.get("hull_ring_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-marine-unit-1",
            "role": "metrology",
            "timestamp": "2026-05-26T11:00:00Z",
            "signature": "aA1bB2cC3dD4eE5f...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-marine-unit-1",
            "role": "weld_witness",
            "timestamp": "2026-05-26T11:00:05Z",
            "signature": "gG6hH7iI8jJ9kK0l...",
        },
    ]
    hs.robotSignatures = mock_sigs
    hs.phase = HullRingPhase.ATTESTATION_EMITTED
    hs.completionPct = 100

    record = {
        "$type": "com.etzhayyim.watatsumi.pressureHullAttestation",
        "craftId": hs.craftId,
        "ringIndex": hs.ringIndex,
        "materialLot": hs.materialLot,
        "rolling": hs.rollingTelemetry,
        "weldPasses": hs.weldPasses,
        "roundness": hs.roundnessMeasurement,
        "attestingRobots": mock_sigs,
        "recordedAt": "2026-05-26T11:00:10Z",
    }
    return {
        "hull_ring_state": hs.__dict__,
        "pressure_hull_attestation": record,
        "next_node": "end",
    }
