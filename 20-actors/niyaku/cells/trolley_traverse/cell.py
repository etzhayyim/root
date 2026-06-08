"""TrolleyTraverseCell — niyaku R0 Pregel cell.

L4 anti-sway trolley traverse ship<->shore (crane_dynamics / Isaac-Sim verified).

Per ADR-2606074000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606074015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.trolleytraverseAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    TrolleyTraversePhase,
    CellState,
    transition_to_traverse_commanded, transition_to_anti_sway_settled, transition_to_over_target_slot, transition_to_attestation_emitted,
)


class TrolleyTraverseCell:
    """L4 anti-sway trolley traverse ship<->shore (crane_dynamics / Isaac-Sim verified) (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("traverse_commanded", self._step_0)
        graph.add_node("anti_sway_settled", self._step_1)
        graph.add_node("over_target_slot", self._step_2)
        graph.add_node("attestation_emitted", self._step_3)

        graph.add_edge(START, "traverse_commanded")
        graph.add_edge("traverse_commanded", "anti_sway_settled")
        graph.add_edge("anti_sway_settled", "over_target_slot")
        graph.add_edge("over_target_slot", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_traverse_commanded(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_anti_sway_settled(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_over_target_slot(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606074015 post-ratification"
        )


__all__ = ["TrolleyTraverseCell"]
