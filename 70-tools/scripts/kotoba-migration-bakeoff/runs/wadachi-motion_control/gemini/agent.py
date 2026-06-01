"""motion_control_kotoba — MotionControlCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine (matching original EXACTLY) ---

class MotionPhase(Enum):
    INIT = "init"
    MOTORS_ENGAGED = "motors_engaged"
    PATH_FOLLOWING = "path_following"
    SPEED_REGULATED = "speed_regulated"
    MOTION_COMPLETE = "motion_complete"

@dataclass
class MotionState:
    phase: MotionPhase
    missionId: str
    completionPct: int
    currentSpeed: float | None = None
    targetSpeed: float | None = None
    distanceTraveled: float | None = None
    motorMetrics: dict[str, Any] | None = None
    gpsTrajectory: list[dict[str, Any]] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None

def transition_to_motors_engaged(state: dict[str, Any]) -> dict[str, Any]:
    ms = MotionState(**state.get("motion_state", {}))

    mock_motors = {
        "left_motor_rpm": 450,
        "right_motor_rpm": 450,
        "steering_angle_deg": 0,
        "torque_nm": [12.5, 12.5],
        "temperature_c": 32,
    }

    ms.phase = MotionPhase.MOTORS_ENGAGED
    ms.motorMetrics = mock_motors
    ms.completionPct = 20

    return {"motion_state": ms.__dict__, "next_node": "follow_path"}

def transition_to_path_following(state: dict[str, Any]) -> dict[str, Any]:
    ms = MotionState(**state.get("motion_state", {}))

    mock_trajectory = [
        {"latitude": 35.6865, "longitude": 139.6900, "timestamp": "2026-05-26T10:16:00Z"},
        {"latitude": 35.6870, "longitude": 139.6902, "timestamp": "2026-05-26T10:16:15Z"},
        {"latitude": 35.6875, "longitude": 139.6905, "timestamp": "2026-05-26T10:16:30Z"},
    ]

    ms.phase = MotionPhase.PATH_FOLLOWING
    ms.gpsTrajectory = mock_trajectory
    ms.distanceTraveled = 87.5
    ms.completionPct = 45

    return {"motion_state": ms.__dict__, "next_node": "regulate_speed"}

def transition_to_speed_regulated(state: dict[str, Any]) -> dict[str, Any]:
    ms = MotionState(**state.get("motion_state", {}))

    mock_speed = {
        "target_speed_ms": 1.2,
        "actual_speed_ms": 1.19,
        "speed_error_pct": 0.8,
        "acceleration_ms2": 0.15,
        "battery_voltage_v": 24.0,
        "battery_current_a": 8.5,
    }

    ms.phase = MotionPhase.SPEED_REGULATED
    ms.targetSpeed = 1.2
    ms.currentSpeed = 1.19
    ms.motorMetrics = {**(ms.motorMetrics or {}), **mock_speed}
    ms.completionPct = 75

    return {"motion_state": ms.__dict__, "next_node": "witness"}

def transition_to_motion_complete(state: dict[str, Any]) -> dict[str, Any]:
    ms = MotionState(**state.get("motion_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:wadachi-unit-1",
            "role": "motion_executor",
            "timestamp": "2026-05-26T10:17:45Z",
            "signature": "mM1nN2oO3pP4qQ5r...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:sora-unit-1",
            "role": "motion_monitor",
            "timestamp": "2026-05-26T10:17:50Z",
            "signature": "sS6tT7uU8vV9wW0x...",
        },
    ]

    ms.phase = MotionPhase.MOTION_COMPLETE
    ms.robotSignatures = mock_sigs
    ms.completionPct = 100

    return {
        "motion_state": ms.__dict__,
        "motion_record": {
            "missionId": ms.missionId,
            "distanceTraveled": ms.distanceTraveled,
            "avgSpeed": ms.currentSpeed,
            "motorMetrics": ms.motorMetrics,
            "gpsTrajectory": ms.gpsTrajectory,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }

# --- Node Functions (from original_cell.py) ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "motion_state": {
            "phase": MotionPhase.INIT.value,
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        }
    }

def _engage_motors(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_motors_engaged(state)

def _follow_path(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_path_following(state)

def _regulate_speed(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_speed_regulated(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_motion_complete(state)

# --- Graph Builder ---

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("engage_motors", _engage_motors)
_g.add_node("follow_path", _follow_path)
_g.add_node("regulate_speed", _regulate_speed)
_g.add_node("witness", _witness_attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "engage_motors")
_g.add_edge("engage_motors", "follow_path")
_g.add_edge("follow_path", "regulate_speed")
_g.add_edge("regulate_speed", "witness")
_g.add_edge("witness", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
