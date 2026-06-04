"""VinAttestationBinderCell — sarutahiko R0 Pregel cell (terminal). G2 + G13. R0 scaffold."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from .state_machine import (
    BinderPhase, BinderState,
    transition_to_records_collected, transition_to_vin_assigned,
    transition_to_vehicle_did_issued, transition_to_kotoba-datomic_anchored,
    transition_to_record_emitted,
)


class VinAttestationBinderCell:
    def __init__(self) -> None:
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        g = StateGraph(dict)
        g.add_node("init", self._init)
        g.add_node("collect", self._collect)
        g.add_node("vin", self._vin)
        g.add_node("did", self._did)
        g.add_node("anchor", self._anchor)
        g.add_node("record", self._record)
        g.add_edge(START, "init")
        g.add_edge("init", "collect")
        g.add_edge("collect", "vin")
        g.add_edge("vin", "did")
        g.add_edge("did", "anchor")
        g.add_edge("anchor", "record")
        g.add_edge("record", END)
        return g.compile()

    def _init(self, state: dict[str, Any]) -> dict[str, Any]:
        return {"binder_state": {
            "phase": BinderPhase.INIT.value,
            "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
            "completionPct": 0,
        }}

    def _collect(self, s): return transition_to_records_collected(s)
    def _vin(self, s): return transition_to_vin_assigned(s)
    def _did(self, s): return transition_to_vehicle_did_issued(s)
    def _anchor(self, s): return transition_to_kotoba-datomic_anchored(s)
    def _record(self, s): return transition_to_record_emitted(s)

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sarutahiko R0 scaffold: activate via Council ADR-2605252515 post-ratification"
        )


__all__ = ["VinAttestationBinderCell"]
