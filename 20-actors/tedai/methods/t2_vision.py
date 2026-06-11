"""tedai (手代) T2 vision-pointer adapter — dry-run computer-use plan builder (ADR-2606101400).

T2 is the **stance-permitted vision-pointer** tier — the computer-use shape: screenshot → locate →
click/type on the **member's OWN paired device** (G1). Its engine is **on-device vision** (baien
edge, ADR-2605241900, or LAN Murakumo — G4): a screenshot NEVER leaves the device; cloud
computer-use APIs are structurally unrepresentable here. This module turns a T2 DesktopOp into a
DECLARATIVE, dry-run action plan **without any input driver** and **without touching the screen**
(G6). Live actuation is Council Lv6+ + operator gated.

Why a plan builder instead of a driver: at R0 the actor is design + dry-run only, and the charter
invariants are easiest to enforce *structurally* over a declarative plan:

- **G8 no-surveillance** — the action vocabulary (`VISION_ACTIONS`) simply cannot express ambient
  watching, keylogging, camera/microphone capture, presence monitoring, or observing another
  person. Those verbs live in `SURVEILLANCE_ACTIONS`; constructing a step with one raises.
  Surveillance is unrepresentable, the way karakuri's T2 cannot express proxy rotation.
- **G2 no detection-evasion** — anti-cheat bypass, DRM circumvention, input-spoofing-to-defeat-
  bot-detection, and driver-level input forgery live in `EVASION_ACTIONS`; same refusal.
- **G4 on-device vision** — `exfiltrate_screen` / `upload_frame` are surveillance verbs; the only
  evidence action is `evidence_hash` (a sha256 of the frame — G9; the raw frame stays on-device
  under the member's key).
- **G1/G3 own-device-only** — every plan opens with the member's own pairing grant (an encrypted
  ref, never a credential); there is no field to point at another device.
- **G6 dry-run** — every step is planned, never executed; the `live` flag refuses by construction.

Pairs with `desktop.py` (the DesktopOp parser/planner) and the `actuate_invoke` cell. Stdlib only.
"""

from __future__ import annotations

from desktop import (
    SAFETY_READ,
    STANCE_OK,
    T2_ENGINE,
    TIER_T2,
    DesktopOp,
)

# The vision-pointer action vocabulary tedai will plan (member's own device; op-scoped observation).
VISION_ACTIONS: frozenset[str] = frozenset({
    "attach_pairing",   # attach the member's OWN paired device (encrypted pairing-grant ref; G1/G3)
    "observe_screen",   # one op-scoped frame of the member's own session (G8: never ambient)
    "locate",           # find a UI element in the observed frame (on-device vision; G4)
    "wait_for",         # wait for an element/state (human-paced)
    "read_text",        # read visible text the member can already see
    "extract",          # structure read content into a result
    "click",            # click a located control (mutate; gated by member signature, G5)
    "type_text",        # type into a located field (mutate; member-signature required, G5)
    "press_key",        # press a key/chord (mutate; gated)
    "scroll",           # scroll a located surface
    "evidence_hash",    # sha256 the frame for the member's audit trail (G9 — never the raw frame)
})

# Structurally forbidden — surveillance (G8 / N1 / N4). Unrepresentable: building a step with any
# of these raises. There is deliberately no flag, knob, or option anywhere in tedai that turns one on.
SURVEILLANCE_ACTIONS: frozenset[str] = frozenset({
    "watch_user",
    "monitor_idle",
    "track_presence",
    "keylog",
    "capture_camera",
    "capture_microphone",
    "record_other_person",
    "exfiltrate_screen",
    "upload_frame",
})

# Structurally forbidden — detection-evasion / input forgery (G2 / N2). Same refusal.
EVASION_ACTIONS: frozenset[str] = frozenset({
    "bypass_anticheat",
    "bypass_drm",
    "evade_bot_detection",
    "spoof_input_driver",
    "forge_hid_device",
    "randomize_input_timing",
})

_FORBIDDEN: frozenset[str] = SURVEILLANCE_ACTIONS | EVASION_ACTIONS


class SurveillanceRefused(ValueError):
    """Raised when a vision step would perform surveillance (G8 / N1 — unrepresentable)."""


class EvasionRefused(ValueError):
    """Raised when a vision step would perform detection-evasion (G2 / N2 — unrepresentable)."""


class T2NotEligible(ValueError):
    """Raised when an op is not a charter-eligible T2 vision-pointer op (wrong tier / stance refused)."""


def _make_step(action: str, **fields: object) -> dict:
    """Build one vision step, refusing surveillance and evasion verbs by construction (G8/G2)."""
    if action in SURVEILLANCE_ACTIONS:
        raise SurveillanceRefused(
            f"G8/N1: '{action}' is surveillance and is unrepresentable in tedai"
        )
    if action in EVASION_ACTIONS:
        raise EvasionRefused(
            f"G2/N2: '{action}' is detection-evasion and is unrepresentable in tedai"
        )
    if action not in VISION_ACTIONS:
        raise ValueError(f"unknown vision action {action!r} (not in VISION_ACTIONS)")
    return {"action": action, **fields}


