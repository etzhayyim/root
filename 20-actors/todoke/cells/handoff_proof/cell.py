"""LangGraph Pregel wrapper for the todoke handoff_proof (受渡証) cell.

R0 scaffold: .solve() raises until Council activation (ADR-2606042300 §Design).
"""

from __future__ import annotations

from typing import Any

from .state_machine import (
    transition_to_arrived,
    transition_to_consent_verified,
    transition_to_proof_captured,
    transition_to_proof_sealed,
)


class HandoffProofCell:
    """On-device proof-of-delivery (no cloud/biometric). G8/G12/G13."""

    def __init__(self) -> None:
        self._steps = [
            transition_to_arrived,
            transition_to_consent_verified,
            transition_to_proof_captured,
            transition_to_proof_sealed,
        ]

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "todoke R0 scaffold: activate handoff_proof via Council ADR (post-2606042300 ratification)"
        )
