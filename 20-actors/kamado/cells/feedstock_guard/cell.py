"""LangGraph Pregel wrapper for the kamado feedstock_guard (竈) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606051500 §Decision).
The G1 feedstock-class screen + G2/D3 carbon balance live in state_machine.py and are
unit-tested at R0.
"""
from __future__ import annotations

from typing import Any

from .state_machine import (transition_to_admitted, transition_to_balanced,
                            transition_to_screened)


class FeedstockGuardCell:
    """Closed-loop-carbon screen + D3 carbon balance. G1/G2 — the defining cell."""

    def __init__(self) -> None:
        self._steps = [transition_to_screened, transition_to_balanced, transition_to_admitted]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kamado R0 scaffold: activate feedstock_guard via Council ADR (post-2606051500 ratification)"
        )
