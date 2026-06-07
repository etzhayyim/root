"""LangGraph Pregel wrapper for 系図 (keizu) money_graph — R0 scaffold.

Aggregates disclosed money flows into per-payee concentration. .solve() raises at R0 (G8).
"""
from __future__ import annotations

from typing import Any


class MoneyGraphCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "keizu R0 scaffold: money_graph aggregates offline; live ingest Council Lv6+ + operator gated (G8)."
        )
