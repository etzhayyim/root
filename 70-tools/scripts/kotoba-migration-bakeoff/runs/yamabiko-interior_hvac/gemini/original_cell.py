"""InteriorHvacCell — yamabiko R0 Pregel cell (L3). G5 trilingual + N6 anti-advertising + N8 anti-surveillance. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    InteriorPhase, InteriorState,
    transition_to_floor_installed, transition_to_seating_installed,
    transition_to_accessibility_verified, transition_to_hvac_installed,
    transition_to_pis_configured, transition_to_attestation_emitted,
)


class InteriorHvacCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("floor", self._floor)
        g.add_node("seating", self._seating)
        g.add_node("accessibility", self._accessibility)
        g.add_node("hvac", self._hvac)
        g.add_node("pis", self._pis)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "floor")
        g.add_edge("floor", "seating")
        g.add_edge("seating", "accessibility")
        g.add_edge("accessibility", "hvac")
        g.add_edge("hvac", "pis")
        g.add_edge("pis", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"interior_state": {
            "phase": InteriorPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "carIndex": state.get("carIndex", 0),
            "completionPct": 0,
        }}

    def _floor(self, s): return transition_to_floor_installed(s)
    def _seating(self, s): return transition_to_seating_installed(s)
    def _accessibility(self, s): return transition_to_accessibility_verified(s)
    def _hvac(self, s): return transition_to_hvac_installed(s)
    def _pis(self, s): return transition_to_pis_configured(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["InteriorHvacCell"]
