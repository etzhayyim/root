"""TsutaeChassisAssemblyCell — tsutae R0 Pregel cell (L2, zebulun). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    ChassisPhase,
    transition_to_components_staged,
    transition_to_mic_killswitch_verified,
    transition_to_repair_modularity_checked,
    transition_to_chassis_assembled,
    transition_to_attestation_emitted,
)


class TsutaeChassisAssemblyCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("stage", self._stage)
        g.add_node("mic_guard", self._mic_guard)
        g.add_node("repair_guard", self._repair_guard)
        g.add_node("assemble", self._assemble)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "stage")
        g.add_edge("stage", "mic_guard")
        g.add_edge("mic_guard", "repair_guard")
        g.add_edge("repair_guard", "assemble")
        g.add_edge("assemble", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"chassis_state": {
            "phase": ChassisPhase.INIT.value,
            "chassisId": state.get("chassisId", "TSUTAE-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _stage(self, s): return transition_to_components_staged(s)
    def _mic_guard(self, s): return transition_to_mic_killswitch_verified(s)
    def _repair_guard(self, s): return transition_to_repair_modularity_checked(s)
    def _assemble(self, s): return transition_to_chassis_assembled(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeChassisAssemblyCell"]
