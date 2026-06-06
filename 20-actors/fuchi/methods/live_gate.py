"""live_gate.py — 扶持 (fuchi) R1(live): the operator+Council gate that EVERY outward leg refuses by default.

Per ADR-2606052300 R1-live (G10 outward-gated). The R1 a/b/c/d engines (provision / vote / book /
couple) are built and tested **offline**. This module is the single membrane that flips any of them
to *live execution* — and, by construction, it **REFUSES unless every gate condition holds**, exactly
as yadori's live RDAP fetch refuses without `YADORI_ALLOW_LIVE_RDAP=1` + an operator gate.

A live leg is admissible ONLY when all of:

  1. **operator process flag** — the env var `FUCHI_ALLOW_LIVE_<LEG>` == "1" (an operator action on
     the box that runs the leg; absent ⇒ no socket / no chain write / no publish, ever);
  2. **operator attestation** — `gate.operator_did` is a non-empty operator/community DID;
  3. **Council ratification** — `gate.council_level >= min_council` (Lv6 ordinary outward;
     **Lv7 for the displacement coupling**, which is invariant-adjacent to the labor-liberation core);
  4. **member signature (no-server-key)** — `gate.member_signature` is a non-empty member-signed ref.
     The server can never satisfy this (ADR-2605231525); a `:server`/empty signer is refused.

The gate NEVER relaxes the structural invariants. cash≡0 (G2), no-server-key (G9), and the
in-kind-only rails (G3) hold in live mode exactly as offline — `require()` is an *authorization*
membrane, not an invariant override. There is no code path in which it returns a value that lets a
caller move cash or hold a server key.

Stdlib only. Env is read explicitly (the script clock/env is unavailable by design — pass `env=`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# leg → (env flag, minimum Council level). Lv6 = ordinary outward action; Lv7 = invariant-adjacent.
LEG_POLICY: dict[str, tuple[str, int]] = {
    "provision": ("FUCHI_ALLOW_LIVE_PROVISION", 6),
    "vote":      ("FUCHI_ALLOW_LIVE_VOTE", 6),
    "book":      ("FUCHI_ALLOW_LIVE_BOOK", 6),
    "couple":    ("FUCHI_ALLOW_LIVE_COUPLE", 7),  # binds the displacement wave — invariant-adjacent
}


class LiveGateRefused(RuntimeError):
    """Raised when a live leg is attempted without every gate condition satisfied (the default)."""


@dataclass(frozen=True)
class LiveGate:
    """The authorization a live leg must carry. Default-constructed ⇒ refused on every condition."""

    leg: str
    operator_did: str = ""        # operator / community-operator attestation DID
    council_level: int = 0        # ratified Council level for this action
    member_signature: str = ""    # member-signed authorization ref (no-server-key, ADR-2605231525)

    def __post_init__(self) -> None:
        if self.leg not in LEG_POLICY:
            raise ValueError(f"unknown live leg {self.leg!r}; expected one of {tuple(LEG_POLICY)}")


def _is_server_signer(sig: str) -> bool:
    s = (sig or "").strip().lower()
    return (not s) or s.startswith(("server", "did:server", ":server")) or s in ("server", "anon")


def gate_status(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """Report each gate condition WITHOUT raising (for dry-run reporting / analyze.py)."""
    flag, min_council = LEG_POLICY[gate.leg]
    e = os.environ if env is None else env
    conds = {
        "operator_flag": e.get(flag) == "1",
        "operator_attested": bool(gate.operator_did.strip()),
        "council_ratified": gate.council_level >= min_council,
        "member_signed": not _is_server_signer(gate.member_signature),
    }
    return {
        "leg": gate.leg,
        "env_flag": flag,
        "min_council": min_council,
        "conditions": conds,
        "admissible": all(conds.values()),
    }


def require(gate: LiveGate, *, env: dict[str, str] | None = None) -> dict:
    """Authorize a live leg, or RAISE LiveGateRefused naming the first unmet condition.

    Returns the gate_status dict on success. NEVER relaxes cash≡0 / no-server-key / in-kind-only —
    those remain enforced by the engine dataclasses regardless of this authorization.
    """
    st = gate_status(gate, env=env)
    c = st["conditions"]
    flag, min_council = LEG_POLICY[gate.leg]
    if not c["operator_flag"]:
        raise LiveGateRefused(
            f"G10: live '{gate.leg}' refused — operator process flag {flag}=1 is not set"
        )
    if not c["operator_attested"]:
        raise LiveGateRefused(f"G10: live '{gate.leg}' refused — no operator attestation (operator_did)")
    if not c["council_ratified"]:
        raise LiveGateRefused(
            f"G10: live '{gate.leg}' refused — Council Lv{min_council}+ required "
            f"(have Lv{gate.council_level})"
        )
    if not c["member_signed"]:
        raise LiveGateRefused(
            f"G9/no-server-key: live '{gate.leg}' refused — a member signature is required "
            "(the server can never sign; ADR-2605231525)"
        )
    return st
