"""LangGraph Pregel wrapper for the suji (筋) strain_accumulate cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606061900 §Roadmap). The cell
accumulates the Rohmert sustained-isometric dose from per-muscle %MVC into a 強張り stiffness
map, enforcing NON-DIAGNOSTIC (G1) and SELF-REFERENCED Wellbecoming (G3) by construction. The
phase transitions are pure and unit-tested (state_machine.py); the cell body stays gated.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    StrainState,
    transition_assert_self_referenced,
    transition_band,
    transition_emit,
    transition_rohmert_dose,
)


class StrainAccumulateCell:
    """Rohmert dose → stiffness map for a posture's muscle tensions. G1/G3/G9/G10."""

    def __init__(self) -> None:
        self._steps = [
            transition_rohmert_dose,
            transition_band,
            transition_assert_self_referenced,
            transition_emit,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "suji R0 scaffold: activate strain_accumulate via Council ADR "
            "(post-2606061900 ratification; live kizashi-fed solves Lv6+ + operator gated)"
        )
