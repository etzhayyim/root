"""LangGraph Pregel wrapper for 助 (tasuke) account_recovery — R0 scaffold.

Generates a self-help account-recovery procedure for the member to follow themselves (G2
:self-submit — 助 never logs into the member's account). Coded core in state_machine.py.
.solve() raises at R0 — any live adapter execution is Council Lv6+ + operator gated (G9)."""
from __future__ import annotations

from typing import Any


class AccountRecoveryCell:
    """Account-recovery self-help plan. G1 (free) / G2 (:self-submit) / G7 (no-server-key)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tasuke R0 scaffold: account_recovery emits a self-help plan offline; 助 never logs "
            "into the member's account — live execution is Council Lv6+ + operator gated (G9)."
        )
