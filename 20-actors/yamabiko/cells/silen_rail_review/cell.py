"""SilenRailReviewCell — yamabiko R0 Pregel cell (governance). Council 5-of-7 Safe. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ReviewPhase, ReviewState,
    transition_to_scope_declared, transition_to_signatures_collected,
    transition_to_decision_recorded, transition_to_record_emitted,
)


class SilenRailReviewCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("scope", self._scope)
        g.add_node("signatures", self._signatures)
        g.add_node("decision", self._decision)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "scope")
        g.add_edge("scope", "signatures")
        g.add_edge("signatures", "decision")
        g.add_edge("decision", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"review_state": {
            "phase": ReviewPhase.INIT.value,
            "reviewSubjectId": state.get("reviewSubjectId", "YAMABIKO-R0-SCAFFOLD-BASELINE"),
            "completionPct": 0,
        }}

    def _scope(self, s): return transition_to_scope_declared(s)
    def _signatures(self, s): return transition_to_signatures_collected(s)
    def _decision(self, s): return transition_to_decision_recorded(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["SilenRailReviewCell"]