def assert_no_forbidden(steps: list[dict]) -> None:
    """G8/G2: verify a step list contains no surveillance or evasion action (defence in depth)."""
    for step in steps:
        action = step.get("action")
        if action in SURVEILLANCE_ACTIONS:
            raise SurveillanceRefused(f"G8/N1: surveillance step present: {action!r}")
        if action in EVASION_ACTIONS:
            raise EvasionRefused(f"G2/N2: detection-evasion step present: {action!r}")


def _steps_for(op: DesktopOp, grant_ref: str) -> list[dict]:
    """Build the dry-run vision-pointer step skeleton for a DesktopOp (read vs mutate; G5)."""
    steps = [
        # G1/G3: the member's OWN paired device, via an encrypted grant ref — never a credential.
        _make_step("attach_pairing", principal="member", device_owner="member",
                   grant_ref=grant_ref, server_held_key=False),
        # G8: one op-scoped frame of the member's own session; never ambient, never retained raw.
        _make_step("observe_screen", scope="op", session_owner="member", retain_raw=False),
        _make_step("locate", target=op.noun, engine=T2_ENGINE),
        _make_step("wait_for", target=op.noun, human_paced=True),
    ]
    if op.safety == SAFETY_READ:
        steps += [
            _make_step("read_text", target=op.noun),
            _make_step("extract", as_result=op.noun),
        ]
    else:
        # Mutating ops: the plan stops at a member-signature checkpoint; nothing clicks without it (G5).
        steps += [
            _make_step("click", target=op.noun, requires="member-signature"),
            _make_step("type_text", target=op.noun, from_args=sorted(op.args.keys()),
                       requires="member-signature"),
        ]
    # G9: evidence is a hash of the frame, never the frame.
    steps.append(_make_step("evidence_hash", algo="sha256", raw_frame_retained=False))
    return steps


def build_vision_plan(
    op: DesktopOp,
    grant_ref: str = "encref:com.etzhayyim.encrypted/<device>-pairing",
    *,
    live: bool = False,
) -> dict:
    """Build a dry-run vision-pointer action plan for a T2 DesktopOp.

    Refuses (raises) unless the op is a charter-eligible T2 vision-pointer op:
      - `op.adapter_tier` must be T2 (use the scripting API for T1 apps),
      - `op.stance_gate` must be OK (a synthetic-input-prohibited app has no plan; G2),
      - `op.t2_engine` must be on-device-vision (set by `desktop.plan` only on a permitted T2 op).
    `live=True` is refused outright — R0 never actuates; live input injection is Council Lv6+ +
    operator gated (G6).
    """
    if live:
        raise T2NotEligible(
            "G6: live input injection is Council Lv6+ + operator gated; R0 is dry-run only"
        )
    if op.adapter_tier != TIER_T2:
        raise T2NotEligible(
            f"not a T2 op (tier={op.adapter_tier!r}); vision-pointer is the T2 engine only. "
            "Apps with a scripting/accessibility surface use T1, not pixels."
        )
    if op.stance_gate != STANCE_OK:
        raise T2NotEligible(
            f"G2: stance gate is {op.stance_gate!r}; synthetic input refused — no plan"
        )
    if op.t2_engine != T2_ENGINE:
        raise T2NotEligible(
            f"G2: synthetic-input stance does not permit T2 for app {op.app!r}"
        )

    steps = _steps_for(op, grant_ref)
    assert_no_forbidden(steps)  # G8/G2 defence in depth
    return {
        "engine": T2_ENGINE,                 # on-device vision (baien edge / LAN Murakumo; G4)
        "runtime": "langgraph->wasm",        # planned in a LangGraph cell, run in-WASM (Murakumo-only)
        "app": op.app,
        "op": f"{op.noun}.{op.verb}",
        "tier": op.adapter_tier,
        "safety": op.safety,
        "mutate_gate": op.mutate_gate,       # reads run; mutates wait on member signature (G5)
        "dry_run": True,                     # G6 invariant — R0 never actuates
        "surveillance": False,               # G8 — unrepresentable by construction
        "detection_evasion": False,          # G2 — unrepresentable by construction
        "frame_leaves_device": False,        # G4/G9 — evidence is a hash, raw frame stays on-device
        "steps": steps,
        "note": "R0 dry-run; live input injection Council Lv6+ + operator gated (G6)",
    }


if __name__ == "__main__":  # pragma: no cover — tiny offline demo
    import sys

    from desktop import plan

    line = " ".join(sys.argv[1:]) or "tedai legacy-win-app records.list"
    op = plan(line)
    try:
        plan_out = build_vision_plan(op)
        print(f"engine={plan_out['engine']} app={plan_out['app']} "
              f"op={plan_out['op']} dry_run={plan_out['dry_run']} "
              f"surveillance={plan_out['surveillance']} steps={len(plan_out['steps'])}")
        for s in plan_out["steps"]:
            print(f"  - {s['action']}")
    except T2NotEligible as e:
        print(f"no vision-pointer plan: {e}")
