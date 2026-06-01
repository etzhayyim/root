"""Motion control cell - ADR-2605242000."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    MotionState,
    MotionPhase,
    transition_to_motors_engaged,
    transition_to_path_following,
    transition_to_speed_regulated,
    transition_to_motion_complete,
)


class MotionControlCell:
    """Motion control Pregel cell for wadachi autonomous mobility."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("engage_motors", self._engage_motors)
        graph.add_node("follow_path", self._follow_path)
        graph.add_node("regulate_speed", self._regulate_speed)
        graph.add_node("witness", self._witness_attestation)

        graph.add_edge(START, "init")
        graph.add_edge("init", "engage_motors")
        graph.add_edge("engage_motors", "follow_path")
        graph.add_edge("follow_path", "regulate_speed")
        graph.add_edge("regulate_speed", "witness")
        graph.add_edge("witness", END)

        return graph.compile()

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "motion_state": {
                "phase": MotionPhase.INIT.value,
                "missionId": state.get("missionId", "MISSION-2026-0001"),
                "completionPct": 0,
            }
        }

    def _engage_motors(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_motors_engaged(state)

    def _follow_path(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_path_following(state)

    def _regulate_speed(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_speed_regulated(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_motion_complete(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell."""
        raise RuntimeError("wadachi R0 scaffold: activate via Council ADR post-ratification")


__all__ = ["MotionControlCell"]
