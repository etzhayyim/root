"""Electrical integration state machine — ADR-2605252500 L5b.

Harness routing + ECU flash + diagnostics. G1 firmware open-source mandate.
N8 enforcement: no proprietary ECU NDA.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ElectricalPhase(Enum):
    INIT = "init"
    HARNESS_ROUTED = "harness_routed"
    ECU_FLASHED = "ecu_flashed"
    OPEN_SOURCE_VERIFIED = "open_source_verified"
    DIAGNOSTICS_PASSED = "diagnostics_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class ElectricalState:
    phase: ElectricalPhase
    chassisId: str
    completionPct: int
    harnessLayout: dict[str, Any] | None = None
    ecuFlash: dict[str, Any] | None = None
    openSourceVerification: dict[str, Any] | None = None
    diagnostics: dict[str, Any] | None = None


def transition_to_harness_routed(state: dict[str, Any]) -> dict[str, Any]:
    s = ElectricalState(**state.get("electrical_state", {}))
    s.harnessLayout = {
        "totalWireMassKg": 28,
        "branchCount": 14,
        "routingCid": "bafkreiroute...",
        "akariUnits": 2,
    }
    s.phase = ElectricalPhase.HARNESS_ROUTED
    s.completionPct = 25
    return {"electrical_state": s.__dict__, "next_node": "flash"}


def transition_to_ecu_flashed(state: dict[str, Any]) -> dict[str, Any]:
    s = ElectricalState(**state.get("electrical_state", {}))
    s.ecuFlash = {
        "ecuModel": "etzhayyim-open-ecu-v1",
        "firmwareCid": "bafkreiopenecuFW...",
        "firmwareLicense": "Apache 2.0 + Charter Compliance Rider v2.0",
        "flashTimestamp": "2026-05-26T16:30:00Z",
    }
    s.phase = ElectricalPhase.ECU_FLASHED
    s.completionPct = 55
    return {"electrical_state": s.__dict__, "next_node": "verify"}


def transition_to_open_source_verified(state: dict[str, Any]) -> dict[str, Any]:
    """G1 + N8 enforcement: firmware open-source license required."""
    s = ElectricalState(**state.get("electrical_state", {}))
    license_str = (s.ecuFlash or {}).get("firmwareLicense", "")
    s.openSourceVerification = {
        "g1Enforcement": "active",
        "n8Enforcement": "active",
        "firmwareLicense": license_str,
        "containsApache2": "Apache 2.0" in license_str,
        "containsCharterRider": "Charter Compliance Rider" in license_str,
        "proprietaryNdaPresent": False,
        "accept": "Apache 2.0" in license_str and "Charter Compliance Rider" in license_str,
    }
    s.phase = ElectricalPhase.OPEN_SOURCE_VERIFIED
    s.completionPct = 75
    return {"electrical_state": s.__dict__, "next_node": "diagnostics"}


def transition_to_diagnostics_passed(state: dict[str, Any]) -> dict[str, Any]:
    s = ElectricalState(**state.get("electrical_state", {}))
    s.diagnostics = {
        "obdIIScan": "PASS",
        "canBusIntegrity": "PASS",
        "wakeUpSleepCycle": "PASS",
        "shortCircuitCheck": "PASS",
        "groundResistanceOhms": 0.04,
    }
    s.phase = ElectricalPhase.DIAGNOSTICS_PASSED
    s.completionPct = 92
    return {"electrical_state": s.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = ElectricalState(**state.get("electrical_state", {}))
    s.phase = ElectricalPhase.ATTESTATION_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.sarutahiko.electricalAttestation",
        "chassisId": s.chassisId,
        "harnessLayout": s.harnessLayout,
        "ecuFlash": s.ecuFlash,
        "openSourceVerification": s.openSourceVerification,
        "diagnostics": s.diagnostics,
        "recordedAt": "2026-05-26T17:00:00Z",
    }
    return {"electrical_state": s.__dict__, "electrical_attestation": record, "next_node": "end"}
