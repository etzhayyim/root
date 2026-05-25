"""
StructuralAssemblyCell — tatekata R1+ Pregel cell (concrete implementation).

Per ADR-2605250715 §2 (Phase 2 cadence): multi-robot coordination (Giemon shoring + Otete assembly).
Input: foundationAuthorized record (from foundation_excavation).
Output: structuralAuthRecord (MST, witness-signed).

8-node LangGraph super-step state machine:
  START → load_bim → validate_foundations → coordinate_robots → execute_assembly
        → metrology_check → witness_attestation → emit_record → END

  (metrology_check may branch to halt)

R1+ Status: Concrete implementation with mock data flow. Production-ready structure.
ADR-2605250715 R0 approved; R1 activation gate: Council Lv6+ + SME structural engineer.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from .state_machine import (
    StructuralPhase,
    StructuralState,
    transition_to_bim_loaded,
    transition_to_foundation_validated,
    transition_to_robot_coordinated,
    transition_to_execution,
    transition_to_metrology_check,
    transition_to_witness_attestation,
    emit_structural_auth_record,
    halt_on_metrology_anomaly,
)


class StructuralAssemblyCell:
    """Structural assembly orchestration (R1+ production-ready)."""

    def __init__(self) -> None:
        self.graph: StateGraph[dict[str, Any]] | None = None

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initialize structural state from input."""
        projectId = state.get("projectId", "unknown")
        init_state = StructuralState(
            phase=StructuralPhase.INIT,
            projectId=projectId,
            completionPct=0,
        )
        return {"structural_state": init_state.__dict__, "next_node": "load_bim"}

    def _load_bim_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → BIM_LOADED: Load CAD from vendor-free source (FreeCAD STEP)."""
        return transition_to_bim_loaded(state)

    def _validate_foundations(self, state: dict[str, Any]) -> dict[str, Any]:
        """BIM_LOADED → FOUNDATION_VALIDATED: Compare survey vs design assumptions."""
        return transition_to_foundation_validated(state)

    def _coordinate_robots(self, state: dict[str, Any]) -> dict[str, Any]:
        """FOUNDATION_VALIDATED → ROBOT_COORDINATED: Giemon + Otete trajectory planning."""
        return transition_to_robot_coordinated(state)

    def _execute_assembly(self, state: dict[str, Any]) -> dict[str, Any]:
        """ROBOT_COORDINATED → EXECUTION: Giemon shoring + Otete assembly (mock completion)."""
        return transition_to_execution(state)

    def _metrology_check(self, state: dict[str, Any]) -> dict[str, Any]:
        """EXECUTION → METROLOGY_CHECK or ANOMALY_HALT: Mimi plumb/level verification."""
        return transition_to_metrology_check(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        """METROLOGY_CHECK → WITNESS_WAIT (fixed-point): Collect ≥2 robot Ed25519 signatures."""
        return transition_to_witness_attestation(state)

    def _emit_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """WITNESS_WAIT → COMPLETE: Emit structuralAuthRecord to MST."""
        return emit_structural_auth_record(state)

    def _halt(self, state: dict[str, Any]) -> dict[str, Any]:
        """ANOMALY_HALT: Halt assembly, escalate to human."""
        return halt_on_metrology_anomaly(state)

    def _build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build LangGraph super-step loop (8 nodes)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("load_bim", self._load_bim_model)
        graph.add_node("validate", self._validate_foundations)
        graph.add_node("coordinate", self._coordinate_robots)
        graph.add_node("execute", self._execute_assembly)
        graph.add_node("metrology", self._metrology_check)
        graph.add_node("witness", self._witness_attestation)
        graph.add_node("emit", self._emit_record)
        graph.add_node("halt", self._halt)

        graph.add_edge("init", "load_bim")
        graph.add_edge("load_bim", "validate")
        graph.add_edge("validate", "coordinate")
        graph.add_edge("coordinate", "execute")
        graph.add_edge("execute", "metrology")

        def route_metrology(state: dict[str, Any]) -> str:
            return state.get("next_node", "witness")

        graph.add_conditional_edges("metrology", route_metrology, {"witness": "witness", "halt": "halt"})

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
