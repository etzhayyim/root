"""ColdRollingFinishingCell — kanayama R0 Pregel cell (L5b). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ColdRollingPhase, ColdRollingState,
    transition_to_hot_band_loaded, transition_to_cold_passes_complete,
    transition_to_temper_complete, transition_to_surface_inspection_complete,
    transition_to_coil_qualified, transition_to_record_emitted,
)


class ColdRollingFinishingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("load", self._load)
        g.add_node("cold", self._cold)
        g.add_node("temper", self._temper)
        g.add_node("migaki", self._migaki)
        g.add_node("qualify", self._qualify)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "load")
        g.add_edge("load", "cold")
        g.add_edge("cold", "temper")
        g.add_edge("temper", "migaki")
        g.add_edge("migaki", "qualify")
        g.add_edge("qualify", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"cold_rolling_state": {
            "phase": ColdRollingPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _load(self, s): return transition_to_hot_band_loaded(s)
    def _cold(self, s): return transition_to_cold_passes_complete(s)
    def _temper(self, s): return transition_to_temper_complete(s)
    def _migaki(self, s): return transition_to_surface_inspection_complete(s)
    def _qualify(self, s): return transition_to_coil_qualified(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["ColdRollingFinishingCell"]
