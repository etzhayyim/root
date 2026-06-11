"""TsutaeDisplayAttachmentCell — tsutae R0 Pregel cell (L3, joseph). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    DisplayPhase,
    transition_to_panel_verified,
    transition_to_laminated,
    transition_to_touch_calibrated,
    transition_to_attestation_emitted,
)


class TsutaeDisplayAttachmentCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("laminate", self._laminate)
        g.add_node("calibrate", self._calibrate)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "laminate")
        g.add_edge("laminate", "calibrate")
        g.add_edge("calibrate", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"display_state": {
            "phase": DisplayPhase.INIT.value,
            "chassisId": state.get("chassisId", "TSUTAE-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_panel_verified(s)
    def _laminate(self, s): return transition_to_laminated(s)
    def _calibrate(self, s): return transition_to_touch_calibrated(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeDisplayAttachmentCell"]
