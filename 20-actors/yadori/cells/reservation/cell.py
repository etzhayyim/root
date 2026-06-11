"""LangGraph Pregel wrapper for the yadori reservation (宿り) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606038400 §Decision).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_authorized,
    transition_to_intent_built,
    transition_to_quoted,
    transition_to_screened,
)


class ReservationCell:
    """Member-principal, server-keyless domain reservation. G2/G3/G5/G6/G7."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_screened,
            transition_to_quoted,
            transition_to_intent_built,
            transition_to_authorized,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yadori R0 scaffold: activate reservation via Council ADR (post-2606038400 ratification)"
        )
