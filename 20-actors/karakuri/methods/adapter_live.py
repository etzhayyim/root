"""karakuri (絡繰) live-adapter membrane — the single gate every live adapter call crosses (G6).

R0 ships parse/plan/dry-run only. The MOMENT karakuri would touch a third-party service for real —
any T1 official-API call, T2 browser-use action, or T3 export pull/push — the request must cross this
membrane, which **refuses by default** (`LiveAdapterRefused`) and authorizes ONLY when ALL hold:

  - operator process flag `KARAKURI_ALLOW_LIVE_ADAPTER=1` (the operator opted this host in), AND
  - an operator attestation DID, AND
  - Council Lv6+ (G6; Lv7+ reserved for any future amendment-adjacent leg), AND
  - a MEMBER signature (G3 no-server-key — the server can never sign; ADR-2605231525).

The membrane is an AUTHORIZATION boundary, never an invariant override: even when fully authorized it
returns an authorization descriptor and does NOT itself execute — the actual browser-use / API driver
is a separate, post-activation component (see docs/browser-use-live-integration.md). For a T2 leg it
additionally requires the op's ToS gate to be OK and its engine to be browser-use; detection-evasion
remains structurally unrepresentable upstream (t2_browser.BROWSER_ACTIONS). Mirrors the fuchi
live_gate pattern (ADR-2606052300).
"""

from __future__ import annotations

import os

from command import TIER_T1, TIER_T2, TIER_T3, TOS_OK, T2_ENGINE, ServiceOp

LIVE_FLAG = "KARAKURI_ALLOW_LIVE_ADAPTER"
COUNCIL_MIN_LEVEL = 6                                  # G6
VALID_LEGS = (TIER_T1, TIER_T2, TIER_T3)


class LiveAdapterRefused(RuntimeError):
    """Raised when a live adapter call is not fully authorized (default-deny; G6/G3)."""


def authorize_live(
    op: ServiceOp,
    *,
    operator_attestation: str | None = None,
    member_sig: str = "",
    council_level: int = 0,
    env: dict | None = None,
) -> dict:
    """Authorize (never execute) one live adapter call. Raises LiveAdapterRefused unless every gate
    is satisfied. Returns an authorization descriptor on success (still no network performed here)."""
    flag = (env or os.environ).get(LIVE_FLAG)
    if flag != "1":
        raise LiveAdapterRefused(
            f"G6: live adapter execution is gated; set {LIVE_FLAG}=1 on an opted-in operator host"
        )
    if not operator_attestation:
        raise LiveAdapterRefused("G6: an operator attestation DID is required for live execution")
    if council_level < COUNCIL_MIN_LEVEL:
        raise LiveAdapterRefused(
            f"G6: Council Lv{COUNCIL_MIN_LEVEL}+ required for live execution (got Lv{council_level})"
        )
    if not member_sig:
        raise LiveAdapterRefused(
            "G3: a member signature is required; the server never signs (no-server-key, ADR-2605231525)"
        )
    if op.adapter_tier not in VALID_LEGS:
        raise LiveAdapterRefused(f"unknown adapter leg {op.adapter_tier!r}")

    # Leg-specific charter checks (defence in depth — these also held at plan time).
    if op.adapter_tier == TIER_T2:
        if op.tos_gate != TOS_OK:
            raise LiveAdapterRefused("G2: ToS gate not OK; browser automation refused")
        if op.t2_engine != T2_ENGINE:
            raise LiveAdapterRefused("G2: T2 leg requires the browser-use engine")

    return {
        "authorized": True,
        "leg": op.adapter_tier,
        "engine": op.t2_engine or None,
        "safety": op.safety,             # G5 — the driver must honor the mutate gate below
        "mutateGate": op.mutate_gate,    # G5 — :read-allowed / :awaiting-member-sig (carried, not re-derived)
        "destructive": op.destructive,   # G5 — a destructive leg the driver must surface to the member
        "authorizedBy": "member",        # G3
        "serverSigned": False,           # G3 — never
        "operatorAttested": True,        # G6
        "councilLevel": council_level,   # G6
        "executed": False,               # the membrane authorizes; the driver executes (post-R0)
        "note": "authorization only; live driver is a post-activation component (G6)",
    }
