"""LangGraph Pregel wrapper for the suji (筋) load_solve cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606061900 §Roadmap). The cell
runs static inverse dynamics for a posture (the kami-genesis PlanarChain gravity term) and
distributes the joint moments to Hill-type muscle %MVC, enforcing NON-DIAGNOSTIC output by
construction (G1, 医師法 §17). The phase transitions are pure and unit-tested
(state_machine.py); the cell body stays gated.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    LoadState,
    transition_assert_nondiagnostic,
    transition_emit,
    transition_muscle_distribute,
    transition_static_inverse_dynamics,
)


class LoadSolveCell:
    """Static inverse-dynamics + muscle %MVC for a posture. G1/G9/G10."""

    def __init__(self) -> None:
        self._steps = [
            transition_static_inverse_dynamics,
            transition_muscle_distribute,
            transition_assert_nondiagnostic,
            transition_emit,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "suji R0 scaffold: activate load_solve via Council ADR "
            "(post-2606061900 ratification; live kizashi-fed solves Lv6+ + operator gated)"
        )
