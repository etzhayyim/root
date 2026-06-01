"""TractionElectricalCell — yamabiko R0 Pregel cell (L4). G1+N5 open-source ATP/ATO + G7 propulsion guard. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    TractionPhase, TractionState,
    transition_to_propulsion_guard_checked, transition_to_pantograph_installed,
    transition_to_inverter_installed, transition_to_atp_ato_flashed,
    transition_to_open_source_verified, transition_to_attestation_emitted,
)


class TractionElectricalCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("propulsion", self._propulsion)
        g.add_node("pantograph", self._pantograph)
        g.add_node("inverter", self._inverter)
        g.add_node("atp", self._atp)
        g.add_node("verify", self._verify)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "propulsion")
        g.add_edge("propulsion", "pantograph")
        g.add_edge("pantograph", "inverter")
        g.add_edge("inverter", "atp")
        g.add_edge("atp", "verify")
        g.add_edge("verify", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"traction_state": {
            "phase": TractionPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "completionPct": 0,
        }}

    def _propulsion(self, s): return transition_to_propulsion_guard_checked(s)
    def _pantograph(self, s): return transition_to_pantograph_installed(s)
    def _inverter(self, s): return transition_to_inverter_installed(s)
    def _atp(self, s): return transition_to_atp_ato_flashed(s)
    def _verify(self, s): return transition_to_open_source_verified(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["TractionElectricalCell"]
