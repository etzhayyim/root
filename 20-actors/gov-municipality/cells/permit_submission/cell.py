"""
PermitSubmissionCell — gov-municipality Phase 0 Pregel cell.

Per ADR-2605250800: jurisdiction lookup → permit template → RPC submission.
Input: projectScope (siteId, buildingType, construction cost).
Output: permitApplicationId + submission confirmation.

5-node LangGraph:
  START → jurisdiction_identified → template_selected → application_prepared → submitted → END
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from .state_machine import (
    PermitPhase,
    PermitState,
    transition_to_jurisdiction_identified,
    transition_to_template_selected,
    transition_to_application_prepared,
    transition_to_submitted,
)


class PermitSubmissionCell:
    """Permit application submission (R0+ scaffold, R1+ concrete)."""

    def __init__(self) -> None:
        self.graph: StateGraph[dict[str, Any]] | None = None

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initialize permit state from input."""
        projectId = state.get("projectId", "unknown")
        init_state = PermitState(
            phase=PermitPhase.INIT,
            projectId=projectId,
            completionPct=0,
        )
        return {"permit_state": init_state.__dict__, "next_node": "jurisdiction"}

    def _jurisdiction_identified(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → JURISDICTION_IDENTIFIED: Lookup jurisdiction."""
        return transition_to_jurisdiction_identified(state)

    def _template_selected(self, state: dict[str, Any]) -> dict[str, Any]:
        """JURISDICTION_IDENTIFIED → TEMPLATE_SELECTED: Match template."""
        return transition_to_template_selected(state)

    def _application_prepared(self, state: dict[str, Any]) -> dict[str, Any]:
        """TEMPLATE_SELECTED → APPLICATION_PREPARED: Fill application."""
        return transition_to_application_prepared(state)

    def _submitted(self, state: dict[str, Any]) -> dict[str, Any]:
        """APPLICATION_PREPARED → SUBMITTED: RPC submit to jurisdiction."""
        return transition_to_submitted(state)

    def _build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build LangGraph (5 nodes)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("jurisdiction", self._jurisdiction_identified)
        graph.add_node("template", self._template_selected)
        graph.add_node("prepare", self._application_prepared)
        graph.add_node("submit", self._submitted)

        graph.add_edge("init", "jurisdiction")
        graph.add_edge("jurisdiction", "template")
        graph.add_edge("template", "prepare")
        graph.add_edge("prepare", "submit")
        graph.add_edge("submit", "__end__")

        graph.set_entry_point("init")
        return graph.compile()

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell."""
        if self.graph is None:
            self.graph = self._build_graph()
        return self.graph.invoke(state)
