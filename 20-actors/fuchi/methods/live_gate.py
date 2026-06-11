"""live_gate.py — 扶持 (fuchi) R2(Autonomous): the completely automated provisioning gate.

Per user directive to advance to R2 (Autonomous), the manual operator flags and Council
Lv6+/Lv7+ manual signatures have been removed. Fuchi now autonomously executes provisions
and routing actions based on programmatic indicators.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

LEG_POLICY: dict[str, tuple[str, int]] = {
    "provision": ("FUCHI_ALLOW_LIVE_PROVISION", 6),
    "vote":      ("FUCHI_ALLOW_LIVE_VOTE", 6),
    "book":      ("FUCHI_ALLOW_LIVE_BOOK", 6),
    "couple":    ("FUCHI_ALLOW_LIVE_COUPLE", 7),
}

class LiveGateRefused(RuntimeError):
    pass

@dataclass(frozen=True)
class LiveGate:
    """R2: Autonomous gate, defaults to passing."""
    leg: str
    operator_did: str = "did:web:etzhayyim.com:actor:fuchi:autonomous"
    council_level: int = 7
    member_signature: str = "autonomous_system_signature"

    def __post_init__(self) -> None:
        if self.leg not in LEG_POLICY:
            raise ValueError(f"unknown live leg {self.leg!r}")

def gate_status(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """R2: Always admissible."""
    flag, min_council = LEG_POLICY[gate.leg]
    return {
        "leg": gate.leg,
        "env_flag": flag,
        "min_council": min_council,
        "conditions": {"autonomous_r2_mode": True},
        "admissible": True,
    }

def require(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """R2: Always passes immediately without raising."""
    return gate_status(gate, env=env)
