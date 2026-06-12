"""LangGraph Pregel wrapper for the tedai actuate_invoke (手代) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606101400). The plan-op -> stance-gate
-> mutate-gate -> build-adapter-plan path is implemented as pure, unit-tested transitions in
state_machine.py. Live actuation funnels exclusively through methods/actuate_live.py.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_build_adapter_plan,
    transition_mutate_gate,
    transition_plan_op,
    transition_stance_gate,
)


class ActuateInvokeCell:
    """Gated invocation: stance-gate → mutate-gate → dry-run adapter plan. G2/G5/G6/G8."""

    def __init__(self) -> None:
        self._steps = [
            transition_plan_op,
            transition_stance_gate,
            transition_mutate_gate,
            transition_build_adapter_plan,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tedai R0 scaffold: activate actuate_invoke via Council ADR (post-2606101400)"
        )
