"""FinalMarriageCell — sarutahiko R0 Pregel cell (L4). ≥2 robot witness. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    MarriagePhase, MarriageState,
    transition_to_inputs_verified, transition_to_chassis_lowered,
    transition_to_cab_dropped, transition_to_powertrain_mounted,
    transition_to_harness_connected, transition_to_attestation_emitted,
)


class FinalMarriageCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("lower", self._lower)
        g.add_node("cab", self._cab)
        g.add_node("powertrain", self._powertrain)
        g.add_node("harness", self._harness)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "lower")
        g.add_edge("lower", "cab")
        g.add_edge("cab", "powertrain")
        g.add_edge("powertrain", "harness")
        g.add_edge("harness", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"marriage_state": {
            "phase": MarriagePhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_inputs_verified(s)
    def _lower(self, s): return transition_to_chassis_lowered(s)
    def _cab(self, s): return transition_to_cab_dropped(s)
    def _powertrain(self, s): return transition_to_powertrain_mounted(s)
    def _harness(self, s): return transition_to_harness_connected(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["FinalMarriageCell"]
