"""BerthAllocationCell — niyaku R0 Pregel cell.

L0 assign an arriving vessel to a berth + STS crane window.

Per ADR-2606082000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606082015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.berthallocationAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    BerthAllocationPhase,
    CellState,
    transition_to_berth_assigned, transition_to_crane_window_reserved, transition_to_attestation_emitted,
)


class BerthAllocationCell:
    """L0 assign an arriving vessel to a berth + STS crane window (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("berth_assigned", self._step_0)
        graph.add_node("crane_window_reserved", self._step_1)
        graph.add_node("attestation_emitted", self._step_2)

        graph.add_edge(START, "berth_assigned")
        graph.add_edge("berth_assigned", "crane_window_reserved")
        graph.add_edge("crane_window_reserved", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_berth_assigned(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_crane_window_reserved(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606082015 post-ratification"
        )


__all__ = ["BerthAllocationCell"]
