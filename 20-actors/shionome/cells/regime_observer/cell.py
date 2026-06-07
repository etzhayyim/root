"""LangGraph Pregel wrapper for 潮目 (shionome) regime_observer — R0 scaffold.

Derives the FACTUAL cross-asset regime descriptor (risk-on/off/mixed) from the sign of net
flow into risk vs safe buckets. DESCRIPTIVE, never advice (G2, トレードはしない). Coded core in
methods/weave.regime. .solve() raises at R0 — live derivation is Council Lv6+ gated (G8).
"""
from __future__ import annotations

from typing import Any


class RegimeObserverCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shionome R0 scaffold: regime_observer derives offline; the regime is descriptive, "
            "never advice (G2). Live derivation is Council Lv6+ gated (G8)."
        )
