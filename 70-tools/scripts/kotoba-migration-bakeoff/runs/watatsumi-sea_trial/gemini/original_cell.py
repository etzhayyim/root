"""SeaTrialCell — watatsumi R0 Pregel cell (L5c).

Dock → harbor → deep-water trial. IMCA D-001 equivalent. R0 scaffold.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SeaTrialPhase,
    SeaTrialState,
    transition_to_dock_trial,
    transition_to_harbor_dive,
    transition_to_deep_water_trial,
    transition_to_record_emitted,
)


class SeaTrialCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("dock", self._dock)
        g.add_node("harbor", self._harbor)
        g.add_node("deep_water", self._deep_water)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "dock")
        g.add_edge("dock", "harbor")
        g.add_edge("harbor", "deep_water")
        g.add_edge("deep_water", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "sea_trial_state": {
                "phase": SeaTrialPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "completionPct": 0,
            }
        }

    def _dock(self, s): return transition_to_dock_trial(s)
    def _harbor(self, s): return transition_to_harbor_dive(s)
    def _deep_water(self, s): return transition_to_deep_water_trial(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["SeaTrialCell"]
