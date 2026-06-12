"""LangGraph Pregel wrapper for the tedai intent_plan (手代) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606101400). The parse-brief ->
prohibition-scan -> emit-plan path is implemented as pure, unit-tested transitions in
state_machine.py. The NL → command leg (Murakumo, G4) is R1; R0 takes literal command lines.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_emit_plan,
    transition_parse_brief,
    transition_prohibition_scan,
)


class IntentPlanCell:
    """Member brief → prohibition-scanned, gated, dry-run DesktopOps. G2/G5/G6/G8."""

    def __init__(self) -> None:
        self._steps = [transition_parse_brief, transition_prohibition_scan, transition_emit_plan]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tedai R0 scaffold: activate intent_plan via Council ADR (post-2606101400)"
        )
