"""HotRollingCell — kanayama R0 Pregel cell (L5a). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    HotRollingPhase, HotRollingState,
    transition_to_slab_reheated, transition_to_rough_roll_complete,
    transition_to_finish_roll_complete, transition_to_coiled,
    transition_to_record_emitted,
)


class HotRollingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("reheat", self._reheat)
        g.add_node("rough", self._rough)
        g.add_node("finish", self._finish)
        g.add_node("coil", self._coil)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "reheat")
        g.add_edge("reheat", "rough")
        g.add_edge("rough", "finish")
        g.add_edge("finish", "coil")
        g.add_edge("coil", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"hot_rolling_state": {
            "phase": HotRollingPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _reheat(self, s): return transition_to_slab_reheated(s)
    def _rough(self, s): return transition_to_rough_roll_complete(s)
    def _finish(self, s): return transition_to_finish_roll_complete(s)
    def _coil(self, s): return transition_to_coiled(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["HotRollingCell"]
