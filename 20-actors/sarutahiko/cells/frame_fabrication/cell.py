"""FrameFabricationCell — sarutahiko R0 Pregel cell (L1). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    FramePhase, FrameState,
    transition_to_steel_lot_verified, transition_to_rails_positioned,
    transition_to_cross_members_welded, transition_to_straightness_qa_passed,
    transition_to_attestation_emitted,
)


class FrameFabricationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("position", self._position)
        g.add_node("weld", self._weld)
        g.add_node("qa", self._qa)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "position")
        g.add_edge("position", "weld")
        g.add_edge("weld", "qa")
        g.add_edge("qa", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"frame_state": {
            "phase": FramePhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_steel_lot_verified(s)
    def _position(self, s): return transition_to_rails_positioned(s)
    def _weld(self, s): return transition_to_cross_members_welded(s)
    def _qa(self, s): return transition_to_straightness_qa_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["FrameFabricationCell"]
