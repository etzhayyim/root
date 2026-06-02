"""WeldNdtInspectionCell — funadaiku R0 Pregel cell.

100% NDT (RT/UT/PT) of hull seams with >=2 robot witness quorum.

Per ADR-2606013400. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606013415 (R1 activation). Lexicon: com.etzhayyim.funadaiku.weldInspectionRecord.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    WeldNdtInspectionPhase,
    CellState,
    transition_to_seams_registered, transition_to_rt_ut_pt_run, transition_to_defects_dispositioned, transition_to_record_emitted,
)


class WeldNdtInspectionCell:
    """L3 100% RT/UT/PT hull-seam NDT (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("seams_registered", self._step_0)
        graph.add_node("rt_ut_pt_run", self._step_1)
        graph.add_node("defects_dispositioned", self._step_2)
        graph.add_node("record_emitted", self._step_3)

        graph.add_edge(START, "seams_registered")
        graph.add_edge("seams_registered", "rt_ut_pt_run")
        graph.add_edge("rt_ut_pt_run", "defects_dispositioned")
        graph.add_edge("defects_dispositioned", "record_emitted")
        graph.add_edge("record_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_seams_registered(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_rt_ut_pt_run(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_defects_dispositioned(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_record_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "funadaiku R0 scaffold: activate via Council ADR-2606013415 post-ratification"
        )


__all__ = ["WeldNdtInspectionCell"]
