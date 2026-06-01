"""WeldInspectionCell — watatsumi R0 Pregel cell (L3).

100% RT/UT/PT NDT. Sango AUV swarm in-process witness. R0 scaffold —
.solve() raises RuntimeError until R1.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    WeldInspectionPhase,
    WeldInspectionState,
    transition_to_rt_complete,
    transition_to_ut_complete,
    transition_to_pt_complete,
    transition_to_sango_witness,
    transition_to_record_emitted,
)


class WeldInspectionCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("rt", self._rt)
        g.add_node("ut", self._ut)
        g.add_node("pt", self._pt)
        g.add_node("sango", self._sango)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "rt")
        g.add_edge("rt", "ut")
        g.add_edge("ut", "pt")
        g.add_edge("pt", "sango")
        g.add_edge("sango", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "weld_inspection_state": {
                "phase": WeldInspectionPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "sectionIndex": state.get("sectionIndex", 0),
                "completionPct": 0,
            }
        }

    def _rt(self, state): return transition_to_rt_complete(state)
    def _ut(self, state): return transition_to_ut_complete(state)
    def _pt(self, state): return transition_to_pt_complete(state)
    def _sango(self, state): return transition_to_sango_witness(state)
    def _record(self, state): return transition_to_record_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["WeldInspectionCell"]
