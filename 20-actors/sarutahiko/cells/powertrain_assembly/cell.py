"""PowertrainAssemblyCell — sarutahiko R0 Pregel cell (L2). G7 fuel guard. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    PowertrainPhase, PowertrainState,
    transition_to_fuel_guard_checked, transition_to_engine_installed,
    transition_to_transmission_coupled, transition_to_axles_mounted,
    transition_to_brake_integrated, transition_to_attestation_emitted,
)


class PowertrainAssemblyCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("fuel_guard", self._fuel_guard)
        g.add_node("engine", self._engine)
        g.add_node("transmission", self._transmission)
        g.add_node("axles", self._axles)
        g.add_node("brake", self._brake)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "fuel_guard")
        g.add_edge("fuel_guard", "engine")
        g.add_edge("engine", "transmission")
        g.add_edge("transmission", "axles")
        g.add_edge("axles", "brake")
        g.add_edge("brake", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"powertrain_state": {
            "phase": PowertrainPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _fuel_guard(self, s): return transition_to_fuel_guard_checked(s)
    def _engine(self, s): return transition_to_engine_installed(s)
    def _transmission(self, s): return transition_to_transmission_coupled(s)
    def _axles(self, s): return transition_to_axles_mounted(s)
    def _brake(self, s): return transition_to_brake_integrated(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["PowertrainAssemblyCell"]
