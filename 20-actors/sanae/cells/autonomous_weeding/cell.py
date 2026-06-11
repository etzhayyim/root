"""LangGraph Pregel wrapper for the sanae autonomous_weeding (草薙) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606032100 §Design).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_classified,
    transition_to_pass_logged,
    transition_to_scanned,
    transition_to_weed_cleared,
)


class AutonomousWeedingCell:
    """Herbicide-free vision-guided weeding (kusanagi crawler). G3/G4/G9."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_scanned,
            transition_to_classified,
            transition_to_weed_cleared,
            transition_to_pass_logged,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "sanae R0 scaffold: activate autonomous_weeding via Council ADR (post-2606032100 ratification)"
        )
