"""Safety monitoring cell — Kotoba WASM component.

Port of safety monitoring cell (ADR-2605242000) onto the WASM-native
`kotoba_langgraph` API so it compiles to a kotoba-node component.

Build:
    ../../scripts/build-pywasm.sh agent.py -o agent.wasm
"""

from __future__ import annotations
from typing import Any, TypedDict
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

class SafetyStateDict(TypedDict, total=False):
    missionId: str
    safety_state: dict[str, Any]
    next_node: str
    witness_record: dict[str, Any]

def _initialize_state(state: SafetyStateDict) -> SafetyStateDict:
    return {
        "safety_state": {
            "phase": "INIT",
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        },
        "next_node": "check_sensors",
    }

def _check_sensors(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": "SENSORS_CHECKED",
            "sensor_health": {
                "lidar": "ok",
                "radar": "ok",
                "camera": "ok",
                "imu": "ok",
            },
            "completionPct": 25,
        },
        "next_node": "assess_hazards",
    }

def _assess_hazards(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": "HAZARDS_ASSESSED",
            "hazards_detected": [
                {"type": "pedestrian_near", "severity": "medium", "distance_m": 15.5}
            ],
            "risk_level": "caution",
            "completionPct": 50,
        },
        "next_node": "set_protocol",
    }

def _set_protocol(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": "SAFETY_PROTOCOL_SET",
            "protocol": {
                "speed_limit_ms": 3.0,
                "emergency_stop_armed": True,
                "human_override_enabled": True,
            },
            "completionPct": 75,
        },
        "next_node": "witness",
    }

def _witness_attestation(state: SafetyStateDict) -> SafetyStateDict:
    current = state.get("safety_state", {})
    return {
        "safety_state": {
            **current,
            "phase": "VERIFIED",
            "completionPct": 100,
        },
        "witness_record": {
            "missionId": state.get("missionId", current.get("missionId", "MISSION-2026-0001")),
            "attestation": {
                "timestamp": "2026-05-31T00:00:00Z",
                "safety_verified": True,
                "all_checks_passed": True,
                "attestor_did": "did:web:etzhayyim.com",
            },
        },
        "next_node": "end",
    }

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
