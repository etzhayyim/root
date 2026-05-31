"""DcCastingCell — kanayama R0 Pregel cell (L4). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    CastingPhase, CastingState,
    transition_to_mold_prepared, transition_to_dc_casting_complete,
    transition_to_homogenization_complete, transition_to_inspection_passed,
    transition_to_record_emitted,
)


class DcCastingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("prepare", self._prepare)
        g.add_node("cast", self._cast)
        g.add_node("homogenize", self._homogenize)
        g.add_node("inspect", self._inspect)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "prepare")
        g.add_edge("prepare", "cast")
        g.add_edge("cast", "homogenize")
        g.add_edge("homogenize", "inspect")
        g.add_edge("inspect", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"casting_state": {
            "phase": CastingPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _prepare(self, s): return transition_to_mold_prepared(s)
    def _cast(self, s): return transition_to_dc_casting_complete(s)
    def _homogenize(self, s): return transition_to_homogenization_complete(s)
    def _inspect(self, s): return transition_to_inspection_passed(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["DcCastingCell"]
