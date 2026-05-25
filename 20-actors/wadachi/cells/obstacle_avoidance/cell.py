"""Obstacle avoidance cell - ADR-2605242000."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ObstacleState,
    ObstaclePhase,
    transition_to_lidar_scanning,
    transition_to_obstacles_detected,
    transition_to_course_correction,
    transition_to_avoidance_complete,
)


class ObstacleAvoidanceCell:
    """Obstacle avoidance Pregel cell for wadachi autonomous mobility."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("scan_lidar", self._scan_lidar)
        graph.add_node("detect_objects", self._detect_objects)
        graph.add_node("apply_correction", self._apply_correction)
        graph.add_node("witness", self._witness_attestation)

        graph.add_edge(START, "init")
        graph.add_edge("init", "scan_lidar")
        graph.add_edge("scan_lidar", "detect_objects")
        graph.add_edge("detect_objects", "apply_correction")
        graph.add_edge("apply_correction", "witness")
        graph.add_edge("witness", END)

        return graph.compile()

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "obstacle_state": {
                "phase": ObstaclePhase.INIT.value,
                "missionId": state.get("missionId", "MISSION-2026-0001"),
                "completionPct": 0,
            }
        }

    def _scan_lidar(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_lidar_scanning(state)

    def _detect_objects(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_obstacles_detected(state)

    def _apply_correction(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_course_correction(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_avoidance_complete(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell."""
        raise RuntimeError("wadachi R0 scaffold: activate via Council ADR post-ratification")


__all__ = ["ObstacleAvoidanceCell"]
