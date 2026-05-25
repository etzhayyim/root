"""CarbodyFabricationCell — yamabiko R0 Pregel cell (L1). FSW + G4 witness. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    CarbodyPhase, CarbodyState,
    transition_to_extrusion_verified, transition_to_fsw_seams_complete,
    transition_to_spot_welds_complete, transition_to_dimensional_qa_passed,
    transition_to_attestation_emitted,
)


class CarbodyFabricationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("extrusion", self._extrusion)
        g.add_node("fsw", self._fsw)
        g.add_node("spot", self._spot)
        g.add_node("qa", self._qa)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "extrusion")
        g.add_edge("extrusion", "fsw")
        g.add_edge("fsw", "spot")
        g.add_edge("spot", "qa")
        g.add_edge("qa", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"carbody_state": {
            "phase": CarbodyPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "carIndex": state.get("carIndex", 0),
            "completionPct": 0,
        }}

    def _extrusion(self, s): return transition_to_extrusion_verified(s)
    def _fsw(self, s): return transition_to_fsw_seams_complete(s)
    def _spot(self, s): return transition_to_spot_welds_complete(s)
    def _qa(self, s): return transition_to_dimensional_qa_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["CarbodyFabricationCell"]
