"""LangGraph Pregel wrapper for 朱 (ake) promote — R0 scaffold.

The G8/G9 no-server-key membrane: clears an accepted edit for an append-only revision (and an
optional :representative→:authoritative promotion) only when member/operator-signed. Coded refusal
gate in state_machine.py. .solve() raises at R0 — live promotion / publish is Council Lv6+ +
operator gated (G8).
"""
from __future__ import annotations

from typing import Any


class PromoteCell:
    """No-server-key promotion gate. G4/G8/G9."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "ake R0 scaffold: promote reviews offline; live promotion/publish into the served "
            "registry is Council Lv6+ + operator gated (G8/G9)."
        )
