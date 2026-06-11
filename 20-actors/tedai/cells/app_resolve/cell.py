"""LangGraph Pregel wrapper for the tedai app_resolve (手代) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606101400). The lookup -> tier-select ->
stance path is implemented as pure, unit-tested transitions in state_machine.py.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_lookup,
    transition_stance,
    transition_tier_select,
)


class AppResolveCell:
    """Resolve an app to capability + safest tier + synthetic-input stance. G2/G6/G8/N7."""

    def __init__(self) -> None:
        self._steps = [transition_lookup, transition_tier_select, transition_stance]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tedai R0 scaffold: activate app_resolve via Council ADR (post-2606101400)"
        )
