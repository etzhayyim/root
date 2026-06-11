"""SystemIntegrationCell — watatsumi R0 Pregel cell (L4).

Propulsion + life support + sensors + comms + Charter Rider scan.
R0 scaffold — .solve() raises RuntimeError until R1.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SystemIntegrationPhase,
    SystemIntegrationState,
    transition_to_propulsion_installed,
    transition_to_life_support_installed,
    transition_to_sensors_installed,
    transition_to_comms_installed,
    transition_to_charter_scan_passed,
    transition_to_attestation_emitted,
)


class SystemIntegrationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("propulsion", self._propulsion)
        g.add_node("life_support", self._life_support)
        g.add_node("sensors", self._sensors)
        g.add_node("comms", self._comms)
        g.add_node("charter_scan", self._charter_scan)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "propulsion")
        g.add_edge("propulsion", "life_support")
        g.add_edge("life_support", "sensors")
        g.add_edge("sensors", "comms")
        g.add_edge("comms", "charter_scan")
        g.add_edge("charter_scan", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "system_integration_state": {
                "phase": SystemIntegrationPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "completionPct": 0,
            }
        }

    def _propulsion(self, s): return transition_to_propulsion_installed(s)
    def _life_support(self, s): return transition_to_life_support_installed(s)
    def _sensors(self, s): return transition_to_sensors_installed(s)
    def _comms(self, s): return transition_to_comms_installed(s)
    def _charter_scan(self, s): return transition_to_charter_scan_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["SystemIntegrationCell"]
