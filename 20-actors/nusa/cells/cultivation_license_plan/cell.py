"""LangGraph Pregel wrapper for the nusa cultivation_license_plan (幣) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606039800 §Decision).
The G1/G4/G5/G8 transitions live in state_machine.py and are unit-tested at R0.
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_authorized,
    transition_to_plan_built,
    transition_to_screened,
)


class CultivationLicensePlanCell:
    """Member-principal, server-keyless, outward-gated low-THC 栽培者免許 design. G1/G4/G5/G8."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_screened,
            transition_to_plan_built,
            transition_to_authorized,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "nusa R0 scaffold: activate cultivation_license_plan via Council ADR "
            "(post-2606039800 ratification; live filing also G8 operator-gated)"
        )
