"""
MepInstallationCell — tatekata R1+ Pregel cell (concrete implementation).

Per ADR-2605250715 §2 (Phase 3 cadence): Otete arm routes HVAC/electrical/plumbing.
Input: structuralAuthRecord (from structural_assembly).
Output: mepSignoffRecord (MST, witness-signed).

8-node LangGraph super-step state machine:
  START → route_ductwork → route_conduit → route_piping → pressure_test
        → witness_attestation → emit_record → END

  (pressure_test may branch to halt)

R1+ Status: Concrete implementation with mock data flow. Production-ready structure.
ADR-2605250715 R0 approved; R1 activation gate: Council Lv6+ + SME MEP engineer.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from .state_machine import (
    MepPhase,
    MepState,
    transition_to_ductwork_routed,
    transition_to_conduit_routed,
    transition_to_piping_routed,
    transition_to_pressure_test,
    transition_to_witness_attestation,
    emit_mep_signoff_record,
    halt_on_test_failure,
)


class MepInstallationCell:
    """MEP installation orchestration (R1+ production-ready)."""

    def __init__(self) -> None:
        self.graph: StateGraph[dict[str, Any]] | None = None

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initialize MEP state from input."""
        projectId = state.get("projectId", "unknown")
        init_state = MepState(
            phase=MepPhase.INIT,
            projectId=projectId,
            completionPct=0,
        )
        return {"mep_state": init_state.__dict__, "next_node": "ductwork"}

    def _route_ductwork(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → DUCTWORK_ROUTED: HVAC Otete arm trajectory."""
        return transition_to_ductwork_routed(state)

    def _route_conduit(self, state: dict[str, Any]) -> dict[str, Any]:
        """DUCTWORK_ROUTED → CONDUIT_ROUTED: Electrical Otete arm trajectory."""
        return transition_to_conduit_routed(state)

    def _route_piping(self, state: dict[str, Any]) -> dict[str, Any]:
        """CONDUIT_ROUTED → PIPING_ROUTED: Water/gas Otete arm trajectory."""
        return transition_to_piping_routed(state)

    def _pressure_test(self, state: dict[str, Any]) -> dict[str, Any]:
        """PIPING_ROUTED → PRESSURE_TEST or TEST_FAIL: Hydro/pneumatic testing."""
        return transition_to_pressure_test(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        """PRESSURE_TEST → WITNESS_WAIT: Collect ≥2 robot Ed25519 signatures."""
        return transition_to_witness_attestation(state)

    def _emit_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """WITNESS_WAIT → COMPLETE: Emit mepSignoffRecord to MST."""
        return emit_mep_signoff_record(state)

    def _halt(self, state: dict[str, Any]) -> dict[str, Any]:
        """TEST_FAIL: Halt MEP, escalate."""
        return halt_on_test_failure(state)

    def _build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build LangGraph super-step loop (8 nodes)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("ductwork", self._route_ductwork)
        graph.add_node("conduit", self._route_conduit)
        graph.add_node("piping", self._route_piping)
        graph.add_node("test", self._pressure_test)
        graph.add_node("witness", self._witness_attestation)
        graph.add_node("emit", self._emit_record)
        graph.add_node("halt", self._halt)

        graph.add_edge("init", "ductwork")
        graph.add_edge("ductwork", "conduit")
        graph.add_edge("conduit", "piping")
        graph.add_edge("piping", "test")

        def route_test(state: dict[str, Any]) -> str:
            return state.get("next_node", "witness")

        graph.add_conditional_edges("test", route_test, {"witness": "witness", "halt": "halt"})

        graph.add_edge("witness", "emit")
        graph.add_edge("emit", "__end__")
        graph.add_edge("halt", "__end__")

        graph.set_entry_point("init")
        return graph.compile()

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell super-step loop."""
        if self.graph is None:
            self.graph = self._build_graph()
        return self.graph.invoke(state)
