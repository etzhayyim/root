"""LashingTwistlockCell — niyaku R0 Pregel cell.

L6 secure/lash the loaded box for sea passage.

Per ADR-2606074000. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606074015 (R1 activation). Lexicon:
com.etzhayyim.niyaku.lashingtwistlockAttestation.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    LashingTwistlockPhase,
    CellState,
    transition_to_lashing_applied, transition_to_tension_verified, transition_to_attestation_emitted,
)


class LashingTwistlockCell:
    """L6 secure/lash the loaded box for sea passage (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("lashing_applied", self._step_0)
        graph.add_node("tension_verified", self._step_1)
        graph.add_node("attestation_emitted", self._step_2)

        graph.add_edge(START, "lashing_applied")
        graph.add_edge("lashing_applied", "tension_verified")
        graph.add_edge("tension_verified", "attestation_emitted")
        graph.add_edge("attestation_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_lashing_applied(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_tension_verified(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "niyaku R0 scaffold: activate via Council ADR-2606074015 post-ratification"
        )


__all__ = ["LashingTwistlockCell"]
