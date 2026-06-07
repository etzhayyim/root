"""LangGraph Pregel wrapper for 高札 (kosatsu) competing_claim_weave — R0 scaffold.

Computes the divergence/agreement views over the designation event log. .solve() raises at R0
(G8). Offline weave runs via methods/weave.py.
"""
from __future__ import annotations

from typing import Any


class CompetingClaimWeaveCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kosatsu R0 scaffold: competing_claim_weave runs offline; live Datom-log weave is "
            "Council Lv6+ + operator gated (G8)."
        )
