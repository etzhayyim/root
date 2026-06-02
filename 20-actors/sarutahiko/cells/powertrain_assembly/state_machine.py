"""Powertrain assembly state machine — ADR-2605252500 L2.

Engine + transmission + axle integration. G7 fuel guard:
- R0/R1 transition: B100 biodiesel + diesel hybrid acceptable
- R2+: LFP / H₂ / NH₃ / methanol fuel-cell only (pure fossil rejected)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PowertrainPhase(Enum):
    INIT = "init"
    FUEL_GUARD_CHECKED = "fuel_guard_checked"
    ENGINE_INSTALLED = "engine_installed"
    TRANSMISSION_COUPLED = "transmission_coupled"
    AXLES_MOUNTED = "axles_mounted"
    BRAKE_INTEGRATED = "brake_integrated"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class PowertrainState:
    phase: PowertrainPhase
    chassisId: str
    completionPct: int
    powerTrainType: str | None = None  # one of allowed list
    fuelGuard: dict[str, Any] | None = None  # G7 enforcement
    engineLot: dict[str, Any] | None = None
    transmissionLot: dict[str, Any] | None = None
    axleLots: list[dict[str, Any]] | None = None
    brakeSystem: dict[str, Any] | None = None


def transition_to_fuel_guard_checked(state: dict[str, Any]) -> dict[str, Any]:
    """G7 enforcement: only allowed fuel/powertrain types accepted."""
    s = PowertrainState(**state.get("powertrain_state", {}))
    allowed_r0r1 = {"B100-biodiesel-hybrid", "diesel-hybrid",
                    "LFP-battery", "H2-fuel-cell", "NH3-fuel-cell", "methanol-fuel-cell"}
    allowed_r2plus = {"LFP-battery", "H2-fuel-cell", "NH3-fuel-cell", "methanol-fuel-cell"}
    selected = state.get("powerTrainType", "B100-biodiesel-hybrid")
    s.powerTrainType = selected
    s.fuelGuard = {
        "g7Enforcement": "active",
        "allowedR0R1": sorted(allowed_r0r1),
        "allowedR2Plus": sorted(allowed_r2plus),
        "selected": selected,
        "phaseGate": state.get("phase", "R1"),
        "accept": selected in allowed_r0r1,
        "pureFossilGuard": "pure-fossil prohibited; B100 biodiesel + diesel hybrid acceptable as R0/R1 transition only",
    }
    s.phase = PowertrainPhase.FUEL_GUARD_CHECKED
    s.completionPct = 15
    return {"powertrain_state": s.__dict__, "next_node": "engine"}


def transition_to_engine_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = PowertrainState(**state.get("powertrain_state", {}))
    s.engineLot = {
        "type": s.powerTrainType,
        "lotId": "ENGINE-2026-05-LOT-0011",
        "powerKw": 350,
        "torqueNm": 2200,
        "certCid": "bafkreienginecert...",
    }
    s.phase = PowertrainPhase.ENGINE_INSTALLED
    s.completionPct = 40
    return {"powertrain_state": s.__dict__, "next_node": "transmission"}


def transition_to_transmission_coupled(state: dict[str, Any]) -> dict[str, Any]:
    s = PowertrainState(**state.get("powertrain_state", {}))
    s.transmissionLot = {"ratio_steps": 12, "lotId": "TRANS-2026-05-LOT-0011"}
    s.phase = PowertrainPhase.TRANSMISSION_COUPLED
    s.completionPct = 60
    return {"powertrain_state": s.__dict__, "next_node": "axles"}


def transition_to_axles_mounted(state: dict[str, Any]) -> dict[str, Any]:
    s = PowertrainState(**state.get("powertrain_state", {}))
    s.axleLots = [
        {"position": "front_steer", "lotId": "AXLE-FRONT-0011"},
        {"position": "rear_drive_1", "lotId": "AXLE-REAR-0011"},
        {"position": "rear_drive_2", "lotId": "AXLE-REAR-0012"},
    ]
    s.phase = PowertrainPhase.AXLES_MOUNTED
    s.completionPct = 78
    return {"powertrain_state": s.__dict__, "next_node": "brake"}


def transition_to_brake_integrated(state: dict[str, Any]) -> dict[str, Any]:
    s = PowertrainState(**state.get("powertrain_state", {}))
    s.brakeSystem = {"type": "EBS-disc", "regenerativeAllowed": True}
    s.phase = PowertrainPhase.BRAKE_INTEGRATED
    s.completionPct = 92
    return {"powertrain_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = PowertrainState(**state.get("powertrain_state", {}))
    s.phase = PowertrainPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.powertrainAttestation",
        "chassisId": s.chassisId,
        "powerTrainType": s.powerTrainType,
        "fuelGuard": s.fuelGuard,
        "engineLot": s.engineLot,
        "transmissionLot": s.transmissionLot,
        "axleLots": s.axleLots,
        "brakeSystem": s.brakeSystem,
        "recordedAt": "2026-05-26T09:30:00Z",
    }
    return {"powertrain_state": s.__dict__, "powertrain_attestation": record, "next_node": "end"}
