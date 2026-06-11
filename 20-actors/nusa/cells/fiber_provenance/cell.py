"""LangGraph Pregel wrapper for the nusa fiber_provenance (幣) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039800 §Decision).
The G1 THC-class screen lives in state_machine.py and is unit-tested at R0.
"""

from __future__ import annotations

from typing import Any

from .state_machine import transition_to_recorded, transition_to_screened


class FiberProvenanceCell:
    """Cultivar → fibre-use provenance, gated by the THC-class screen. G1/G2."""

    def __init__(self) -> None:
        self._steps = [transition_to_screened, transition_to_recorded]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "nusa R0 scaffold: activate fiber_provenance via Council ADR (post-2606039800 ratification)"
        )
