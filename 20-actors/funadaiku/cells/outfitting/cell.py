"""OutfittingCell — funadaiku R0 Pregel cell.

Fit cargo handling, hatch covers, low-VOC coatings, accommodation, and the autonomy sensor suite.

Per ADR-2606013400. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606013415 (R1 activation). Lexicon: com.etzhayyim.funadaiku.outfittingAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    OutfittingPhase,
    CellState,
    transition_to_cargo_systems_fitted, transition_to_coatings_applied, transition_to_accommodation_fitted, transition_to_sensor_suite_installed, transition_to_attestation_emitted,
)


class OutfittingCell:
    """L5a cargo systems + coatings + accommodation + autonomy sensors (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("cargo_systems_fitted", self._step_0)
        graph.add_node("coatings_applied", self._step_1)
        graph.add_node("accommodation_fitted", self._step_2)
        graph.add_node("sensor_suite_installed", self._step_3)
        graph.add_node("attestation_emitted", self._step_4)

        graph.add_edge(START, "cargo_systems_fitted")
        graph.add_edge("cargo_systems_fitted", "coatings_applied")
        graph.add_edge("coatings_applied", "accommodation_fitted")
        graph.add_edge("accommodation_fitted", "sensor_suite_installed")
        graph.add_edge("sensor_suite_installed", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_cargo_systems_fitted(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_coatings_applied(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_accommodation_fitted(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_sensor_suite_installed(state)
    def _step_4(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "funadaiku R0 scaffold: activate via Council ADR-2606013415 post-ratification"
        )


__all__ = ["OutfittingCell"]
