"""LangGraph Pregel wrapper for 潮目 (shionome) social_post — R0 scaffold.

Projects an aggregate finding into a DRY-RUN, member-signed social post (mirror disclaimer,
no-trade body scan, ≥2 sources). Coded core in methods/social.py. .solve() raises at R0 — live
social posting is Council Lv6+ + operator + member-signature gated (G8); the server never
signs (G7).
"""
from __future__ import annotations

from typing import Any


class SocialPostCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shionome R0 scaffold: social_post drafts dry-run offline; live posting is Council "
            "Lv6+ + operator + member-signature gated (G8); the server never signs (G7)."
        )
