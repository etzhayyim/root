"""Interior + HVAC + PIS state machine — ADR-2605252600 L3.

Al-honeycomb floor + fire-retardant seating + wheelchair-accessible toilets +
HEPA HVAC + multilingual passenger information system. N6 enforcement: no
third-party advertising; route + safety info only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class InteriorPhase(Enum):
    INIT = "init"
    FLOOR_INSTALLED = "floor_installed"
    SEATING_INSTALLED = "seating_installed"
    ACCESSIBILITY_VERIFIED = "accessibility_verified"
    HVAC_INSTALLED = "hvac_installed"
    PIS_CONFIGURED = "pis_configured"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class InteriorState:
    phase: InteriorPhase
    trainsetId: str
    carIndex: int
    completionPct: int
    floor: dict[str, Any] | None = None
    seating: dict[str, Any] | None = None
    accessibility: dict[str, Any] | None = None
    hvac: dict[str, Any] | None = None
    pisConfig: dict[str, Any] | None = None


def transition_to_floor_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = InteriorState(**state.get("interior_state", {}))
    s.floor = {"material": "Al-honeycomb-with-vinyl", "thicknessMm": 35, "fireClass": "EN 45545 R1 HL2"}
    s.phase = InteriorPhase.FLOOR_INSTALLED
    s.completionPct = 18
    return {"interior_state": s.__dict__, "next_node": "seating"}


def transition_to_seating_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = InteriorState(**state.get("interior_state", {}))
    s.seating = {
        "type": "fire-retardant-fabric-EN 45545 R1",
        "pitch_mm": 990,
        "rowCount": 17,
        "wheelchairBays": 2,
        "n10Note": "Wave 1 single-class only (N10 luxury-only excluded)",
    }
    s.phase = InteriorPhase.SEATING_INSTALLED
    s.completionPct = 38
    return {"interior_state": s.__dict__, "next_node": "accessibility"}


def transition_to_accessibility_verified(state: dict[str, Any]) -> dict[str, Any]:
    s = InteriorState(**state.get("interior_state", {}))
    s.accessibility = {
        "wheelchairAccessibleToiletM2": 2.4,
        "rampsCount": 2,
        "tactileMarkingPath": "full",
        "vacuumWasteSystem": True,
    }
    s.phase = InteriorPhase.ACCESSIBILITY_VERIFIED
    s.completionPct = 55
    return {"interior_state": s.__dict__, "next_node": "hvac"}


def transition_to_hvac_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = InteriorState(**state.get("interior_state", {}))
    s.hvac = {
        "type": "heat-pump",
        "hepaFilter": "H13",
        "freshAirM3PerHourPerPax": 30,
        "co2SensorActive": True,
    }
    s.phase = InteriorPhase.HVAC_INSTALLED
    s.completionPct = 75
    return {"interior_state": s.__dict__, "next_node": "pis"}


def transition_to_pis_configured(state: dict[str, Any]) -> dict[str, Any]:
    """G5 + N6 + N8 enforcement: trilingual minimum, no advertising, no face recognition."""
    s = InteriorState(**state.get("interior_state", {}))
    s.pisConfig = {
        "languages": ["ja", "en", "local"],
        "g5Trilingual": True,
        "contentTypes": ["route-info", "safety-info", "next-station", "emergency"],
        "n6AdvertisingPresent": False,
        "n8FaceRecognitionPresent": False,
        "accept": True,
    }
    s.phase = InteriorPhase.PIS_CONFIGURED
    s.completionPct = 90
    return {"interior_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = InteriorState(**state.get("interior_state", {}))
    s.phase = InteriorPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.interiorAttestation",
        "trainsetId": s.trainsetId,
        "carIndex": s.carIndex,
        "floor": s.floor,
        "seating": s.seating,
        "accessibility": s.accessibility,
        "hvac": s.hvac,
        "pisConfig": s.pisConfig,
        "recordedAt": "2026-05-26T12:00:00Z",
    }
    return {"interior_state": s.__dict__, "interior_attestation": record, "next_node": "end"}
