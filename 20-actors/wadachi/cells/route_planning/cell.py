"""Route planning cell - ADR-2605242000."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    RouteState,
    RoutePlanningPhase,
    transition_to_destination_validated,
    transition_to_obstacles_mapped,
    transition_to_path_computed,
    transition_to_trajectory_planned,
    transition_to_witness_attestation,
)


class RoutePlanningCell:
    """Route planning Pregel cell for wadachi autonomous mobility."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("validate_destination", self._validate_destination)
        graph.add_node("map_obstacles", self._map_obstacles)
        graph.add_node("compute_path", self._compute_path)
        graph.add_node("plan_trajectory", self._plan_trajectory)
        graph.add_node("witness", self._witness_attestation)

        graph.add_edge(START, "init")
        graph.add_edge("init", "validate_destination")
        graph.add_edge("validate_destination", "map_obstacles")
        graph.add_edge("map_obstacles", "compute_path")
        graph.add_edge("compute_path", "plan_trajectory")
        graph.add_edge("plan_trajectory", "witness")
        graph.add_edge("witness", END)

        return graph.compile()

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "route_state": {
                "phase": RoutePlanningPhase.INIT.value,
                "missionId": state.get("missionId", "MISSION-2026-0001"),
                "completionPct": 0,
            }
        }

    def _validate_destination(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_destination_validated(state)

    def _map_obstacles(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_obstacles_mapped(state)

    def _compute_path(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_path_computed(state)

    def _plan_trajectory(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_trajectory_planned(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_witness_attestation(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell."""
        raise RuntimeError("wadachi R0 scaffold: activate via Council ADR post-ratification")


__all__ = ["RoutePlanningCell"]
