"""HomologationBinderCell — yamabiko R0 Pregel cell (L5c terminal). G2+G13. R0 scaffold."""

from typing import Any
from langgraph.graph import StateGraph, START, END

from .state_machine import (
    HomologationPhase, HomologationState,
    transition_to_records_collected, transition_to_serial_assigned,
    transition_to_trainset_did_issued, transition_to_homologation_authority_review,
    transition_to_kotoba_datomic_anchored, transition_to_record_emitted,
)


class HomologationBinderCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("collect", self._collect)
        g.add_node("serial", self._serial)
        g.add_node("did", self._did)
        g.add_node("authority", self._authority)
        g.add_node("anchor", self._anchor)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "collect")
        g.add_edge("collect", "serial")
        g.add_edge("serial", "did")
        g.add_edge("did", "authority")
        g.add_edge("authority", "anchor")
        g.add_edge("anchor", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"homologation_state": {
            "phase": HomologationPhase.INIT.value,
            "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
            "completionPct": 0,
        }}

    def _collect(self, s): return transition_to_records_collected(s)
    def _serial(self, s): return transition_to_serial_assigned(s)
    def _did(self, s): return transition_to_trainset_did_issued(s)
    def _authority(self, s): return transition_to_homologation_authority_review(s)
    def _anchor(self, s): return transition_to_kotoba_datomic_anchored(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yamabiko R0 scaffold: activate via Council ADR-2605252615 post-ratification"
        )


__all__ = ["HomologationBinderCell"]
