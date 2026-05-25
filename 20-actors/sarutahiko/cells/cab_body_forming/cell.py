"""CabBodyFormingCell — sarutahiko R0 Pregel cell (L3). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    CabPhase, CabState,
    transition_to_sheet_lot_verified, transition_to_hot_stamping_complete,
    transition_to_spot_welding_complete, transition_to_leak_test_passed,
    transition_to_attestation_emitted,
)


class CabBodyFormingCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify", self._verify)
        g.add_node("stamp", self._stamp)
        g.add_node("weld", self._weld)
        g.add_node("leak", self._leak)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify")
        g.add_edge("verify", "stamp")
        g.add_edge("stamp", "weld")
        g.add_edge("weld", "leak")
        g.add_edge("leak", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"cab_state": {
            "phase": CabPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _verify(self, s): return transition_to_sheet_lot_verified(s)
    def _stamp(self, s): return transition_to_hot_stamping_complete(s)
    def _weld(self, s): return transition_to_spot_welding_complete(s)
    def _leak(self, s): return transition_to_leak_test_passed(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["CabBodyFormingCell"]
