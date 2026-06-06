"""LangGraph Pregel wrapper for kawaraban outlet_ingest (瓦版) — R0 scaffold.

G4/G5 membrane: ingests a public-facing-page outlet; refuses paywall/terminal. Coded
reasoner in state_machine.py. .solve() raises at R0 — live RSS/sitemap fetch is Council
Lv6+ + operator gated (G8).
"""
from __future__ import annotations
from typing import Any


class OutletIngestCell:
    """Public-facing-page outlet ingest. G4/G5."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kawaraban R0 scaffold: outlet_ingest validates offline; live outlet fetch is "
            "Council Lv6+ + operator gated (G8)."
        )
