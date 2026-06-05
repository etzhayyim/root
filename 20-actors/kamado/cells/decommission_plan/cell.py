"""LangGraph Pregel wrapper for the kamado decommission_plan (竈) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606051500 §Decision).
The G3 intervention guard + G5 no-server-key + G8 outward-gate live in state_machine.py
and are unit-tested at R0.
"""
from __future__ import annotations

from typing import Any

from .state_machine import (transition_to_gated, transition_to_planned,
                            transition_to_scoped)


class DecommissionPlanCell:
    """§2(d) wind-down/convert plan for an existing fossil asset. G3/G5/G8/G9."""

    def __init__(self) -> None:
        self._steps = [transition_to_scoped, transition_to_planned, transition_to_gated]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kamado R0 scaffold: activate decommission_plan via Council ADR (post-2606051500 ratification)"
        )
