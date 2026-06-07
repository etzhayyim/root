"""LangGraph Pregel wrapper for the karakuri export_roundtrip (絡繰) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039200). The owner-check ->
format-select -> export-plan path is implemented as pure, unit-tested transitions in
state_machine.py; the live pull/push is G6-gated.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_export_plan,
    transition_format_select,
    transition_owner_check,
)


class ExportRoundtripCell:
    """T3 data-portability: export the member's OWN data, encrypted (G9). G6/G7/G9."""

    def __init__(self) -> None:
        self._steps = [
            transition_owner_check,
            transition_format_select,
            transition_export_plan,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "karakuri R0 scaffold: activate export_roundtrip via Council ADR (post-2606039200)"
        )
