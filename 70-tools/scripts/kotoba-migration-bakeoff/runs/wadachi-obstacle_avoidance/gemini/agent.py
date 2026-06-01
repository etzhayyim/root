"""Obstacle avoidance cell - Kotoba WASM port."""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

from enum import Enum

# Mock constants and transitions from .state_machine for standalone compilation
class ObstaclePhase(Enum):
    INIT = "init"

def transition_to_lidar_scanning(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "obstacle_state": {
            **state.get("obstacle_state", {}),
            "phase": "scanning",
            "completionPct": 25,
        }
    }

def transition_to_obstacles_detected(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "obstacle_state": {
            **state.get("obstacle_state", {}),
            "phase": "detected",
            "completionPct": 50,
        }
    }

def transition_to_course_correction(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "obstacle_state": {
            **state.get("obstacle_state", {}),
            "phase": "correcting",
            "completionPct": 75,
        }
    }

def transition_to_avoidance_complete(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "obstacle_state": {
            **state.get("obstacle_state", {}),
            "phase": "complete",
            "completionPct": 100,
        },
        "avoidance_record": {
            "missionId": state.get("obstacle_state", {}).get("missionId"),
            "status": "success",
            "clearance": True
        }
    }

# Node functions
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "obstacle_state": {
            "phase": ObstaclePhase.INIT.value,
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        }
    }

def _scan_lidar(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_lidar_scanning(state)

def _detect_objects(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_obstacles_detected(state)

def _apply_correction(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_course_correction(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_avoidance_complete(state)

# Graph builder
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("scan_lidar", _scan_lidar)
_g.add_node("detect_objects", _detect_objects)
_g.add_node("apply_correction", _apply_correction)
_g.add_node("witness", _witness_attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "scan_lidar")
_g.add_edge("scan_lidar", "detect_objects")
_g.add_edge("detect_objects", "apply_correction")
_g.add_edge("apply_correction", "witness")
_g.add_edge("witness", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
