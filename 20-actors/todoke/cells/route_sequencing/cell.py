"""LangGraph Pregel wrapper for the todoke route_sequencing (順路) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606042300 §Design).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_envelope_checked,
    transition_to_job_loaded,
    transition_to_route_emitted,
    transition_to_sequenced,
)


class RouteSequencingCell:
    """Last-mile stop sequencing + G7 safety envelope. G4/G7/G11."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_job_loaded,
            transition_to_envelope_checked,
            transition_to_sequenced,
            transition_to_route_emitted,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "todoke R0 scaffold: activate route_sequencing via Council ADR (post-2606042300 ratification)"
        )
