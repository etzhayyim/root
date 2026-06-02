"""LaunchCommissioningCell — funadaiku R0 Pregel cell.

Float out the hull, run the inclining (stability) test, and complete dock trials.

Per ADR-2606013400. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606013415 (R1 activation). Lexicon: com.etzhayyim.funadaiku.launchCommissioningRecord.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    LaunchCommissioningPhase,
    CellState,
    transition_to_floated_out, transition_to_inclining_test_done, transition_to_dock_trial_done, transition_to_record_emitted,
)


class LaunchCommissioningCell:
    """L5b float-out + inclining test + dock trial (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("floated_out", self._step_0)
        graph.add_node("inclining_test_done", self._step_1)
        graph.add_node("dock_trial_done", self._step_2)
        graph.add_node("record_emitted", self._step_3)

        graph.add_edge(START, "floated_out")
        graph.add_edge("floated_out", "inclining_test_done")
        graph.add_edge("inclining_test_done", "dock_trial_done")
        graph.add_edge("dock_trial_done", "record_emitted")
        graph.add_edge("record_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_floated_out(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_inclining_test_done(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_dock_trial_done(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_record_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "funadaiku R0 scaffold: activate via Council ADR-2606013415 post-ratification"
        )


__all__ = ["LaunchCommissioningCell"]
