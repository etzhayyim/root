"""SectionAssemblyCell — watatsumi R0 Pregel cell (L2).

Stack N pressure-hull rings + bulkheads + penetrators. N1 weapons-mount
enforcement. R0 scaffold — .solve() raises RuntimeError until R1.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SectionAssemblyPhase,
    SectionAssemblyState,
    transition_to_rings_verified,
    transition_to_rings_stacked,
    transition_to_frames_installed,
    transition_to_penetrators_installed,
    transition_to_attestation_emitted,
)


class SectionAssemblyCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify_rings", self._verify_rings)
        g.add_node("stack", self._stack)
        g.add_node("frames", self._frames)
        g.add_node("penetrators", self._penetrators)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "verify_rings")
        g.add_edge("verify_rings", "stack")
        g.add_edge("stack", "frames")
        g.add_edge("frames", "penetrators")
        g.add_edge("penetrators", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "section_assembly_state": {
                "phase": SectionAssemblyPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "sectionIndex": state.get("sectionIndex", 0),
                "completionPct": 0,
            }
        }

    def _verify_rings(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_rings_verified(state)

    def _stack(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_rings_stacked(state)

    def _frames(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_frames_installed(state)

    def _penetrators(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_penetrators_installed(state)

    def _attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_attestation_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["SectionAssemblyCell"]
