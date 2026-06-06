"""LangGraph Pregel wrapper for 扶持 (fuchi) covenant_intake — R0 scaffold.

The G4/G5/G9 eligibility membrane: screens a 信者 maintainer's covenant, then records it as a
:maintainer/* record. Coded core in state_machine.py. .solve() raises at R0 — live covenant
recording into the canonical Datom log is Council Lv6+ + operator gated (G10).
"""
from __future__ import annotations

from typing import Any


class CovenantIntakeCell:
    """信者-covenant eligibility intake. G4/G5/G9."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "fuchi R0 scaffold: covenant_intake screens + records offline; live recording "
            "into the canonical Datom log is Council Lv6+ + operator gated (G10)."
        )
