"""
CommissioningCell — tatekata R1+ Pregel cell (concrete implementation).

Per ADR-2605250715 §2 (Phase 5 cadence): final systems test, defect walkdown, waste log.
Input: finishingRecord (from finishing_handoff).
Output: projectClosure record (MST, witness-signed).

6-node LangGraph super-step state machine:
  START → final_systems_test → defect_walkdown → waste_inventory
        → sign_off → emit_record → END

R1+ Status: Concrete implementation with mock data flow.
ADR-2605250715 R0 approved; R1 activation gate: Council Lv6+ + SME project manager.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from .state_machine import (
    CommissioningPhase,
    CommissioningState,
    transition_to_systems_tested,
    transition_to_defect_walkdown,
    transition_to_waste_inventory,
    transition_to_project_signoff,
    emit_project_closure_record,
)


class CommissioningCell:
    """Project commissioning & closure (R1+ production-ready)."""

    def __init__(self) -> None:
        self.graph: StateGraph[dict[str, Any]] | None = None

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initialize commissioning state from input."""
        projectId = state.get("projectId", "unknown")
        init_state = CommissioningState(
            phase=CommissioningPhase.INIT,
            projectId=projectId,
            completionPct=0,
        )
        return {"commissioning_state": init_state.__dict__, "next_node": "test"}

    def _final_systems_test(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → SYSTEMS_TESTED: HVAC/electrical/plumbing verification."""
        return transition_to_systems_tested(state)

    def _defect_walkdown(self, state: dict[str, Any]) -> dict[str, Any]:
        """SYSTEMS_TESTED → DEFECTS_IDENTIFIED: Photo survey + punch-list."""
        return transition_to_defect_walkdown(state)

    def _waste_inventory(self, state: dict[str, Any]) -> dict[str, Any]:
        """DEFECTS_IDENTIFIED → WASTE_LOGGED: Material waste categorization."""
        return transition_to_waste_inventory(state)

    def _project_signoff(self, state: dict[str, Any]) -> dict[str, Any]:
        """WASTE_LOGGED → SIGNED_OFF: Human PM + ≥2 robot sigs."""
        return transition_to_project_signoff(state)

    def _emit_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """SIGNED_OFF → COMPLETE: Emit projectClosure to MST."""
        return emit_project_closure_record(state)

    def _build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build LangGraph super-step loop (6 nodes)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("test", self._final_systems_test)
        graph.add_node("walkdown", self._defect_walkdown)
        graph.add_node("waste", self._waste_inventory)
        graph.add_node("signoff", self._project_signoff)
        graph.add_node("emit", self._emit_record)

        graph.add_edge("init", "test")
        graph.add_edge("test", "walkdown")
        graph.add_edge("walkdown", "waste")
        graph.add_edge("waste", "signoff")
        graph.add_edge("signoff", "emit")
        graph.add_edge("emit", "__end__")

        graph.set_entry_point("init")
        return graph.compile()

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell super-step loop."""
        if self.graph is None:
            self.graph = self._build_graph()
        return self.graph.invoke(state)
