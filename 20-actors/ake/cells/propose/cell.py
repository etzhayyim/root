"""LangGraph Pregel wrapper for 朱 (ake) propose — R0 scaffold.

The G1/G3/G4 intake membrane: screens a member-signed correction, then records it as an
append-only :edit/* datom. Coded core in state_machine.py. .solve() raises at R0 — live
proposal recording into the canonical Datom log is Council Lv6+ + operator gated (G8).
"""
from __future__ import annotations

from typing import Any


class ProposeCell:
    """Member-signed correction intake. G1/G3/G4."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "ake R0 scaffold: propose screens + records offline; live recording into the "
            "canonical Datom log is Council Lv6+ + operator gated (G8)."
        )
