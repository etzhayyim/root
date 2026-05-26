"""SelfAssessmentCell — manabi.cert_prep R0 scaffold per ADR-2605264400.

Self-paced demonstration cell. G10 STRUCTURAL: timer is opt-in only;
default sessions are untimed. No proctoring. No ID-verification gating.
No high-stakes scoring.

Outputs domainMasteryAttestation when the adherent self-elects to record
a demonstration. credentialClaimedAttested const false (G7 + N13).
"""

from __future__ import annotations

from typing import Any


class SelfAssessmentCell:
    """Self-paced demonstration cell."""

    def __init__(self) -> None:
        pass

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "manabi.cert_prep R0 scaffold: self_assessment cell not activated. "
            "Requires ADR-2605264400 Council ratify + practice_question cell "
            "active (R1) + domainMasteryAttestation lexicon production-deployed."
        )
