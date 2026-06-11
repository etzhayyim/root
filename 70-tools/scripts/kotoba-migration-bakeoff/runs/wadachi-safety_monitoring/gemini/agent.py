from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401
import wit_world.imports.llm  # noqa: F401

# --- Mocks for .state_machine ---

class SafetyPhase:
    class INIT: value = "init"
    class SENSORS_CHECKED: value = "sensors_checked"
    class HAZARDS_ASSESSED: value = "hazards_assessed"
    class PROTOCOL_SET: value = "protocol_set"
    class VERIFIED: value = "verified"

def transition_to_sensors_checked(state: dict[str, Any]) -> dict[str, Any]:
    return {"safety_state": {**state.get("safety_state", {}), "phase": "sensors_checked", "completionPct": 25}}

def transition_to_hazards_assessed(state: dict[str, Any]) -> dict[str, Any]:
    return {"safety_state": {**state.get("safety_state", {}), "phase": "hazards_assessed", "completionPct": 50}}

def transition_to_safety_protocol_set(state: dict[str, Any]) -> dict[str, Any]:
    return {"safety_state": {**state.get("safety_state", {}), "phase": "protocol_set", "completionPct": 75}}

def transition_to_safety_verified(state: dict[str, Any]) -> dict[str, Any]:
    mock_attestation = {
        "witness_id": "did:web:safety.wadachi.ai",
        "signature": "sAfeTy_vErIfIeD_sIg",
        "status": "secure"
    }
    return {"safety_state": {**state.get("safety_state", {}), "phase": "verified", "attestation": mock_attestation, "completionPct": 100}}

# --- Node Functions ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "safety_state": {
            "phase": SafetyPhase.INIT.value,
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        }
    }

def _check_sensors(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_sensors_checked(state)

def _assess_hazards(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_hazards_assessed(state)

def _set_protocol(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_safety_protocol_set(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_safety_verified(state)

# --- Graph Construction ---

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("check_sensors", _check_sensors)
_g.add_node("assess_hazards", _assess_hazards)
_g.add_node("set_protocol", _set_protocol)
_g.add_node("witness", _witness_attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "check_sensors")
_g.add_edge("check_sensors", "assess_hazards")
_g.add_edge("assess_hazards", "set_protocol")
_g.add_edge("set_protocol", "witness")
_g.add_edge("witness", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

# --- Kotoba Entry Point ---

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
