"""karakuri (絡繰) T2 browser-use adapter — dry-run action-plan builder (ADR-2606039200).

T2 is the **ToS-permitted headless-browser** tier. Its engine is **browser-use** — a LangGraph-driven
browser agent over Playwright — driving the **member's OWN authenticated session** (G1). This module
turns a T2 ServiceOp into a DECLARATIVE, dry-run browser action plan **without importing browser-use**
and **without touching the network** (G6). Live execution is Council Lv6+ + operator gated.

Why a plan builder instead of a driver: at R0 the actor is design + dry-run only, and the charter
invariants are easiest to enforce *structurally* over a declarative plan:

- **G2 no detection-evasion** — the action vocabulary (`BROWSER_ACTIONS`) simply cannot express
  proxy/IP rotation, captcha-solving-as-evasion, stealth fingerprinting, or rate-limit circumvention.
  Those verbs live in `EVASION_ACTIONS`; constructing a step with one raises `ValueError`. Evasion is
  unrepresentable, the way nusa cannot express `:psychoactive` or tazuna `:weaponizable`.
- **G2 ToS-honest** — a refused ToS gate (or a non-T2 op, or a service whose browser-automation
  stance is not permitted) yields no plan; `build_browser_plan` raises.
- **G1 own-account-only** — the plan opens the member's own session via the encrypted session-grant
  ref (never a credential, G3); there is no field to point at another account.
- **G6 dry-run** — every step is planned, never executed; the `live` flag refuses by construction.

Pairs with `command.py` (the ServiceOp parser/planner) and the `adapter_invoke` cell. Stdlib only.
"""

from __future__ import annotations

from command import (
    SAFETY_READ,
    TIER_T2,
    TOS_OK,
    T2_ENGINE,
    ServiceOp,
)

# The browser-use action vocabulary karakuri will plan (member's own session; ToS-honest).
BROWSER_ACTIONS: frozenset[str] = frozenset({
    "open_session",   # attach the member's OWN authenticated session (encrypted grant ref; G1/G3)
    "goto",           # navigate to an in-account URL
    "wait_for",       # wait for an element/state (human-paced; respects the site, no busy-loop)
    "read_text",      # read visible text the member can already see
    "extract",        # structure read content into a result
    "click",          # click an in-account control
    "fill",           # fill a form field (mutate; gated by member signature, G5)
    "select",         # choose an option
    "submit",         # submit a form (mutate; member-signature required, G5)
    "screenshot",     # capture for the member's own audit trail
})

# Structurally forbidden — detection-evasion / anti-bot circumvention (G2 / N2). Unrepresentable:
# building a step with any of these raises. There is deliberately no flag, knob, or option anywhere
# in karakuri that turns one on.
EVASION_ACTIONS: frozenset[str] = frozenset({
    "solve_captcha",
    "rotate_proxy",
    "set_proxy",
    "spoof_fingerprint",
    "stealth_mode",
    "bypass_ratelimit",
    "randomize_user_agent",
    "evade_detection",
})


class EvasionRefused(ValueError):
    """Raised when a browser step would perform detection-evasion (G2 / N2 — unrepresentable)."""


class T2NotEligible(ValueError):
    """Raised when an op is not a charter-eligible T2 browser-use op (wrong tier / ToS refused)."""


def _make_step(action: str, **fields: object) -> dict:
    """Build one browser-use step, refusing any detection-evasion verb by construction (G2)."""
    if action in EVASION_ACTIONS:
        raise EvasionRefused(
            f"G2/N2: '{action}' is detection-evasion and is unrepresentable in karakuri"
        )
    if action not in BROWSER_ACTIONS:
        raise ValueError(f"unknown browser action {action!r} (not in BROWSER_ACTIONS)")
    return {"action": action, **fields}


def assert_no_evasion(steps: list[dict]) -> None:
    """G2: verify a step list contains no detection-evasion action (defence in depth)."""
    for step in steps:
        if step.get("action") in EVASION_ACTIONS:
            raise EvasionRefused(f"G2/N2: detection-evasion step present: {step.get('action')!r}")


