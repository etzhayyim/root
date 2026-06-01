"""ElectricalIntegrationCell — sarutahiko R0 Pregel cell (L5b). G1 + N8 open-source ECU. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ElectricalPhase, ElectricalState,
    transition_to_harness_routed, transition_to_ecu_flashed,
    transition_to_open_source_verified, transition_to_diagnostics_passed,
    transition_to_attestation_emitted,
)


class ElectricalIntegrationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("harness", self._harness)
        g.add_node("flash", self._flash)
        g.add_node("verify", self._verify)
        g.add_node("diagnostics", self._diagnostics)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "harness")
        g.add_edge("harness", "flash")
        g.add_edge("flash", "verify")
        g.add_edge("verify", "diagnostics")
        g.add_edge("diagnostics", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"electrical_state": {
            "phase": ElectricalPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _harness(self, s): return transition_to_harness_routed(s)
    def _flash(self, s): return transition_to_ecu_flashed(s)
    def _verify(self, s): return transition_to_open_source_verified(s)
    def _diagnostics(self, s): return transition_to_diagnostics_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["ElectricalIntegrationCell"]
