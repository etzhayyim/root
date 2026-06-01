"""Chip testing cell - ADR-2605242500."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ChiptestState,
    ChiptestPhase,
    transition_to_contact_probe_engaged,
    transition_to_parametric_test_complete,
    transition_to_functional_test_complete,
    transition_to_chip_graded,
)


class ChiptestCell:
    """Chip testing Pregel cell for silicon manufacturing."""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("engage_probe", self._engage_probe)
        graph.add_node("parametric_test", self._parametric_test)
        graph.add_node("functional_test", self._functional_test)
        graph.add_node("grade_chip", self._grade_chip)

        graph.add_edge(START, "init")
        graph.add_edge("init", "engage_probe")
        graph.add_edge("engage_probe", "parametric_test")
        graph.add_edge("parametric_test", "functional_test")
        graph.add_edge("functional_test", "grade_chip")
        graph.add_edge("grade_chip", END)

        return graph.compile()

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "chiptest_state": {
                "phase": ChiptestPhase.INIT.value,
                "dieId": state.get("dieId", "DIE-7NM-2026-0001"),
                "completionPct": 0,
            }
        }

    def _engage_probe(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_contact_probe_engaged(state)

    def _parametric_test(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_parametric_test_complete(state)

    def _functional_test(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_functional_test_complete(state)

    def _grade_chip(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_chip_graded(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell."""
        raise RuntimeError("silicon R0 scaffold: activate via Council ADR post-ratification")


__all__ = ["ChiptestCell"]
