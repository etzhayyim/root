"""PressureTestCell — watatsumi R0 Pregel cell (L5b).

1.25× design-depth pressure test with continuous Hibiki AE monitoring.
G12 KPI cap: design depth ≤6500 m civilian. R0 scaffold.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    PressureTestPhase,
    PressureTestState,
    transition_to_design_depth_verified,
    transition_to_dock_lowering,
    transition_to_pressurization,
    transition_to_hold,
    transition_to_depressurization,
    transition_to_record_emitted,
)


class PressureTestCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("verify_depth", self._verify_depth)
        g.add_node("dock", self._dock)
        g.add_node("pressurize", self._pressurize)
        g.add_node("hold", self._hold)
        g.add_node("depressurize", self._depressurize)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "verify_depth")
        g.add_edge("verify_depth", "dock")
        g.add_edge("dock", "pressurize")
        g.add_edge("pressurize", "hold")
        g.add_edge("hold", "depressurize")
        g.add_edge("depressurize", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {
            "pressure_test_state": {
                "phase": PressureTestPhase.INIT.value,
                "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
                "completionPct": 0,
            }
        }

    def _verify_depth(self, s): return transition_to_design_depth_verified(s)
    def _dock(self, s): return transition_to_dock_lowering(s)
    def _pressurize(self, s): return transition_to_pressurization(s)
    def _hold(self, s): return transition_to_hold(s)
    def _depressurize(self, s): return transition_to_depressurization(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "watatsumi R0 scaffold: activate via Council ADR-2605252215 post-ratification"
        )


__all__ = ["PressureTestCell"]
