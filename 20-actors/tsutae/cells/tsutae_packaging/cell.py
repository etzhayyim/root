"""TsutaePackagingCell — tsutae R0 Pregel cell (L6, simeon). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    PackagingPhase,
    transition_to_materials_verified,
    transition_to_manual_included,
    transition_to_packed,
    transition_to_record_emitted,
)


class TsutaePackagingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("materials", self._materials)
        g.add_node("manual_guard", self._manual_guard)
        g.add_node("pack", self._pack)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "materials")
        g.add_edge("materials", "manual_guard")
        g.add_edge("manual_guard", "pack")
        g.add_edge("pack", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"packaging_state": {
            "phase": PackagingPhase.INIT.value,
            "deviceId": state.get("deviceId", "TSUTAE-DEV-0001"),
            "completionPct": 0,
        }}

    def _materials(self, s): return transition_to_materials_verified(s)
    def _manual_guard(self, s): return transition_to_manual_included(s)
    def _pack(self, s): return transition_to_packed(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaePackagingCell"]
