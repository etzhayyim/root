"""LangGraph Pregel wrapper for kawaraban issue_compose (瓦版) — R0 scaffold.

Composes a front-面 edition ranked by G2 public-good signals only; unsigned + unpublished +
not-final at R0 (G7/G8/G10). Coded reasoner in state_machine.py. .solve() raises at R0 —
live edition publication is member-signed (G7) + Council Lv6+ + operator gated (G8).
"""
from __future__ import annotations
from typing import Any


class IssueComposeCell:
    """Compose a front-面 edition. G2/G7/G8/G10."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kawaraban R0 scaffold: issue_compose ranks offline by public-good signals; live "
            "edition publication is member-signed (G7) + Council Lv6+ + operator gated (G8)."
        )
