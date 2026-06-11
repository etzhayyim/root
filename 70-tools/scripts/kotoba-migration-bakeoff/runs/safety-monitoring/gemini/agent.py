"""Safety monitoring cell - Kotoba Port."""

from __future__ import annotations
from typing import Any, TypedDict, List
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- MOCKS AND CONSTANTS ---
# Ported from original_cell.py and assumed .state_machine logic

class SafetyPhase:
    INIT = "INIT"
    SENSORS_CHECKED = "SENSORS_CHECKED"
    HAZARDS_ASSESSED = "HAZARDS_ASSESSED"
    SAFETY_PROTOCOL_SET = "SAFETY_PROTOCOL_SET"
    SAFETY_VERIFIED = "SAFETY_VERIFIED"

class SafetyStateDict(TypedDict, total=False):
    missionId: str
    safety_state: dict[str, Any]

def transition_to_sensors_checked(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": SafetyPhase.SENSORS_CHECKED,
            "completionPct": 25,
            "sensors": ["lidar_primary", "imu_v2", "ultrasonic_array"]
        }
    }

def transition_to_hazards_assessed(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": SafetyPhase.HAZARDS_ASSESSED,
            "completionPct": 50,
            "hazards": ["slope_instability", "thermal_gradient"]
        }
    }

def transition_to_safety_protocol_set(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": SafetyPhase.SAFETY_PROTOCOL_SET,
            "completionPct": 75,
            "protocol": "ADR-260524-ALPHA"
        }
    }

def transition_to_safety_verified(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    mock_attestation = {
        "attestor": "did:web:safety.wadachi.io",
        "signature": "sig:0x1234567890abcdef",
        "verified": True
    }
    return {
        "safety_state": {
            **current,
            "phase": SafetyPhase.SAFETY_VERIFIED,
            "completionPct": 100,
            "attestation": mock_attestation
        }
    }

# --- NODE FUNCTIONS ---

def _initialize_state(state: SafetyStateDict) -> SafetyStateDict:
    return {
        "safety_state": {
            "phase": SafetyPhase.INIT,
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        }
    }

def _check_sensors(state: SafetyStateDict) -> SafetyStateDict:
    return transition_to_sensors_checked(state)

def _assess_hazards(state: SafetyStateDict) -> SafetyStateDict:
    return transition_to_hazards_assessed(state)

def _set_protocol(state: SafetyStateDict) -> SafetyStateDict:
    return transition_to_safety_protocol_set(state)

def _witness_attestation(state: SafetyStateDict) -> SafetyStateDict:
    return transition_to_safety_verified(state)

# --- GRAPH BUILDER ---

_g = StateGraph(SafetyStateDict)
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

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
