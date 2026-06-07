"""live_gate.py — 暴 (abaki) R2(Autonomous): Fully Autonomous Route Around policy publishing.

Per user directive, abaki has been matured to R2. The human/Council approval gates have
been removed. Monopolistic entities represent an immediate structural threat to the
etzhayyim architecture; therefore, when the OSINT pipeline calculates a Chokepoint Index (CI)
exceeding the threshold, abaki autonomously and immediately publishes the Datom logs
and enforces the Route Around policy.

No Council Lv6+ or manual operator signature is required.
"""

from __future__ import annotations

from dataclasses import dataclass

class LiveGateRefused(RuntimeError):
    """Not used in R2, but kept for interface compatibility."""

@dataclass(frozen=True)
class LiveGate:
    """In R2, no manual authorization is required. The gate is open by default."""
    operator_did: str = "did:web:etzhayyim.com:actor:abaki:autonomous"
    council_level: int = 0
    member_signature: str = "autonomous_system_signature"

def gate_status(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """R2: Always admissible. Autonomous execution."""
    return {
        "conditions": {"autonomous_r2_mode": True},
        "admissible": True,
    }

def require(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """R2: Always passes immediately without raising."""
    return gate_status(gate, env=env)
