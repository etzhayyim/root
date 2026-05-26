"""IntakeQaCell — kanayama R0 Pregel cell (L1).

UBC bale weighing + QA. R0 scaffold — .solve() raises RuntimeError until R1.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    IntakePhase,
    IntakeState,
    transition_to_bale_weighed,
    transition_to_contamination_scanned,
    transition_to_accept_or_reject_decided,
    transition_to_record_emitted,
)


class IntakeQaCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("weigh", self._weigh)
        g.add_node("scan", self._scan)
        g.add_node("decide", self._decide)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "weigh")
        g.add_edge("weigh", "scan")
        g.add_edge("scan", "decide")
        g.add_edge("decide", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"intake_state": {
            "phase": IntakePhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _weigh(self, s): return transition_to_bale_weighed(s)
    def _scan(self, s): return transition_to_contamination_scanned(s)
    def _decide(self, s): return transition_to_accept_or_reject_decided(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["IntakeQaCell"]
