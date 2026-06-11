"""QualityRoadTestCell — sarutahiko R0 Pregel cell (L5c). G12 KPI + Norimichi driver. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    RoadTestPhase, RoadTestState,
    transition_to_dyno_run_complete, transition_to_g12_kpi_verified,
    transition_to_public_road_test_complete, transition_to_norimichi_attestation,
    transition_to_record_emitted,
)


class QualityRoadTestCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("dyno", self._dyno)
        g.add_node("g12", self._g12)
        g.add_node("road", self._road)
        g.add_node("norimichi", self._norimichi)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "dyno")
        g.add_edge("dyno", "g12")
        g.add_edge("g12", "road")
        g.add_edge("road", "norimichi")
        g.add_edge("norimichi", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"road_test_state": {
            "phase": RoadTestPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _dyno(self, s): return transition_to_dyno_run_complete(s)
    def _g12(self, s): return transition_to_g12_kpi_verified(s)
    def _road(self, s): return transition_to_public_road_test_complete(s)
    def _norimichi(self, s): return transition_to_norimichi_attestation(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["QualityRoadTestCell"]
