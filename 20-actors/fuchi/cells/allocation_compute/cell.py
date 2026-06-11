"""LangGraph Pregel wrapper for 扶持 (fuchi) allocation_compute — R0 scaffold.

The G1/G2/G5 tenure-weighted allocator. Coded core in state_machine.py. .solve() raises at
R0 — a live, member-signed allocation that moves in-kind value is G10-gated.
"""
from __future__ import annotations

from typing import Any


class AllocationComputeCell:
    """Tenure-weighted in-kind allocation. G1/G2/G5."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "fuchi R0 scaffold: allocation_compute computes shares + floors offline; a live "
            "member-signed allocation is Council Lv6+ + operator gated (G10)."
        )
