"""Packaging state machine - ADR-2605242500."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PackagingPhase(Enum):
    INIT = "init"
    DIE_ATTACHED = "die_attached"
    WIRE_BONDING_COMPLETE = "wire_bonding_complete"
    ENCAPSULATION_COMPLETE = "encapsulation_complete"
    PACKAGE_TESTED = "package_tested"


@dataclass
class PackagingState:
    phase: PackagingPhase
    packageId: str
    completionPct: int
    dieAttachData: dict[str, Any] | None = None
    wireBondData: dict[str, Any] | None = None
    encapsulationData: dict[str, Any] | None = None
    finalTestData: dict[str, Any] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_die_attached(state: dict[str, Any]) -> dict[str, Any]:
    ps = PackagingState(**state.get("packaging_state", {}))

    mock_attach = {
        "die_size_mm": 5.2,
        "substrate_material": "FR4",
        "adhesive_type": "epoxy",
        "cure_temperature_c": 150,
        "cure_time_hours": 2,
        "die_placement_accuracy_um": 50,
    }

    ps.phase = PackagingPhase.DIE_ATTACHED
    ps.dieAttachData = mock_attach
    ps.completionPct = 25

    return {"packaging_state": ps.__dict__, "next_node": "wire_bond"}


def transition_to_wire_bonding_complete(state: dict[str, Any]) -> dict[str, Any]:
    ps = PackagingState(**state.get("packaging_state", {}))

    mock_bonding = {
        "wire_material": "gold",
        "wire_diameter_um": 25,
        "bond_count": 256,
        "bond_pull_force_grams": 8.5,
        "bond_shear_force_grams": 6.2,
        "bond_quality_pass_rate_pct": 99.8,
    }

    ps.phase = PackagingPhase.WIRE_BONDING_COMPLETE
    ps.wireBondData = mock_bonding
    ps.completionPct = 50

    return {"packaging_state": ps.__dict__, "next_node": "encapsulate"}


def transition_to_encapsulation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ps = PackagingState(**state.get("packaging_state", {}))

    mock_encap = {
        "encapsulant_material": "epoxy_mold_compound",
        "mold_temperature_c": 175,
        "mold_pressure_bar": 85,
        "mold_time_seconds": 120,
        "encapsulant_thickness_mm": 1.8,
        "voids_detected_pct": 0.2,
        "moisture_absorption_pct": 0.15,
    }

    ps.phase = PackagingPhase.ENCAPSULATION_COMPLETE
    ps.encapsulationData = mock_encap
    ps.completionPct = 75

    return {"packaging_state": ps.__dict__, "next_node": "final_test"}


def transition_to_package_tested(state: dict[str, Any]) -> dict[str, Any]:
    ps = PackagingState(**state.get("packaging_state", {}))

    mock_final = {
        "visual_inspection": "pass",
        "dimensional_check": "pass",
        "electrical_continuity": "pass",
        "temperature_cycling": "pass",
        "humidity_stress": "pass",
        "package_quality_grade": "A",
    }

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-5",
            "role": "packaging_executor",
            "timestamp": "2026-05-26T17:15:45Z",
            "signature": "vV1wW2xX3yY4zZ5a...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-4",
            "role": "package_inspector",
            "timestamp": "2026-05-26T17:15:50Z",
            "signature": "bB6cC7dD8eE9fF0g...",
        },
    ]

    ps.phase = PackagingPhase.PACKAGE_TESTED
    ps.finalTestData = mock_final
    ps.robotSignatures = mock_sigs
    ps.completionPct = 100

    return {
        "packaging_state": ps.__dict__,
        "packaging_record": {
            "packageId": ps.packageId,
            "dieAttach": ps.dieAttachData,
            "wireBond": ps.wireBondData,
            "encapsulation": ps.encapsulationData,
            "finalTest": ps.finalTestData,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
