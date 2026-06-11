"""safety — cross-cutting structural gates for infra-robotics (stdlib only).

Generalises the gates already proven in 20-actors/noroshi (civilian-only laser
gate + no-server-key job commit) and 20-actors/kuni-umi/py/agent.py (witness
quorum >=2) so every infra domain (electric / water / gas / telecom) shares one
audited implementation.

These are *structural* gates: a forbidden intent raises before any motion is
planned, never returns a value the caller could ignore. They are the software
embodiment of the constitutional invariants — not a substitute for the certified
IEC 61508/61511 parallel safety PLC that owns the hard-RT stop (that lives in
open-ot field-tier firmware, not here).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Constitutional witness quorum (G8, ADR-2605201400). Mirrors kuni-umi/py/agent.py.
MIN_WITNESS_SIGS = 2

# N1 (Mission Charter §1.12): weaponisation / covert force can never be energised.
# A permitted-use allowlist is safer than a forbidden-use denylist — an intent that
# is neither permitted nor forbidden is rejected (closed-world). Each domain passes
# its own civilian allowlist; these are the cross-domain forbidden anchors.
FORBIDDEN_USES = (
    "weapon",
    "directed-energy",
    "munition",
    "fire-control",
    "interdiction",
    "covert-force",
    "surveillance-targeting",
)


class SafetyError(Exception):
    """Raised when a structural safety / charter gate refuses an operation."""


def assert_civilian(use: str, permitted: tuple[str, ...]) -> None:
    """Closed-world civilian-use gate (N1). Raise unless `use` is explicitly permitted.

    `permitted` is the domain's civilian allowlist (e.g. for hikari:
    ("install", "service", "inspect", "drill", "grid-control")). Anything in the
    cross-domain forbidden anchors is rejected even if a caller mistakenly lists it.
    """
    if use in FORBIDDEN_USES:
        raise SafetyError(
            f"N1: use {use!r} is a forbidden-force use and can never be energised "
            "(Mission Charter §1.12 constitutional invariant)"
        )
    if use not in permitted:
        raise SafetyError(
            f"N1: use {use!r} is not in the civilian allowlist {permitted!r}; "
            "closed-world refusal (only explicitly-permitted civilian uses run)"
        )


def require_member_signature(member_sig: str, server_sig: str = "") -> None:
    """No-server-key gate (G15 / G7, ADR-2605231525). Raise unless a member/operator
    signs and the platform holds no key.

    A non-empty `server_sig` is a structural violation: the platform must never sign
    an actuation. An empty `member_sig` means nobody authorised the action.
    """
    if server_sig:
        raise SafetyError(
            "G15/G7 violation: a server/platform signature was supplied; the platform "
            "holds no key and never signs actuation (ADR-2605231525)"
        )
    if not member_sig:
        raise SafetyError(
            "G15/G7 violation: a member/operator signature is required to authorise "
            "any actuation (no-server-key)"
        )


def witness_quorum_ok(witness_sigs: list[str]) -> dict:
    """Witness quorum >=2 independent robot DIDs (G8); N<2 or duplicates rejected.

    Returns a dict (does not raise) so callers can attach the Council-escalation
    flag to a Datom — identical contract to kuni-umi/py/agent.py.witness_quorum_ok.
    """
    if len(witness_sigs) < MIN_WITNESS_SIGS:
        return {
            "ok": False,
            "reason": f"witness quorum {len(witness_sigs)} < {MIN_WITNESS_SIGS} (G8 constitutional)",
            "escalate_council_lv6": True,
        }
    if len(set(witness_sigs)) < MIN_WITNESS_SIGS:
        return {
            "ok": False,
            "reason": "duplicate witness DIDs detected (G8)",
            "escalate_council_lv6": True,
        }
    return {"ok": True, "reason": "witness quorum satisfied"}


@dataclass(frozen=True)
class SafetyEnvelope:
    """A motion safety envelope for an install/service robot.

    Limits are checked against a planned joint trajectory BEFORE any dispatch.
    `max_joint_speed` is the per-step joint-rate ceiling; `human_proximity_speed`
    is the (lower) ceiling that must hold whenever a person may be inside the
    work cell — the cell stays gated to the slower limit until a Council Lv7+
    near-human attestation lifts it (kuni-umi CLAUDE.md, ADR-2605201400 §7).
    """

    max_joint_speed: float = 1.0          # rad/step ceiling, far from humans
    human_proximity_speed: float = 0.25   # rad/step ceiling, person may be present
    max_reach: float = field(default=float("inf"))  # Cartesian reach ceiling (m)

    def check_trajectory(
        self,
        trajectory: list[tuple[float, ...]],
        dt: float,
        human_present: bool = False,
    ) -> dict:
        """Validate a joint-space trajectory. Returns {ok, violations:[...]}.

        Each element of `trajectory` is a joint-configuration tuple. The per-step
        joint rate is |Δq|/dt; it must stay under the applicable ceiling.
        """
        ceiling = self.human_proximity_speed if human_present else self.max_joint_speed
        violations: list[str] = []
        for i in range(1, len(trajectory)):
            prev, cur = trajectory[i - 1], trajectory[i]
            if len(prev) != len(cur):
                violations.append(f"step {i}: joint-count mismatch")
                continue
            for j, (a, b) in enumerate(zip(prev, cur)):
                rate = abs(b - a) / dt if dt > 0 else float("inf")
                if rate > ceiling + 1e-9:
                    violations.append(
                        f"step {i} joint {j}: rate {rate:.4f} > ceiling {ceiling:.4f}"
                        f"{' (human present)' if human_present else ''}"
                    )
        return {"ok": not violations, "violations": violations}