def _steps_for(op: ServiceOp, grant_ref: str) -> list[dict]:
    """Build the dry-run browser-use step skeleton for a ServiceOp (read vs mutate; G5)."""
    steps = [
        # G1/G3: the member's OWN session, via an encrypted grant ref — never a plaintext credential.
        _make_step("open_session", principal="member", account_owner="member",
                   grant_ref=grant_ref, server_held_key=False),
        _make_step("goto", target=f"{op.service}:{op.noun}"),
        _make_step("wait_for", target=op.noun, human_paced=True),
    ]
    if op.safety == SAFETY_READ:
        steps += [
            _make_step("read_text", target=op.noun),
            _make_step("extract", as_result=op.noun),
        ]
    else:
        # Mutating ops: the plan stops at a member-signature checkpoint; nothing submits without it (G5).
        steps += [
            _make_step("fill", target=op.noun, from_args=sorted(op.args.keys())),
            _make_step("submit", target=op.noun, requires="member-signature"),
        ]
    return steps


def build_browser_plan(
    op: ServiceOp,
    grant_ref: str = "encref:com.etzhayyim.encrypted/<service>-session",
    *,
    live: bool = False,
) -> dict:
    """Build a dry-run browser-use action plan for a T2 ServiceOp.

    Refuses (raises) unless the op is a charter-eligible T2 browser-use op:
      - `op.adapter_tier` must be T2 (use the official API for T1 services — Google/Facebook),
      - `op.tos_gate` must be OK (a ToS-prohibited service has no plan; G2),
      - `op.t2_engine` must be browser-use (set by `command.plan` only on a permitted T2 op).
    `live=True` is refused outright — R0 never executes; live exec is Council Lv6+ + operator gated (G6).
    """
    if live:
        raise T2NotEligible(
            "G6: live browser execution is Council Lv6+ + operator gated; R0 is dry-run only"
        )
    if op.adapter_tier != TIER_T2:
        raise T2NotEligible(
            f"not a T2 op (tier={op.adapter_tier!r}); browser-use is the T2 engine only. "
            "T1 services (e.g. Google, Facebook) use their official API, not browser automation."
        )
    if op.tos_gate != TOS_OK:
        raise T2NotEligible(
            f"G2: ToS gate is {op.tos_gate!r}; browser automation refused — no plan"
        )
    if op.t2_engine != T2_ENGINE:
        raise T2NotEligible(
            f"G2: browser-automation stance does not permit T2 for service {op.service!r}"
        )

    steps = _steps_for(op, grant_ref)
    assert_no_evasion(steps)  # G2 defence in depth
    return {
        "engine": T2_ENGINE,                 # browser-use
        "runtime": "langgraph->wasm",        # planned in a LangGraph cell, run in-WASM (Murakumo-only)
        "service": op.service,
        "op": f"{op.noun}.{op.verb}",
        "tier": op.adapter_tier,
        "safety": op.safety,
        "mutate_gate": op.mutate_gate,       # reads run; mutates wait on member signature (G5)
        "dry_run": True,                     # G6 invariant — R0 never executes
        "detection_evasion": False,          # G2 — unrepresentable by construction
        "steps": steps,
        "note": "R0 dry-run; live browser-use execution Council Lv6+ + operator gated (G6)",
    }


if __name__ == "__main__":  # pragma: no cover — tiny offline demo
    import sys

    from command import plan

    line = " ".join(sys.argv[1:]) or "karakuri legacy-portal records.list"
    op = plan(line)
    try:
        plan_out = build_browser_plan(op)
        print(f"engine={plan_out['engine']} service={plan_out['service']} "
              f"op={plan_out['op']} dry_run={plan_out['dry_run']} "
              f"evasion={plan_out['detection_evasion']} steps={len(plan_out['steps'])}")
        for s in plan_out["steps"]:
            print(f"  - {s['action']}")
    except T2NotEligible as e:
        print(f"no browser-use plan: {e}")
