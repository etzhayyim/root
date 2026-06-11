"""DynamicTestCell — yamabiko R0 Pregel cell (L5b). G12 KPI enforcement. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    DynamicPhase, DynamicState,
    transition_to_static_test_passed, transition_to_g12_kpi_verified,
    transition_to_dynamic_run_complete, transition_to_record_emitted,
)


class DynamicTestCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("static", self._static)
        g.add_node("g12", self._g12)
        g.add_node("run", self._run)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "static")
        g.add_edge("static", "g12")
        g.add_edge("g12", "run")
        g.add_edge("run", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"dynamic_state": {
            "phase": DynamicPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "completionPct": 0,
        }}

    def _static(self, s): return transition_to_static_test_passed(s)
    def _g12(self, s): return transition_to_g12_kpi_verified(s)
    def _run(self, s): return transition_to_dynamic_run_complete(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["DynamicTestCell"]
