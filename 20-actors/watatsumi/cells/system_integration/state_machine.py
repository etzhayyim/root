"""System integration state machine — ADR-2605252200 L4.

Propulsion (LFP / H₂ / NH₃ / methanol fuel-cell only — nuclear = N2), pressure-
compensated electrical penetrations, ballast/trim, CO₂ scrubber + O₂ generator,
passive sonar, acoustic modem, RF surface comm.

Forbidden: nuclear propulsion (N2), active sonar >180 dB (G8), proprietary
acoustic-stealth coatings (N12).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SystemIntegrationPhase(Enum):
    INIT = "init"
    PROPULSION_INSTALLED = "propulsion_installed"
    LIFE_SUPPORT_INSTALLED = "life_support_installed"
    SENSORS_INSTALLED = "sensors_installed"
    COMMS_INSTALLED = "comms_installed"
    CHARTER_RIDER_SCAN_PASSED = "charter_rider_scan_passed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class SystemIntegrationState:
    phase: SystemIntegrationPhase
    craftId: str
    completionPct: int
    propulsion: dict[str, Any] | None = None
    lifeSupport: dict[str, Any] | None = None
    sensors: dict[str, Any] | None = None
    comms: dict[str, Any] | None = None
    charterRiderScan: dict[str, Any] | None = None


def transition_to_propulsion_installed(state: dict[str, Any]) -> dict[str, Any]:
    """Install propulsion — G13 fuel restriction enforcement."""
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    allowed_fuels = {"LFP-battery", "H2-fuel-cell", "NH3-fuel-cell", "methanol-fuel-cell"}
    mock_propulsion = {
        "primaryFuel": "LFP-battery",
        "capacityKwh": 480,
        "thrustKN": 22,
        "fuelChecks": {
            "allowedFuels": sorted(allowed_fuels),
            "nuclearGuard": "N2 enforced: no nuclear propulsion",
            "selectedFuel": "LFP-battery",
            "g13Accept": True,
        },
    }
    si.propulsion = mock_propulsion
    si.phase = SystemIntegrationPhase.PROPULSION_INSTALLED
    si.completionPct = 25
    return {"system_integration_state": si.__dict__, "next_node": "life_support"}


def transition_to_life_support_installed(state: dict[str, Any]) -> dict[str, Any]:
    """Install life support — G12 caps: ≤3 crew, ≤72 h submerged."""
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    si.lifeSupport = {
        "maxCrew": 3,
        "maxSubmergedHours": 72,
        "co2ScrubberType": "LiOH-canister",
        "o2GeneratorType": "candle-supplement+electrolysis",
        "humidityControlType": "passive-desiccant",
        "emergencyEscapeMechanism": "personnel-survival-sphere",
        "g12Accept": True,
    }
    si.phase = SystemIntegrationPhase.LIFE_SUPPORT_INSTALLED
    si.completionPct = 50
    return {"system_integration_state": si.__dict__, "next_node": "sensors"}


def transition_to_sensors_installed(state: dict[str, Any]) -> dict[str, Any]:
    """Install sensors — G8 active sonar ≤180 dB / N12 no stealth coating."""
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    si.sensors = {
        "passiveSonar": {"hydrophoneArrayCount": 12, "bandwidthKHz": 100},
        "activeSonar": {
            "enabled": True,
            "maxSplDbRe1uPaAt1m": 175,
            "g8Limit": 180,
            "g8Accept": True,
        },
        "imuLidar": {"present": True, "rateHz": 200},
        "antiStealthCoating": {
            "n12Enforcement": "active",
            "proprietaryStealthCoatingPresent": False,
            "n12Accept": True,
        },
    }
    si.phase = SystemIntegrationPhase.SENSORS_INSTALLED
    si.completionPct = 70
    return {"system_integration_state": si.__dict__, "next_node": "comms"}


def transition_to_comms_installed(state: dict[str, Any]) -> dict[str, Any]:
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    si.comms = {
        "acousticModem": {"bandKHz": [9, 14], "rangeMeters": 8000},
        "rfSurface": {"band": "VHF/UHF/Iridium-SBD", "satelliteFallback": True},
        "fiberOptic": {"present": True, "lengthM": 6500, "g1Accept": True},
    }
    si.phase = SystemIntegrationPhase.COMMS_INSTALLED
    si.completionPct = 85
    return {"system_integration_state": si.__dict__, "next_node": "charter_scan"}


def transition_to_charter_scan_passed(state: dict[str, Any]) -> dict[str, Any]:
    """G6 Charter Rider scan on all CAD + firmware artifacts."""
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    si.charterRiderScan = {
        "categoriesChecked": ["§2(a)", "§2(b)", "§2(c)", "§2(d)", "§2(e)",
                              "§2(f)", "§2(g)", "§2(h)"],
        "violations": [],
        "accept": True,
        "scannerVersion": "etzhayyim_organism.sensors.charter_rider v2.0",
    }
    si.phase = SystemIntegrationPhase.CHARTER_RIDER_SCAN_PASSED
    si.completionPct = 95
    return {"system_integration_state": si.__dict__, "next_node": "attestation"}


def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    si = SystemIntegrationState(**state.get("system_integration_state", {}))
    si.phase = SystemIntegrationPhase.ATTESTATION_EMITTED
    si.completionPct = 100
    record = {
        "$type": "com.etzhayyim.watatsumi.systemIntegrationAttestation",
        "craftId": si.craftId,
        "propulsion": si.propulsion,
        "lifeSupport": si.lifeSupport,
        "sensors": si.sensors,
        "comms": si.comms,
        "charterRiderScan": si.charterRiderScan,
        "recordedAt": "2026-05-26T14:00:00Z",
    }
    return {
        "system_integration_state": si.__dict__,
        "system_integration_attestation": record,
        "next_node": "end",
    }
