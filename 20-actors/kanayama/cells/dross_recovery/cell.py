"""DrossRecoveryCell — kanayama R0 Pregel cell (L3 cross). G14 closed-loop dross. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    DrossPhase, DrossState,
    transition_to_dross_collected, transition_to_salt_cake_processed,
    transition_to_secondary_al_recovered, transition_to_k_salt_recycled,
    transition_to_record_emitted,
)


class DrossRecoveryCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("collect", self._collect)
        g.add_node("salt_cake", self._salt_cake)
        g.add_node("al", self._al)
        g.add_node("k_salt", self._k_salt)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "collect")
        g.add_edge("collect", "salt_cake")
        g.add_edge("salt_cake", "al")
        g.add_edge("al", "k_salt")
        g.add_edge("k_salt", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"dross_state": {
            "phase": DrossPhase.INIT.value,
            "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
            "completionPct": 0,
        }}

    def _collect(self, s): return transition_to_dross_collected(s)
    def _salt_cake(self, s): return transition_to_salt_cake_processed(s)
    def _al(self, s): return transition_to_secondary_al_recovered(s)
    def _k_salt(self, s): return transition_to_k_salt_recycled(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kanayama R0 scaffold: activate via Council ADR-2605252415 post-ratification"
        )


__all__ = ["DrossRecoveryCell"]
