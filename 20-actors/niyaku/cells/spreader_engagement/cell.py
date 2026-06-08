"""SpreaderEngagementCell — niyaku R0 Pregel cell.

L2 align + engage the twistlock spreader on the target container.

Per ADR-2606074000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606074015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.spreaderengagementAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SpreaderEngagementPhase,
    CellState,
    transition_to_spreader_aligned, transition_to_twistlocks_engaged, transition_to_load_verified, transition_to_attestation_emitted,
)


class SpreaderEngagementCell:
    """L2 align + engage the twistlock spreader on the target container (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("spreader_aligned", self._step_0)
        graph.add_node("twistlocks_engaged", self._step_1)
        graph.add_node("load_verified", self._step_2)
        graph.add_node("attestation_emitted", self._step_3)

        graph.add_edge(START, "spreader_aligned")
        graph.add_edge("spreader_aligned", "twistlocks_engaged")
        graph.add_edge("twistlocks_engaged", "load_verified")
        graph.add_edge("load_verified", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_spreader_aligned(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_twistlocks_engaged(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_load_verified(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606074015 post-ratification"
        )


__all__ = ["SpreaderEngagementCell"]
