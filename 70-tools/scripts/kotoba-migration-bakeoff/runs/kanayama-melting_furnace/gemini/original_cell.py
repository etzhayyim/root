"""MeltingFurnaceCell — kanayama R0 Pregel cell (L3). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    MeltingPhase, MeltingState,
    transition_to_charged, transition_to_melt_held,
    transition_to_degas_complete, transition_to_alloy_adjusted,
    transition_to_pour_witnessed, transition_to_record_emitted,
)


class MeltingFurnaceCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("charge", self._charge)
        g.add_node("hold", self._hold)
        g.add_node("degas", self._degas)
        g.add_node("alloy", self._alloy)
        g.add_node("pour", self._pour)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "charge")
        g.add_edge("charge", "hold")
        g.add_edge("hold", "degas")
        g.add_edge("degas", "alloy")
        g.add_edge("alloy", "pour")
        g.add_edge("pour", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"melting_state": {
            "phase": MeltingPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _charge(self, s): return transition_to_charged(s)
    def _hold(self, s): return transition_to_melt_held(s)
    def _degas(self, s): return transition_to_degas_complete(s)
    def _alloy(self, s): return transition_to_alloy_adjusted(s)
    def _pour(self, s): return transition_to_pour_witnessed(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["MeltingFurnaceCell"]
