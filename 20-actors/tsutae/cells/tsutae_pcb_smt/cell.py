"""TsutaePcbSmtCell — tsutae R0 Pregel cell (L1, naphtali). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    PcbPhase,
    transition_to_components_sourced,
    transition_to_soc_guard_checked,
    transition_to_smt_placed,
    transition_to_aoi_passed,
    transition_to_attestation_emitted,
)


class TsutaePcbSmtCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("source", self._source)
        g.add_node("soc_guard", self._soc_guard)
        g.add_node("place", self._place)
        g.add_node("aoi", self._aoi)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "source")
        g.add_edge("source", "soc_guard")
        g.add_edge("soc_guard", "place")
        g.add_edge("place", "aoi")
        g.add_edge("aoi", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"pcb_state": {
            "phase": PcbPhase.INIT.value,
            "boardId": state.get("boardId", "TSUTAE-PCB-0001"),
            "completionPct": 0,
        }}

    def _source(self, s): return transition_to_components_sourced(s)
    def _soc_guard(self, s): return transition_to_soc_guard_checked(s)
    def _place(self, s): return transition_to_smt_placed(s)
    def _aoi(self, s): return transition_to_aoi_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaePcbSmtCell"]
