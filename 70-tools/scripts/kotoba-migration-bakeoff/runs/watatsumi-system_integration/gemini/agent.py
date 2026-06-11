"""SystemIntegrationCell ported to Kotoba WASM.
"""

from __future__ import annotations
import wit_world
from typing import Any
from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock state_machine imports
class SystemIntegrationPhase:
    class INIT: value = "init"
    class PROPULSION: value = "propulsion_installed"
    class LIFE_SUPPORT: value = "life_support_installed"
    class SENSORS: value = "sensors_installed"
    class COMMS: value = "comms_installed"
    class CHARTER_SCAN: value = "charter_scan_passed"
    class ATTESTATION: value = "attestation_emitted"

def transition_to_propulsion_installed(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.PROPULSION.value, "completionPct": 15}}

def transition_to_life_support_installed(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.LIFE_SUPPORT.value, "completionPct": 30}}

def transition_to_sensors_installed(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.SENSORS.value, "completionPct": 45}}

def transition_to_comms_installed(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.COMMS.value, "completionPct": 60}}

def transition_to_charter_scan_passed(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.CHARTER_SCAN.value, "completionPct": 80}}

def transition_to_attestation_emitted(s: dict[str, Any]) -> dict[str, Any]:
    return {"system_integration_state": {**s.get("system_integration_state", {}), "phase": SystemIntegrationPhase.ATTESTATION.value, "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "system_integration_state": {
            "phase": SystemIntegrationPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _propulsion(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_propulsion_installed(s)

def _life_support(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_life_support_installed(s)

def _sensors(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_sensors_installed(s)

def _comms(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_comms_installed(s)

def _charter_scan(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_charter_scan_passed(s)

def _attestation(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("propulsion", _propulsion)
_g.add_node("life_support", _life_support)
_g.add_node("sensors", _sensors)
_g.add_node("comms", _comms)
_g.add_node("charter_scan", _charter_scan)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "propulsion")
_g.add_edge("propulsion", "life_support")
_g.add_edge("life_support", "sensors")
_g.add_edge("sensors", "comms")
_g.add_edge("comms", "charter_scan")
_g.add_edge("charter_scan", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
