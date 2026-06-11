"""LangGraph Pregel wrapper for 助 (tasuke) platform_abuse — R0 scaffold.

Generates the member-authored platform/bank requests (account freeze/takedown/disclosure;
銀行 不正送金 組戻し・口座凍結依頼 under 振り込め詐欺救済法). Coded core in state_machine.py.
.solve() raises at R0 — live sending is Council Lv6+ + operator gated (G9)."""
from __future__ import annotations

from typing import Any


class PlatformAbuseCell:
    """Platform/bank request generation. G1 (free) / G2 (member sends) / G3 (member-authored)."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "tasuke R0 scaffold: platform_abuse drafts member-authored requests offline; live "
            "sending is Council Lv6+ + operator gated (G9)."
        )
