"""SectionJoiningCell — watatsumi R0 Pregel cell (L5a).

Final ring-to-ring multi-pass TIG + 100% RT + PWHT. R0 scaffold.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SectionJoiningPhase,
    SectionJoiningState,
    transition_to_sections_aligned,
    transition_to_multipass_tig_complete,
    transition_to_rt_100pct_passed,
    transition_to_pwht_complete,
    transition_to_attestation_emitted,
)


class SectionJoiningCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("align", self._align)
        g.add_node("tig", self._tig)
        g.add_node("rt", self._rt)
        g.add_node("pwht", self._pwht)
        g.add_node("attestation", self._attestation)
        g.add_edge(START, "init")
        g.add_edge("init", "align")
        g.add_edge("align", "tig")
        g.add_edge("tig", "rt")
        g.add_edge("rt", "pwht")
        g.add_edge("pwht", "attestation")
        g.add_edge("attestation", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "section_joining_state": {
                "phase": SectionJoiningPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "completionPct": 0,
            }
        }

    def _align(self, s): return transition_to_sections_aligned(s)
    def _tig(self, s): return transition_to_multipass_tig_complete(s)
    def _rt(self, s): return transition_to_rt_100pct_passed(s)
    def _pwht(self, s): return transition_to_pwht_complete(s)
    def _attestation(self, s): return transition_to_attestation_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["SectionJoiningCell"]
