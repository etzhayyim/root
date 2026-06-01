"""
FinishingHandoffCell — tatekata R1+ Pregel cell (concrete implementation).

Per ADR-2605250715 §2 (Phase 4 cadence): surface prep, drywall, paint, trim.
Input: mepSignoffRecord (from mep_installation).
Output: finishingRecord (MST, witness-signed).

7-node LangGraph super-step state machine:
  START → prep_surfaces → drywall_tape_mud → paint_seal → trim_install
        → witness_attestation → emit_record → END

R1+ Status: Concrete implementation with mock data flow.
ADR-2605250715 R0 approved; R1 activation gate: Council Lv6+ + SME finishing contractor.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import StateGraph

from .state_machine import (
    FinishingPhase,
    FinishingState,
    transition_to_prep_complete,
    transition_to_drywall_complete,
    transition_to_paint_complete,
    transition_to_trim_installed,
    transition_to_witness_attestation,
    emit_finishing_record,
)


class FinishingHandoffCell:
    """Finishing handoff orchestration (R1+ production-ready)."""

    def __init__(self) -> None:
        self.graph: StateGraph[dict[str, Any]] | None = None

    def _initialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Initialize finishing state from input."""
        projectId = state.get("projectId", "unknown")
        init_state = FinishingState(
            phase=FinishingPhase.INIT,
            projectId=projectId,
            completionPct=0,
        )
        return {"finishing_state": init_state.__dict__, "next_node": "prep"}

    def _prep_surfaces(self, state: dict[str, Any]) -> dict[str, Any]:
        """INIT → SURFACES_PREPPED: Giemon substrate cleaning."""
        return transition_to_prep_complete(state)

    def _drywall_tape_mud(self, state: dict[str, Any]) -> dict[str, Any]:
        """SURFACES_PREPPED → DRYWALL_COMPLETE: Tape, mud, sand."""
        return transition_to_drywall_complete(state)

    def _paint_seal(self, state: dict[str, Any]) -> dict[str, Any]:
        """DRYWALL_COMPLETE → PAINT_COMPLETE: Primer + finish coats."""
        return transition_to_paint_complete(state)

    def _trim_install(self, state: dict[str, Any]) -> dict[str, Any]:
        """PAINT_COMPLETE → TRIM_INSTALLED: Baseboard, casing, crown."""
        return transition_to_trim_installed(state)

    def _witness_attestation(self, state: dict[str, Any]) -> dict[str, Any]:
        """TRIM_INSTALLED → WITNESS_WAIT: Collect ≥2 robot sigs."""
        return transition_to_witness_attestation(state)

    def _emit_record(self, state: dict[str, Any]) -> dict[str, Any]:
        """WITNESS_WAIT → COMPLETE: Emit finishingRecord to MST."""
        return emit_finishing_record(state)

    def _build_graph(self) -> StateGraph[dict[str, Any]]:
        """Build LangGraph super-step loop (7 nodes)."""
        graph = StateGraph(dict)

        graph.add_node("init", self._initialize_state)
        graph.add_node("prep", self._prep_surfaces)
        graph.add_node("drywall", self._drywall_tape_mud)
        graph.add_node("paint", self._paint_seal)
        graph.add_node("trim", self._trim_install)
        graph.add_node("witness", self._witness_attestation)
        graph.add_node("emit", self._emit_record)

        graph.add_edge("init", "prep")
        graph.add_edge("prep", "drywall")
        graph.add_edge("drywall", "paint")
        graph.add_edge("paint", "trim")
        graph.add_edge("trim", "witness")
        graph.add_edge("witness", "emit")
        graph.add_edge("emit", "__end__")

        graph.set_entry_point("init")
        return graph.compile()

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the cell super-step loop."""
        if self.graph is None:
            self.graph = self._build_graph()
        return self.graph.invoke(state)
