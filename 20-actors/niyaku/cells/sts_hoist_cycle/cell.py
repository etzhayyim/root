"""StsHoistCycleCell — niyaku R0 Pregel cell.

L3 ship-to-shore hoist: raise the box clear of the cell guides.

Per ADR-2606074000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606074015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.stshoistcycleAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    StsHoistCyclePhase,
    CellState,
    transition_to_hoist_commanded, transition_to_box_lifted, transition_to_clear_of_guides, transition_to_attestation_emitted,
)


class StsHoistCycleCell:
    """L3 ship-to-shore hoist: raise the box clear of the cell guides (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("hoist_commanded", self._step_0)
        graph.add_node("box_lifted", self._step_1)
        graph.add_node("clear_of_guides", self._step_2)
        graph.add_node("attestation_emitted", self._step_3)

        graph.add_edge(START, "hoist_commanded")
        graph.add_edge("hoist_commanded", "box_lifted")
        graph.add_edge("box_lifted", "clear_of_guides")
        graph.add_edge("clear_of_guides", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_hoist_commanded(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_box_lifted(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_clear_of_guides(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606074015 post-ratification"
        )


__all__ = ["StsHoistCycleCell"]
