"""EmissionsAuditCell — sarutahiko R0 Pregel cell (cross-cutting). G8 enforcement. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    EmissionsPhase, EmissionsState,
    transition_to_euro7_scanned, transition_to_japan_pnlt_scanned,
    transition_to_bharat_vi_scanned, transition_to_record_emitted,
)


class EmissionsAuditCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("euro7", self._euro7)
        g.add_node("japan", self._japan)
        g.add_node("bharat", self._bharat)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "euro7")
        g.add_edge("euro7", "japan")
        g.add_edge("japan", "bharat")
        g.add_edge("bharat", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"emissions_state": {
            "phase": EmissionsPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _euro7(self, s): return transition_to_euro7_scanned(s)
    def _japan(self, s): return transition_to_japan_pnlt_scanned(s)
    def _bharat(self, s): return transition_to_bharat_vi_scanned(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["EmissionsAuditCell"]
