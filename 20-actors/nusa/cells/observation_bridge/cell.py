"""LangGraph Pregel wrapper for the nusa observation_bridge (幣) cell — R0 scaffold.

G3: routes legal/legislative questions to danjo/chigiri/moushibumi; never adjudicates.
"""

from __future__ import annotations

from typing import Any

# G3: where each off-actor concern is routed. nusa holds none of these itself.
ROUTES = {
    "legislative-trace": "danjo (ADR-2605301600) — non-adjudicating fact trace",
    "legal-characterization": "chigiri (ADR-2605262700) — UPL boundary, licensed counsel",
    "public-comment": "moushibumi (ADR-2605312400) — neutral 意見公募 / 請願 support",
    "cannabis-derived-medicine": "yakushi (ADR-2605250500) — 薬機法/医師法 boundary (G10)",
}


class ObservationBridgeCell:
    """Router to danjo/chigiri/moushibumi/yakushi. G3 non-adjudicating; no advocacy."""

    def route(self, concern: str) -> str:
        if concern not in ROUTES:
            raise ValueError(f"unknown concern {concern!r}; nusa routes only {sorted(ROUTES)}")
        return ROUTES[concern]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "nusa R0 scaffold: activate observation_bridge via Council ADR (post-2606039800 ratification)"
        )
