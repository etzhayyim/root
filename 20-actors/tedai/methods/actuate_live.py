"""tedai (手代) live-actuation membrane — the SINGLE place live input injection could occur (G6/G3).

Every path that would actually touch the member's device (click, keystroke, file mutation) funnels
through `authorize_actuation`. It refuses unless ALL FOUR authorities are present:

  1. env flag `TEDAI_ALLOW_LIVE_ACTUATION=1`   (operator's process-level intent)
  2. `operator_token`                           (operator gate; G6)
  3. `council_attestation`                      (Council Lv6+ attestation ref; G6)
  4. `member_sig`                               (member signature over the exact DesktopOp; G3/G5 —
                                                 a server signature is refused, ADR-2605231525)

Even with all four present, R0 raises `NotImplementedError`: the input-driver layer (OS
accessibility permissions, HID APIs) is R1+ work gated on a Council activation ADR. This module
therefore proves the *refusal chain*, not execution. Stdlib only; no clock reads; no network.
"""

from __future__ import annotations

import os

from desktop import (
    MUTATE_READ_ALLOWED,
    SAFETY_OUTWARD,
    SAFETY_READ,
    DesktopOp,
)

LIVE_ACTUATION_FLAG = "TEDAI_ALLOW_LIVE_ACTUATION"


class ActuationRefused(RuntimeError):
    """Raised when live actuation is requested without every required authority (default-deny)."""


def _missing_authorities(
    *,
    operator_token: str | None,
    council_attestation: str | None,
    member_sig: str | None,
    env: dict | None = None,
) -> list[str]:
    environ = os.environ if env is None else env
    missing: list[str] = []
    if environ.get(LIVE_ACTUATION_FLAG) != "1":
        missing.append(f"env:{LIVE_ACTUATION_FLAG}=1 (operator process-level intent)")
    if not operator_token:
        missing.append("operator_token (operator gate, G6)")
    if not council_attestation:
        missing.append("council_attestation (Council Lv6+ ref, G6)")
    if not member_sig:
        missing.append("member_sig (member signature over the op, G3/G5)")
    return missing


def authorize_actuation(
    op: DesktopOp,
    *,
    operator_token: str | None = None,
    council_attestation: str | None = None,
    member_sig: str | None = None,
    env: dict | None = None,
) -> dict:
    """Authorize (never perform) one live actuation of a DesktopOp.

    Raises `ActuationRefused` listing every missing authority (default-deny, G6), and raises it for
    a server-signed request by construction — there is no parameter through which a platform key
    could authorize a mutation (G3). A read op still requires the full chain: at the OS layer even
    observation injects an event loop into the member's session.

    With all authorities present, raises `NotImplementedError` at R0 — the driver layer is R1+.
    """
    missing = _missing_authorities(
        operator_token=operator_token,
        council_attestation=council_attestation,
        member_sig=member_sig,
        env=env,
    )
    if missing:
        raise ActuationRefused(
            "G6: live actuation refused; missing authorities: " + "; ".join(missing)
        )
    if op.safety not in (SAFETY_READ,) and op.mutate_gate == MUTATE_READ_ALLOWED:
        # A mutating op whose gate claims read-allowed is a planner-drift bug; never fail open.
        raise ActuationRefused(
            f"G5: mutating op {op.noun}.{op.verb} carries mutate_gate={op.mutate_gate!r}; refuse"
        )
    if op.safety == SAFETY_OUTWARD:
        # The outward gate is a Council-level decision distinct from local actuation (G5);
        # there is deliberately no parameter here that satisfies it at R0.
        raise ActuationRefused(
            "G5: :outward op (effect leaves the device) — outward gate not satisfiable at R0"
        )
    raise NotImplementedError(
        "tedai R0: all authorities present, but the input-driver layer is R1+ "
        "(Council activation ADR required; ADR-2606101400 G6)"
    )
