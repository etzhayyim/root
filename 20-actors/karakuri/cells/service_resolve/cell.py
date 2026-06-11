"""LangGraph Pregel wrapper for the karakuri service_resolve (絡繰) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039200). The lookup -> tier-select ->
tos-stance path is implemented as pure, unit-tested transitions in state_machine.py.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_lookup,
    transition_tier_select,
    transition_tos_stance,
)


class ServiceResolveCell:
    """Resolve a service to capability + safest tier + both ToS stance axes. G2/G6/G8."""

    def __init__(self) -> None:
        self._steps = [transition_lookup, transition_tier_select, transition_tos_stance]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "karakuri R0 scaffold: activate service_resolve via Council ADR (post-2606039200)"
        )
