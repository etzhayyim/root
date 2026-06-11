"""LangGraph Pregel wrapper for the hotaru commons_readiness (蛍) cell — R0 scaffold.

Aggregates per-stage open-publication coverage of the substrate chain and emits a
commonsReadinessReport routed to the ADR-2605265500 §2 R4+ gate evaluation. NON-
adjudicating (G3): reports the facts; Council decides the gate. The pure-logic
implementation of the aggregation lives in methods/analyze.py (tested).
"""

from __future__ import annotations

from typing import Any


class CommonsReadinessCell:
    """Substrate-commons coverage index → R4+ gate input. Non-adjudicating (G3)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "hotaru R0 scaffold: commons_readiness reporting runs offline via "
            "methods/analyze.py; live atproto publish + Council gate routing is "
            "outward-gated (G8, Council Lv6+ + operator)."
        )
