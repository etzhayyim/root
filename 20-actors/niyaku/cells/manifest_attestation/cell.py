"""ManifestAttestationCell — niyaku R0 Pregel cell.

terminal per-move kotoba EAVT anchor + open move registry.

Per ADR-2606082000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606082015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.manifestattestationAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ManifestAttestationPhase,
    CellState,
    transition_to_move_recorded, transition_to_datom_anchored, transition_to_attestation_emitted,
)


class ManifestAttestationCell:
    """terminal per-move kotoba EAVT anchor + open move registry (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("move_recorded", self._step_0)
        graph.add_node("datom_anchored", self._step_1)
        graph.add_node("attestation_emitted", self._step_2)

        graph.add_edge(START, "move_recorded")
        graph.add_edge("move_recorded", "datom_anchored")
        graph.add_edge("datom_anchored", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_move_recorded(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_datom_anchored(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606082015 post-ratification"
        )


__all__ = ["ManifestAttestationCell"]
