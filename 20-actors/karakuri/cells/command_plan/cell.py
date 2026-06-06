"""LangGraph Pregel wrapper for the karakuri command_plan (絡繰) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039200). The parse -> classify ->
charter-scan -> plan path is implemented as pure, unit-tested transitions in state_machine.py; the
live Murakumo NL path is operator-gated (G4).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_charter_scan,
    transition_classify,
    transition_parse,
    transition_plan,
)


class CommandPlanCell:
    """NL brief -> ordered, gated, Charter-scanned ServiceOps (dry-run). G4/G5/G6/G7/N6."""

    def __init__(self) -> None:
        self._steps = [
            transition_parse,
            transition_classify,
            transition_charter_scan,
            transition_plan,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "karakuri R0 scaffold: activate command_plan via Council ADR (post-2606039200); "
            "live Murakumo NL planning is operator-gated (G4)"
        )
