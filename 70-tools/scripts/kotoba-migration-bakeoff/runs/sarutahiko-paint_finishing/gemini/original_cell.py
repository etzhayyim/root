"""PaintFinishingCell — sarutahiko R0 Pregel cell (L5a). G8 VOC <100 g/L. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    PaintPhase, PaintState,
    transition_to_pretreatment_done, transition_to_ktl_primer_applied,
    transition_to_base_coat_applied, transition_to_clear_coat_applied,
    transition_to_cured, transition_to_attestation_emitted,
)


class PaintFinishingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("pretreat", self._pretreat)
        g.add_node("ktl", self._ktl)
        g.add_node("base", self._base)
        g.add_node("clear", self._clear)
        g.add_node("cure", self._cure)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "pretreat")
        g.add_edge("pretreat", "ktl")
        g.add_edge("ktl", "base")
        g.add_edge("base", "clear")
        g.add_edge("clear", "cure")
        g.add_edge("cure", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"paint_state": {
            "phase": PaintPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _pretreat(self, s): return transition_to_pretreatment_done(s)
    def _ktl(self, s): return transition_to_ktl_primer_applied(s)
    def _base(self, s): return transition_to_base_coat_applied(s)
    def _clear(self, s): return transition_to_clear_coat_applied(s)
    def _cure(self, s): return transition_to_cured(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["PaintFinishingCell"]
