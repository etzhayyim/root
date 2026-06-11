"""LangGraph Pregel wrapper for the kamado transition_bridge (竈) cell — R0 scaffold.

Routes, never adjudicates (G4). A converted site → hikari (solar), a dismantled unit →
hodoki (disassembly) + kanayama (metal recovery) + haraedo (bulky waste); a fossil-policy
question → danjo (non-adjudicating fact trace) + moushibumi (neutral public comment).
kamado decommissions and synthesizes; it does not lobby. .solve() raises until activation.
"""
from __future__ import annotations

from typing import Any

# the routing table this cell encodes (R0: declarative, not yet executed)
ROUTES = {
    "converted-site": ["hikari"],
    "dismantled-unit": ["hodoki", "kanayama", "haraedo"],
    "remediated-land": ["hikari", "mitsuho"],
    "fossil-policy-question": ["danjo", "moushibumi"],
    "displaced-worker": ["displacement-dividend"],  # ADR-2606032130, G9
}


class TransitionBridgeCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kamado R0 scaffold: activate transition_bridge via Council ADR (post-2606051500 ratification)"
        )
