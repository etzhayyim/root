"""Section assembly state machine — ADR-2605252200 L2.

Stack N pressure-hull rings into a 10–15 m section, install internal frames,
bulkheads, and hull penetrators (hatches, sensor heads, snorkel). No weapon
mounts (N1).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SectionAssemblyPhase(Enum):
    INIT = "init"
    RINGS_VERIFIED = "rings_verified"
    RINGS_STACKED = "rings_stacked"
    INTERNAL_FRAMES_INSTALLED = "internal_frames_installed"
    PENETRATORS_INSTALLED = "penetrators_installed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class SectionAssemblyState:
    phase: SectionAssemblyPhase
    craftId: str
    sectionIndex: int
    completionPct: int
    ringAttestations: list[dict[str, Any]] | None = None
    sectionLengthMm: int | None = None
    bulkheads: list[dict[str, Any]] | None = None
    penetrators: list[dict[str, Any]] | None = None
    weaponMountCheck: dict[str, Any] | None = None  # N1 enforcement
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_rings_verified(state: dict[str, Any]) -> dict[str, Any]:
    sa = SectionAssemblyState(**state.get("section_assembly_state", {}))
    mock_rings = [
        {"ringIndex": i, "attestationCid": f"bafkreiring{i}..."}
        for i in range(4)
    ]
    sa.phase = SectionAssemblyPhase.RINGS_VERIFIED
    sa.ringAttestations = mock_rings
    sa.completionPct = 15
    return {"section_assembly_state": sa.__dict__, "next_node": "stack"}


def transition_to_rings_stacked(state: dict[str, Any]) -> dict[str, Any]:
    sa = SectionAssemblyState(**state.get("section_assembly_state", {}))
    sa.phase = SectionAssemblyPhase.RINGS_STACKED
    sa.sectionLengthMm = 12000
    sa.completionPct = 40
    return {"section_assembly_state": sa.__dict__, "next_node": "frames"}


def transition_to_frames_installed(state: dict[str, Any]) -> dict[str, Any]:
    sa = SectionAssemblyState(**state.get("section_assembly_state", {}))
    sa.phase = SectionAssemblyPhase.INTERNAL_FRAMES_INSTALLED
    sa.bulkheads = [
        {"index": 0, "kind": "pressure-bulkhead", "positionMm": 0},
        {"index": 1, "kind": "watertight-door", "positionMm": 6000},
        {"index": 2, "kind": "pressure-bulkhead", "positionMm": 12000},
    ]
    sa.completionPct = 65
    return {"section_assembly_state": sa.__dict__, "next_node": "penetrators"}


def transition_to_penetrators_installed(state: dict[str, Any]) -> dict[str, Any]:
    """Install hull penetrators. N1 enforcement: no weapon mounts."""
    sa = SectionAssemblyState(**state.get("section_assembly_state", {}))
    mock_pens = [
        {"kind": "personnel-hatch", "positionMm": 1500, "diaMm": 800},
        {"kind": "sensor-head-passive-sonar", "positionMm": 3000, "diaMm": 200},
        {"kind": "acoustic-modem", "positionMm": 5000, "diaMm": 150},
        {"kind": "manipulator-mount-otete", "positionMm": 7500, "diaMm": 250},
        {"kind": "ballast-tank-vent", "positionMm": 10000, "diaMm": 100},
    ]
    forbidden_kinds = {
        "torpedo-tube", "missile-silo", "mine-laying-bay", "weapon-mount",
        "ordnance-stowage", "depth-charge-rack",
    }
    weapon_check = {
        "n1Enforcement": "active",
        "forbiddenKinds": sorted(forbidden_kinds),
        "violationsFound": [p for p in mock_pens if p["kind"] in forbidden_kinds],
        "accept": True,
    }
    sa.phase = SectionAssemblyPhase.PENETRATORS_INSTALLED
    sa.penetrators = mock_pens
    sa.weaponMountCheck = weapon_check
    sa.completionPct = 90
    return {"section_assembly_state": sa.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    sa = SectionAssemblyState(**state.get("section_assembly_state", {}))
    mock_sigs = [
        {"robotDid": "did:web:etzhayyim.com:ama-unit-1", "role": "structural",
         "timestamp": "2026-05-26T12:00:00Z", "signature": "..."},
        {"robotDid": "did:web:etzhayyim.com:mimi-marine-unit-1", "role": "metrology",
         "timestamp": "2026-05-26T12:00:05Z", "signature": "..."},
    ]
    sa.robotSignatures = mock_sigs
    sa.phase = SectionAssemblyPhase.ATTESTATION_EMITTED
    sa.completionPct = 100
    record = {
        "$type": "com.etzhayyim.watatsumi.sectionAssemblyAttestation",
        "craftId": sa.craftId,
        "sectionIndex": sa.sectionIndex,
        "ringAttestations": sa.ringAttestations,
        "sectionLengthMm": sa.sectionLengthMm,
        "bulkheads": sa.bulkheads,
        "penetrators": sa.penetrators,
        "weaponMountCheck": sa.weaponMountCheck,
        "attestingRobots": mock_sigs,
        "recordedAt": "2026-05-26T12:00:10Z",
    }
    return {
        "section_assembly_state": sa.__dict__,
        "section_assembly_attestation": record,
        "next_node": "end",
    }
