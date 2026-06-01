"""EmissionsAcousticAuditCell — yamabiko R0 Pregel cell (cross). G8. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    AcousticPhase, AcousticState,
    transition_to_wayside_noise_measured, transition_to_vibration_measured,
    transition_to_emc_verified, transition_to_record_emitted,
)


class EmissionsAcousticAuditCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("noise", self._noise)
        g.add_node("vibration", self._vibration)
        g.add_node("emc", self._emc)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "noise")
        g.add_edge("noise", "vibration")
        g.add_edge("vibration", "emc")
        g.add_edge("emc", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"acoustic_state": {
            "phase": AcousticPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "completionPct": 0,
        }}

    def _noise(self, s): return transition_to_wayside_noise_measured(s)
    def _vibration(self, s): return transition_to_vibration_measured(s)
    def _emc(self, s): return transition_to_emc_verified(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["EmissionsAcousticAuditCell"]
