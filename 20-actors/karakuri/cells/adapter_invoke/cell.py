"""LangGraph Pregel wrapper for the karakuri adapter_invoke (絡繰) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039200 §Decision). The dry-run
planning path (tos-gate -> mutate-gate -> dry-run -> execute-gated) is implemented as pure,
unit-tested transitions in state_machine.py; live adapter execution is Council Lv6+ + operator
gated (G6).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_dry_run,
    transition_execute_gated,
    transition_mutate_gate,
    transition_tos_gate,
)


class AdapterInvokeCell:
    """Single-ServiceOp adapter executor (T1 official-API > T2 browser-use > T3 export). G2/G5/G6/G7."""

    def __init__(self) -> None:
        self._steps = [
            transition_tos_gate,
            transition_mutate_gate,
            transition_dry_run,
            transition_execute_gated,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "karakuri R0 scaffold: activate adapter_invoke via Council ADR "
            "(post-2606039200 ratification); live adapter execution is Council Lv6+ + operator gated"
        )
