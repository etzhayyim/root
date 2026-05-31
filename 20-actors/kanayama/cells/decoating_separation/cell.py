"""DecoatingSeparationCell — kanayama R0 Pregel cell (L2). R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    DecoatingPhase,
    DecoatingState,
    transition_to_decoater_heated,
    transition_to_lacquer_burnoff_complete,
    transition_to_shred_complete,
    transition_to_magnetic_separation_complete,
    transition_to_eddy_current_separation_complete,
    transition_to_record_emitted,
)


class DecoatingSeparationCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("heat", self._heat)
        g.add_node("burnoff", self._burnoff)
        g.add_node("shred", self._shred)
        g.add_node("magnetic", self._magnetic)
        g.add_node("eddy", self._eddy)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "heat")
        g.add_edge("heat", "burnoff")
        g.add_edge("burnoff", "shred")
        g.add_edge("shred", "magnetic")
        g.add_edge("magnetic", "eddy")
        g.add_edge("eddy", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"decoating_state": {
            "phase": DecoatingPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _heat(self, s): return transition_to_decoater_heated(s)
    def _burnoff(self, s): return transition_to_lacquer_burnoff_complete(s)
    def _shred(self, s): return transition_to_shred_complete(s)
    def _magnetic(self, s): return transition_to_magnetic_separation_complete(s)
    def _eddy(self, s): return transition_to_eddy_current_separation_complete(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["DecoatingSeparationCell"]
