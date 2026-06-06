"""LangGraph Pregel wrapper for kawaraban article_mirror (瓦版) — R0 scaffold.

Mirrors a real article as an observation (G1 no-verdict / G4 link-out / G9 no-speak-as).
Coded reasoner in state_machine.py. .solve() raises at R0 — live article ingest is Council
Lv6+ + operator gated (G8).
"""
from __future__ import annotations
from typing import Any


class ArticleMirrorCell:
    """Mirror a real article as observation. G1/G4/G9."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kawaraban R0 scaffold: article_mirror validates offline; live article ingest is "
            "Council Lv6+ + operator gated (G8)."
        )
