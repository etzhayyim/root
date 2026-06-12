"""YardTransferCell — niyaku R0 Pregel cell.

L5 AGV/straddle transfer quay apron -> yard stack tier.

Per ADR-2606082000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606082015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.yardtransferAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    YardTransferPhase,
    CellState,
    transition_to_agv_dispatched, transition_to_box_landed, transition_to_stack_updated, transition_to_attestation_emitted,
)


class YardTransferCell:
    """L5 AGV/straddle transfer quay apron -> yard stack tier (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("agv_dispatched", self._step_0)
        graph.add_node("box_landed", self._step_1)
        graph.add_node("stack_updated", self._step_2)
        graph.add_node("attestation_emitted", self._step_3)

        graph.add_edge(START, "agv_dispatched")
        graph.add_edge("agv_dispatched", "box_landed")
        graph.add_edge("box_landed", "stack_updated")
        graph.add_edge("stack_updated", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_agv_dispatched(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_box_landed(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_stack_updated(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606082015 post-ratification"
        )


__all__ = ["YardTransferCell"]
