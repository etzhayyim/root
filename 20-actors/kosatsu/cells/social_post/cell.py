"""LangGraph Pregel wrapper for 高札 (kosatsu) social_post — R0 scaffold.

Drafts a dry-run, member-signed, non-adjudicating divergence post. .solve() raises at R0 (G8):
live publication is Council Lv6+ + operator + member-signature gated. The drafting membrane logic
(G2/G3/G7/G8) lives in state_machine.py and is exercised by the cell tests.
"""
from __future__ import annotations

from typing import Any


class SocialPostCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kosatsu R0 scaffold: social_post drafts dry-run only; live publication is "
            "Council Lv6+ + operator + member-sig gated (G8)."
        )
