"""TsutaeDeviceAttestationCell — tsutae R0 Pregel cell (L7, levi). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    DevicePhase,
    transition_to_bom_lineage_assembled,
    transition_to_robot_quorum_signed,
    transition_to_did_minted,
    transition_to_attestation_emitted,
)


class TsutaeDeviceAttestationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("lineage", self._lineage)
        g.add_node("quorum", self._quorum)
        g.add_node("mint", self._mint)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "lineage")
        g.add_edge("lineage", "quorum")
        g.add_edge("quorum", "mint")
        g.add_edge("mint", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"device_state": {
            "phase": DevicePhase.INIT.value,
            "serial": state.get("serial", "TSUTAE-SN-0001"),
            "completionPct": 0,
        }}

    def _lineage(self, s): return transition_to_bom_lineage_assembled(s)
    def _quorum(self, s): return transition_to_robot_quorum_signed(s)
    def _mint(self, s): return transition_to_did_minted(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeDeviceAttestationCell"]
