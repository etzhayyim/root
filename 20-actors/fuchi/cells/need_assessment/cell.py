"""LangGraph Pregel wrapper for 扶持 (fuchi) need_assessment — R0 scaffold.

The G2/G3 in-kind sustenance envelope assessment. Coded core in state_machine.py.
.solve() raises at R0 — live assessment over the real maintainer roster is G10-gated.
"""
from __future__ import annotations

from typing import Any


class NeedAssessmentCell:
    """In-kind sustenance envelope assessment. G2/G3."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "fuchi R0 scaffold: need_assessment builds the in-kind envelope offline; live "
            "assessment over the real roster is Council Lv6+ + operator gated (G10)."
        )
