"""LangGraph Pregel wrapper for 扶持 (fuchi) governance_gate — R0 scaffold.

The G7 non-adjudicating router. Coded core in state_machine.py. .solve() raises at R0 — a
binding 1 SBT = 1 vote / Council decision is Council Lv6+ (Lv7+ invariant-adjacent) + operator gated (G10).
"""
from __future__ import annotations

from typing import Any


class GovernanceGateCell:
    """Pure-function route → auto / sbt-vote / council-lv7 / refused. G7/G10."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "fuchi R0 scaffold: governance_gate routes offline; a binding vote / Council "
            "decision is Council Lv6+ (Lv7+ invariant-adjacent) + operator gated (G10)."
        )
