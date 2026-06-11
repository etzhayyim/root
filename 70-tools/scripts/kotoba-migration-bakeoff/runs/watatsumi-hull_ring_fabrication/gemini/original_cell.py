"""HullRingFabricationCell — watatsumi R0 Pregel cell (L1).

Per ADR-2605252200 §6 / §3 L1: pressure hull ring rolling + ring-frame welding +
roundness QA. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2605252215 (R1 activation).
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    HullRingPhase,
    HullRingState,
    transition_to_material_verified,
    transition_to_plate_rolled,
    transition_to_ring_frame_welded,
    transition_to_roundness_qa,
    transition_to_attestation_emitted,
)


class HullRingFabricationCell:
    """L1 pressure hull ring fabrication (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("init", self._initialize_state)
        graph.add_node("verify_material", self._verify_material)
        graph.add_node("rolling", self._rolling)
        graph.add_node("ring_weld", self._ring_weld)
        graph.add_node("roundness_qa", self._roundness_qa)
        graph.add_node("attestation", self._attestation)

        graph.add_edge(START, "init")
        graph.add_edge("init", "verify_material")
        graph.add_edge("verify_material", "rolling")
        graph.add_edge("rolling", "ring_weld")
        graph.add_edge("ring_weld", "roundness_qa")
        graph.add_edge("roundness_qa", "attestation")
        graph.add_edge("attestation", END)

        return graph.compile()

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "hull_ring_state": {
                "phase": HullRingPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "ringIndex": state.get("ringIndex", 0),
                "completionPct": 0,
            }
        }

    def _verify_material(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_material_verified(state)

    def _rolling(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_plate_rolled(state)

    def _ring_weld(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_ring_frame_welded(state)

    def _roundness_qa(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_roundness_qa(state)

    def _attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["HullRingFabricationCell"]
