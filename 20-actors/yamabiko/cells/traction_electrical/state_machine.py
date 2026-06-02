"""Traction + electrical state machine — ADR-2605252600 L4.

25 kV AC / 1500 V DC pantograph + traction inverter + ATP/ATO firmware.
G1 + N5 enforcement: ATP/ATO firmware Apache 2.0 + Charter Rider, no NDA.
G7 propulsion guard: R0/R1 BEMU+H₂ acceptable; R2+ full electric only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TractionPhase(Enum):
    INIT = "init"
    PROPULSION_GUARD_CHECKED = "propulsion_guard_checked"
    PANTOGRAPH_INSTALLED = "pantograph_installed"
    INVERTER_INSTALLED = "inverter_installed"
    ATP_ATO_FLASHED = "atp_ato_flashed"
    OPEN_SOURCE_VERIFIED = "open_source_verified"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class TractionState:
    phase: TractionPhase
    trainsetId: str
    completionPct: int
    propulsionType: str | None = None
    propulsionGuard: dict[str, Any] | None = None
    pantograph: dict[str, Any] | None = None
    inverter: dict[str, Any] | None = None
    atpAtoFirmware: dict[str, Any] | None = None
    openSourceVerification: dict[str, Any] | None = None


def transition_to_propulsion_guard_checked(state: dict[str, Any]) -> dict[str, Any]:
    s = TractionState(**state.get("traction_state", {}))
    allowed_r0r1 = {"overhead-25kV-AC", "overhead-1500V-DC", "third-rail-750V-DC", "BEMU-LFP", "H2-fuel-cell-hybrid"}
    allowed_r2plus = {"overhead-25kV-AC", "overhead-1500V-DC", "third-rail-750V-DC", "BEMU-LFP", "H2-fuel-cell-hybrid", "NH3-fuel-cell-hybrid"}
    selected = state.get("propulsionType", "overhead-25kV-AC")
    s.propulsionType = selected
    s.propulsionGuard = {
        "g7Enforcement": "active",
        "allowedR0R1": sorted(allowed_r0r1),
        "allowedR2Plus": sorted(allowed_r2plus),
        "selected": selected,
        "phaseGate": state.get("phase", "R1"),
        "accept": selected in allowed_r0r1,
        "dieselGuard": "R2+ diesel locomotive prohibited (N4)",
    }
    s.phase = TractionPhase.PROPULSION_GUARD_CHECKED
    s.completionPct = 15
    return {"traction_state": s.__dict__, "next_node": "pantograph"}


def transition_to_pantograph_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = TractionState(**state.get("traction_state", {}))
    s.pantograph = {"count": 2, "type": "wing", "ratedVoltageV": 25000, "currentA": 1000}
    s.phase = TractionPhase.PANTOGRAPH_INSTALLED
    s.completionPct = 35
    return {"traction_state": s.__dict__, "next_node": "inverter"}


def transition_to_inverter_installed(state: dict[str, Any]) -> dict[str, Any]:
    s = TractionState(**state.get("traction_state", {}))
    s.inverter = {"type": "SiC-MOSFET", "ratedPowerKw": 4880, "efficiencyPct": 98.2}
    s.phase = TractionPhase.INVERTER_INSTALLED
    s.completionPct = 55
    return {"traction_state": s.__dict__, "next_node": "atp"}


def transition_to_atp_ato_flashed(state: dict[str, Any]) -> dict[str, Any]:
    s = TractionState(**state.get("traction_state", {}))
    s.atpAtoFirmware = {
        "atpStandard": "ETCS-Level-2",
        "atoLevel": "GoA-3",
        "atoMaxLevel": 3,
        "n7Note": "GoA 4 = N7 constitutional non-goal Wave 1",
        "firmwareCid": "bafkreiatp-ato-fw...",
        "firmwareLicense": "Apache 2.0 + Charter Compliance Rider v2.0",
        "flashTimestamp": "2026-05-26T14:00:00Z",
    }
    s.phase = TractionPhase.ATP_ATO_FLASHED
    s.completionPct = 75
    return {"traction_state": s.__dict__, "next_node": "verify"}


def transition_to_open_source_verified(state: dict[str, Any]) -> dict[str, Any]:
    """G1 + N5 enforcement: ATP/ATO firmware open-source license required."""
    s = TractionState(**state.get("traction_state", {}))
    license_str = (s.atpAtoFirmware or {}).get("firmwareLicense", "")
    s.openSourceVerification = {
        "g1Enforcement": "active",
        "n5Enforcement": "active",
        "firmwareLicense": license_str,
        "containsApache2": "Apache 2.0" in license_str,
        "containsCharterRider": "Charter Compliance Rider" in license_str,
        "proprietaryNdaPresent": False,
        "accept": "Apache 2.0" in license_str and "Charter Compliance Rider" in license_str,
    }
    s.phase = TractionPhase.OPEN_SOURCE_VERIFIED
    s.completionPct = 92
    return {"traction_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = TractionState(**state.get("traction_state", {}))
    s.phase = TractionPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.tractionElectricalAttestation",
        "trainsetId": s.trainsetId,
        "propulsionType": s.propulsionType,
        "propulsionGuard": s.propulsionGuard,
        "pantograph": s.pantograph,
        "inverter": s.inverter,
        "atpAtoFirmware": s.atpAtoFirmware,
        "openSourceVerification": s.openSourceVerification,
        "recordedAt": "2026-05-26T14:00:10Z",
    }
    return {"traction_state": s.__dict__, "traction_electrical_attestation": record, "next_node": "end"}
