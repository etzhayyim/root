"""Route planning state machine - ADR-2605242000."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RoutePlanningPhase(Enum):
    INIT = "init"
    DESTINATION_VALIDATED = "destination_validated"
    OBSTACLES_MAPPED = "obstacles_mapped"
    PATH_COMPUTED = "path_computed"
    TRAJECTORY_PLANNED = "trajectory_planned"


@dataclass
class RouteState:
    phase: RoutePlanningPhase
    missionId: str
    completionPct: int
    origin: dict[str, Any] | None = None
    destination: dict[str, Any] | None = None
    obstacles: list[dict[str, Any]] | None = None
    pathWaypoints: list[dict[str, Any]] | None = None
    trajectoryPlan: dict[str, Any] | None = None
    estimatedDuration: float | None = None
    safetyMargin: float | None = None
    robotSignatures: list[dict[str, Any]] | None = None


def transition_to_destination_validated(state: dict[str, Any]) -> dict[str, Any]:
    rs = RouteState(**state.get("route_state", {}))

    mock_dest = {
        "latitude": 35.6895,
        "longitude": 139.6917,
        "altitude": 0,
        "location_type": "construction_site",
        "access_restricted": False,
    }

    rs.phase = RoutePlanningPhase.DESTINATION_VALIDATED
    rs.destination = mock_dest
    rs.completionPct = 20

    return {"route_state": rs.__dict__, "next_node": "map_obstacles"}


def transition_to_obstacles_mapped(state: dict[str, Any]) -> dict[str, Any]:
    rs = RouteState(**state.get("route_state", {}))

    mock_obstacles = [
        {
            "type": "building",
            "latitude": 35.6890,
            "longitude": 139.6910,
            "radius_m": 15,
        },
        {
            "type": "construction_zone",
            "latitude": 35.6900,
            "longitude": 139.6920,
            "radius_m": 20,
        },
        {
            "type": "pedestrian_area",
            "latitude": 35.6898,
            "longitude": 139.6915,
            "radius_m": 10,
        },
    ]

    rs.phase = RoutePlanningPhase.OBSTACLES_MAPPED
    rs.obstacles = mock_obstacles
    rs.completionPct = 40

    return {"route_state": rs.__dict__, "next_node": "compute_path"}


def transition_to_path_computed(state: dict[str, Any]) -> dict[str, Any]:
    rs = RouteState(**state.get("route_state", {}))

    mock_waypoints = [
        {"latitude": 35.6865, "longitude": 139.6900, "order": 1},
        {"latitude": 35.6875, "longitude": 139.6905, "order": 2},
        {"latitude": 35.6885, "longitude": 139.6913, "order": 3},
        {"latitude": 35.6895, "longitude": 139.6917, "order": 4},
    ]

    rs.phase = RoutePlanningPhase.PATH_COMPUTED
    rs.pathWaypoints = mock_waypoints
    rs.completionPct = 60

    return {"route_state": rs.__dict__, "next_node": "plan_trajectory"}


def transition_to_trajectory_planned(state: dict[str, Any]) -> dict[str, Any]:
    rs = RouteState(**state.get("route_state", {}))

    # Calculate distance in meters (rough approximation)
    distance_m = 350
    max_speed_ms = 5  # R0 is 5 m/s, R1 will throttle to 1 m/s
    duration_s = distance_m / max_speed_ms

    mock_trajectory = {
        "total_distance_m": distance_m,
        "total_duration_seconds": duration_s,
        "max_speed_ms": max_speed_ms,
        "safety_margin_m": 2.0,
        "waypoint_count": 4,
        "terrain_type": "urban",
        "traffic_class": "low",
    }

    rs.phase = RoutePlanningPhase.TRAJECTORY_PLANNED
    rs.trajectoryPlan = mock_trajectory
    rs.estimatedDuration = duration_s
    rs.safetyMargin = 2.0
    rs.completionPct = 80

    return {"route_state": rs.__dict__, "next_node": "witness"}


def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    rs = RouteState(**state.get("route_state", {}))

    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:sora-unit-1",
            "role": "route_planner",
            "timestamp": "2026-05-26T10:15:30Z",
            "signature": "aA1bB2cC3dD4eE5f...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:wadachi-unit-1",
            "role": "execution_verifier",
            "timestamp": "2026-05-26T10:15:35Z",
            "signature": "gG6hH7iI8jJ9kK0l...",
        },
    ]

    rs.robotSignatures = mock_sigs
    rs.completionPct = 100

    return {
        "route_state": rs.__dict__,
        "trajectory_record": {
            "missionId": rs.missionId,
            "destination": rs.destination,
            "waypoints": rs.pathWaypoints,
            "trajectory": rs.trajectoryPlan,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }
