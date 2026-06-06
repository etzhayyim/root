"""LangGraph Pregel wrapper for mitooshi forecast_issue (見通し) — R0 scaffold.

G1/G2 invariant gate: emits a probabilistic forecast (distribution-only, non-speculative
use) into the Datom log with its info-as-of stamp. Coded reasoner in state_machine.py.
.solve() raises at R0 — live forecast publication (atproto firehose) is Council Lv6+ +
operator gated (G10).
"""
from __future__ import annotations
from typing import Any


class ForecastIssueCell:
    """Distribution-only, non-speculative forecast issuance. G1/G2."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "mitooshi R0 scaffold: forecast_issue validates offline; live forecast "
            "publication is Council Lv6+ + operator gated (G10)."
        )
