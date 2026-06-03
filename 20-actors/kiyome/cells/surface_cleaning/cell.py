"""LangGraph Pregel wrapper for the kiyome surface_cleaning (箒) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606032100 §Design).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_cleaned,
    transition_to_pass_logged,
    transition_to_traversed,
)


class SurfaceCleaningCell:
    """Privacy-by-construction floor/surface cleaning (houki rover + nugui arm). G3/G4/G9."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_traversed,
            transition_to_cleaned,
            transition_to_pass_logged,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kiyome R0 scaffold: activate surface_cleaning via Council ADR (post-2606032100 ratification)"
        )
