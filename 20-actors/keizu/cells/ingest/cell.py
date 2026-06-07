"""LangGraph Pregel wrapper for 系図 (keizu) ingest — R0 scaffold.

Validates + records public-source batches as :node/:committee/:rel/:money datoms. Coded core in
state_machine.py. .solve() raises at R0 — live ingest from government portals is Council Lv6+ +
operator gated (G8).
"""
from __future__ import annotations

from typing import Any


class IngestCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "keizu R0 scaffold: ingest validates offline; live public-source ingest is "
            "Council Lv6+ + operator gated (G8)."
        )
