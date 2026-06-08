"""StowagePlanningCell — niyaku R0 Pregel cell.

L1 compute bay/row/tier stow plan (weight/rotation/reefer/hazmat) + work sequence.

Per ADR-2606082000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606082015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.stowageplanningAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    StowagePlanningPhase,
    CellState,
    transition_to_plan_computed, transition_to_sequence_ordered, transition_to_no_rehandle_verified, transition_to_attestation_emitted,
)


class StowagePlanningCell:
    """L1 compute bay/row/tier stow plan (weight/rotation/reefer/hazmat) + work sequence (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("plan_computed", self._step_0)
        graph.add_node("sequence_ordered", self._step_1)
        graph.add_node("no_rehandle_verified", self._step_2)
        graph.add_node("attestation_emitted", self._step_3)

        graph.add_edge(START, "plan_computed")
        graph.add_edge("plan_computed", "sequence_ordered")
        graph.add_edge("sequence_ordered", "no_rehandle_verified")
        graph.add_edge("no_rehandle_verified", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_plan_computed(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_sequence_ordered(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_no_rehandle_verified(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606082015 post-ratification"
        )


__all__ = ["StowagePlanningCell"]
