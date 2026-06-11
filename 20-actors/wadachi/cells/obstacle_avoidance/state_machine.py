"""Obstacle avoidance state machine - ADR-2605242000."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ObstaclePhase(Enum):
    INIT = "init"
    LIDAR_SCANNING = "lidar_scanning"
    OBSTACLES_DETECTED = "obstacles_detected"
    COURSE_CORRECTION = "course_correction"
    AVOIDANCE_COMPLETE = "avoidance_complete"


@dataclass
class ObstacleState:
    phase: ObstaclePhase
    missionId: str
    completionPct: int
    lidarScan: dict[str, Any] | None = None
    detectedObjects: list[dict[str, Any]] | None = None
    collisionRisk: list[dict[str, Any]] | None = None
    correctionApplied: bool | None = None
    newTrajectory: dict[str, Any] | None = None
    anomalyFlags: list[str] | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_lidar_scanning(state: dict[str, Any]) -> dict[str, Any]:
    os = ObstacleState(**state.get("obstacle_state", {}))

    mock_lidar = {
        "range_m": 50,
        "angular_resolution_deg": 0.1,
        "scan_points": 3600,
        "min_distance_m": 0.5,
        "max_distance_m": 49.8,
    }

    os.phase = ObstaclePhase.LIDAR_SCANNING
    os.lidarScan = mock_lidar
    os.completionPct = 20

    return {"obstacle_state": os.__dict__, "next_node": "detect_objects"}


def transition_to_obstacles_detected(state: dict[str, Any]) -> dict[str, Any]:
    os = ObstacleState(**state.get("obstacle_state", {}))

    mock_objects = [
        {
            "object_id": "OBS-001",
            "distance_m": 8.5,
            "angle_deg": 15,
            "size_m": 1.2,
            "type": "pedestrian_alert",
            "moving": True,
        },
        {
            "object_id": "OBS-002",
            "distance_m": 12.3,
            "angle_deg": -10,
            "size_m": 0.8,
            "type": "static_debris",
            "moving": False,
        },
        {
            "object_id": "OBS-003",
            "distance_m": 25.0,
            "angle_deg": 0,
            "size_m": 2.5,
            "type": "vehicle",
            "moving": True,
        },
    ]

    mock_risks = [
        {
            "object_id": "OBS-001",
            "collision_time_s": 7.0,
            "risk_level": "medium",
            "required_action": "divert_right",
        },
        {
            "object_id": "OBS-002",
            "collision_time_s": 10.0,
            "risk_level": "low",
            "required_action": "monitor",
        },
    ]

    os.phase = ObstaclePhase.OBSTACLES_DETECTED
    os.detectedObjects = mock_objects
    os.collisionRisk = mock_risks
    os.completionPct = 45

    return {"obstacle_state": os.__dict__, "next_node": "apply_correction"}


def transition_to_course_correction(state: dict[str, Any]) -> dict[str, Any]:
    os = ObstacleState(**state.get("obstacle_state", {}))

    mock_correction = {
        "original_bearing_deg": 45,
        "new_bearing_deg": 52,
        "steering_adjustment_deg": 7,
        "speed_reduction_pct": 15,
        "new_speed_ms": 1.02,
    }

    os.phase = ObstaclePhase.COURSE_CORRECTION
    os.newTrajectory = mock_correction
    os.correctionApplied = True
    os.completionPct = 70

    return {"obstacle_state": os.__dict__, "next_node": "witness"}


def transition_to_avoidance_complete(state: dict[str, Any]) -> dict[str, Any]:
    os = ObstacleState(**state.get("obstacle_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:wadachi-unit-1",
            "role": "obstacle_handler",
            "timestamp": "2026-05-26T10:18:30Z",
            "signature": "yY1zZ2aA3bB4cC5d...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:sora-unit-1",
            "role": "lidar_monitor",
            "timestamp": "2026-05-26T10:18:35Z",
            "signature": "eE6fF7gG8hH9iI0j...",
        },
    ]

    os.phase = ObstaclePhase.AVOIDANCE_COMPLETE
    os.robotSignatures = mock_sigs
    os.completionPct = 100

    return {
        "obstacle_state": os.__dict__,
        "avoidance_record": {
            "missionId": os.missionId,
            "detectedObjects": os.detectedObjects,
            "collisionRisks": os.collisionRisk,
            "correctionApplied": os.correctionApplied,
            "newTrajectory": os.newTrajectory,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
