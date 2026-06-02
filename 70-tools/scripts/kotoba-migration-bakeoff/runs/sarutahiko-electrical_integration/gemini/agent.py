"""ElectricalIntegrationCell — sarutahiko R0 Pregel cell (L5b) compiled to WASM.

Port of original_cell.py onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---

class ElectricalPhase(Enum):
    INIT = "init"
    HARNESS_ROUTED = "harness_routed"
    ECU_FLASHED = "ecu_flashed"
    OPEN_SOURCE_VERIFIED = "open_source_verified"
    DIAGNOSTICS_PASSED = "diagnostics_passed"
    ATTESTATION_EMITTED = "attestation_emitted"

@dataclass
class ElectricalState:
    phase: ElectricalPhase | str
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
    s.phase = ElectricalPhase.HARNESS_ROUTED.value
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
    s.phase = ElectricalPhase.ECU_FLASHED.value
    s.completionPct = 55
    return {"electrical_state": s.__dict__, "next_node": "verify"}

def transition_to_open_source_verified(state: dict[str, Any]) -> dict[str, Any]:
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
    s.phase = ElectricalPhase.OPEN_SOURCE_VERIFIED.value
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
    s.phase = ElectricalPhase.DIAGNOSTICS_PASSED.value
    s.completionPct = 92
    return {"electrical_state": s.__dict__, "next_node": "attestation"}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = ElectricalState(**state.get("electrical_state", {}))
    s.phase = ElectricalPhase.ATTESTATION_EMITTED.value
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

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"electrical_state": {
        "phase": ElectricalPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _harness(s: dict[str, Any]): return transition_to_harness_routed(s)
def _flash(s: dict[str, Any]): return transition_to_ecu_flashed(s)
def _verify(s: dict[str, Any]): return transition_to_open_source_verified(s)
def _diagnostics(s: dict[str, Any]): return transition_to_diagnostics_passed(s)
def _attestation(s: dict[str, Any]): return transition_to_attestation_emitted(s)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("harness", _harness)
_g.add_node("flash", _flash)
_g.add_node("verify", _verify)
_g.add_node("diagnostics", _diagnostics)
_g.add_node("attestation", _attestation)
_g.add_edge(START, "init")
_g.add_edge("init", "harness")
_g.add_edge("harness", "flash")
_g.add_edge("flash", "verify")
_g.add_edge("verify", "diagnostics")
_g.add_edge("diagnostics", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
