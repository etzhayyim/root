"""SeaTrialCell — funadaiku R0 Pregel cell.

Speed/endurance trial plus MASS Degree-3 autonomy and COLREG-compliance trial.

Per ADR-2606013400. R0 scaffold — .solve() raises RuntimeError until Council Lv6+
ratifies ADR-2606013415 (R1 activation). Lexicon: com.etzhayyim.funadaiku.seaTrialRecord.
"""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    SeaTrialPhase,
    CellState,
    transition_to_speed_trial, transition_to_endurance_trial, transition_to_mass_autonomy_trial, transition_to_colreg_trial, transition_to_record_emitted,
)


class SeaTrialCell:
    """L5c speed / endurance / autonomy (MASS) / COLREG trial (R0 scaffold)."""

    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(dict)
        graph.add_node("speed_trial", self._step_0)
        graph.add_node("endurance_trial", self._step_1)
        graph.add_node("mass_autonomy_trial", self._step_2)
        graph.add_node("colreg_trial", self._step_3)
        graph.add_node("record_emitted", self._step_4)

        graph.add_edge(START, "speed_trial")
        graph.add_edge("speed_trial", "endurance_trial")
        graph.add_edge("endurance_trial", "mass_autonomy_trial")
        graph.add_edge("mass_autonomy_trial", "colreg_trial")
        graph.add_edge("colreg_trial", "record_emitted")
        graph.add_edge("record_emitted", END)

        return graph.compile()

    def _step_0(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_speed_trial(state)
    def _step_1(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_endurance_trial(state)
    def _step_2(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_mass_autonomy_trial(state)
    def _step_3(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_colreg_trial(state)
    def _step_4(self, state: dict[str, Any]) -> dict[str, Any]:
        return transition_to_record_emitted(state)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell — R0 scaffold raises until R1 activation."""
        raise RuntimeError(
            "funadaiku R0 scaffold: activate via Council ADR-2606013415 post-ratification"
        )


__all__ = ["SeaTrialCell"]
