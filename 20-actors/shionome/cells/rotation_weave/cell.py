"""LangGraph Pregel wrapper for 潮目 (shionome) rotation_weave — R0 scaffold.

Computes the aggregate edge-primary metrics (net flow, rotation pairs, inflow HHI, by-asset-
class/region) on read from the flow edges. Coded core in methods/weave.py. .solve() raises at
R0 — live aggregation over the live read-path is Council Lv6+ gated (G8).
"""
from __future__ import annotations

from typing import Any


class RotationWeaveCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shionome R0 scaffold: rotation_weave aggregates offline; live aggregation is "
            "Council Lv6+ gated (G8)."
        )
