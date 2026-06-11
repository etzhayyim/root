"""LangGraph Pregel wrapper for 朱 (ake) triage — R0 scaffold.

G2/G6 advisory membrane: scores risk + quality and routes (never decides). Coded core in
state_machine.py over methods/triage.py. .solve() raises at R0 — any live LLM refinement of the
scores is Murakumo-only (G6) and the live pipeline is Council Lv6+ + operator gated (G8).
"""
from __future__ import annotations

from typing import Any


class TriageCell:
    """Risk + quality scoring and routing. G2/G6 — non-adjudicating."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "ake R0 scaffold: triage scores + routes offline; the LLM never decides (G2) and "
            "live inference is Murakumo-only (G6), Council Lv6+ + operator gated (G8)."
        )
