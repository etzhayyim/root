"""LangGraph Pregel wrapper for 潮目 (shionome) ingest — R0 scaffold.

Validates + records public market-data batches as :bucket/:flow/:snap datoms. Coded core in
state_machine.py. .solve() raises at R0 — live market-data ingest is Council Lv6+ + operator
gated (G8).
"""
from __future__ import annotations

from typing import Any


class IngestCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shionome R0 scaffold: ingest validates offline; live market-data ingest is "
            "Council Lv6+ + operator gated (G8)."
        )
