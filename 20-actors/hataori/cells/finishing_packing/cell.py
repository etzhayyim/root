"""LangGraph Pregel wrapper for the hataori finishing_packing (畳) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606032100 §Design).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_finished,
    transition_to_folded,
    transition_to_lot_attested,
)


class FinishingPackingCell:
    """Terminal cell — emits the finished lot WITH fair-labor provenance (G9/G2)."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_finished,
            transition_to_folded,
            transition_to_lot_attested,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "hataori R0 scaffold: activate finishing_packing via Council ADR (post-2606032100 ratification)"
        )
