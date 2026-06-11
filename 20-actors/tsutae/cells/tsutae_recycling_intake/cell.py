"""TsutaeRecyclingIntakeCell — tsutae R0 Pregel cell (EOL, dan). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    RecyclingPhase,
    transition_to_dismantled,
    transition_to_materials_sorted,
    transition_to_kanayama_routed,
    transition_to_certificate_emitted,
)


class TsutaeRecyclingIntakeCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("dismantle", self._dismantle)
        g.add_node("sort", self._sort)
        g.add_node("route", self._route)
        g.add_node("certificate", self._certificate)
        g.add_edge(START, "init")
        g.add_edge("init", "dismantle")
        g.add_edge("dismantle", "sort")
        g.add_edge("sort", "route")
        g.add_edge("route", "certificate")
        g.add_edge("certificate", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"recycling_state": {
            "phase": RecyclingPhase.INIT.value,
            "serial": state.get("serial", "TSUTAE-SN-0001"),
            "completionPct": 0,
        }}

    def _dismantle(self, s): return transition_to_dismantled(s)
    def _sort(self, s): return transition_to_materials_sorted(s)
    def _route(self, s): return transition_to_kanayama_routed(s)
    def _certificate(self, s): return transition_to_certificate_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeRecyclingIntakeCell"]
