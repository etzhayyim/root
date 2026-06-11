"""TsutaeFinalQcCell — tsutae R0 Pregel cell (L5, levi). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    QcPhase,
    transition_to_calibrated,
    transition_to_rf_tested,
    transition_to_addiction_ux_audited,
    transition_to_functional_tested,
    transition_to_qc_record_emitted,
)


class TsutaeFinalQcCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("calibrate", self._calibrate)
        g.add_node("rf", self._rf)
        g.add_node("ux_guard", self._ux_guard)
        g.add_node("functional", self._functional)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "calibrate")
        g.add_edge("calibrate", "rf")
        g.add_edge("rf", "ux_guard")
        g.add_edge("ux_guard", "functional")
        g.add_edge("functional", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"qc_state": {
            "phase": QcPhase.INIT.value,
            "deviceId": state.get("deviceId", "TSUTAE-DEV-0001"),
            "completionPct": 0,
        }}

    def _calibrate(self, s): return transition_to_calibrated(s)
    def _rf(self, s): return transition_to_rf_tested(s)
    def _ux_guard(self, s): return transition_to_addiction_ux_audited(s)
    def _functional(self, s): return transition_to_functional_tested(s)
    def _record(self, s): return transition_to_qc_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tsutae R0 scaffold: activate via Council ADR-2605261315 post-ratification"
        )


__all__ = ["TsutaeFinalQcCell"]
