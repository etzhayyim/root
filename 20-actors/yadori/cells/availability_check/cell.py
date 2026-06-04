"""LangGraph Pregel wrapper for the yadori availability_check (宿り) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606038400 §Decision). The wired RDAP
classifier + G7 live gate live in state_machine.py and are unit-tested.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_availability_recorded,
    transition_to_classified,
    transition_to_normalized,
    transition_to_rdap_resolved,
)


class AvailabilityCheckCell:
    """RDAP domain-availability check. Read-only (G1); live fetch operator-gated (G7)."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_normalized,
            transition_to_rdap_resolved,
            transition_to_classified,
            transition_to_availability_recorded,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "yadori R0 scaffold: activate availability_check via Council ADR (post-2606038400 ratification)"
        )
