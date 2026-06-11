"""FinalAssemblyCell — yamabiko R0 Pregel cell (L5a). ≥2 robot witness. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    FinalPhase, FinalState,
    transition_to_inputs_verified, transition_to_bogie_carbody_married,
    transition_to_cab_interior_installed, transition_to_livery_applied,
    transition_to_attestation_emitted,
)


class FinalAssemblyCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("marriage", self._marriage)
        g.add_node("cab", self._cab)
        g.add_node("livery", self._livery)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "marriage")
        g.add_edge("marriage", "cab")
        g.add_edge("cab", "livery")
        g.add_edge("livery", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"final_state": {
            "phase": FinalPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_inputs_verified(s)
    def _marriage(self, s): return transition_to_bogie_carbody_married(s)
    def _cab(self, s): return transition_to_cab_interior_installed(s)
    def _livery(self, s): return transition_to_livery_applied(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["FinalAssemblyCell"]
