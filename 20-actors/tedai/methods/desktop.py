"""tedai (手代) DesktopOp parser/planner — member-computer operation, stdlib only (ADR-2606101400).

The uniform vocabulary is a normalized **DesktopOp** (the karakuri ServiceOp pattern lifted to the
OS layer): `app` · `noun` · `verb` · classified `safety` (read/create/update/delete/**outward**) +
a `destructive` flag + the selected adapter `tier`. A CLI string

    tedai <app> <noun>.<verb> [--flag value ...]

parses into exactly one DesktopOp. This module does the offline-safe parts purely and
deterministically: command parsing, app resolution against a :representative registry, safety
classification (incl. the OS-layer-specific **:outward** class — a verb whose effect leaves the
device: send/pay/post/upload), adapter-tier selection (T1 scripting/accessibility-API first), the
**stance gate** (the T2 vision-pointer adapter is refused on a synthetic-input-prohibited app — G2;
anti-cheat games and DRM players are the canonical case), the **karakuri route** (browser apps are
karakuri's surface — N7), and the **mutate/outward gates** (G5). It emits a **dry-run plan** and
never injects input or touches the network (G6). The T2 vision action plan is built by
`t2_vision.py`.

G1 own-device · G2 T1-preferred / stance-honest · G5 read-default/mutate-gated + outward-gated ·
G6 actuation-gated · G8 :representative registry (unknown app degrades honestly) · N7 browser →
karakuri.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── :representative app capability + stance registry (mirrors data/app-registry.kotoba.edn; G8).
#    Runtime source of truth is the EDN registry; operator MUST verify a stance before live use.
#    Axes:
#      "t1"     — the app's official automation surface (AppleScript/JXA + AXUIElement, Windows
#                 UI Automation, AT-SPI2/D-Bus, or the app's own CLI). True → T1 is selected.
#      "t2"     — the SYNTHETIC-INPUT stance: "permitted" / "restricted" / "prohibited"; a
#                 "prohibited" stance refuses the T2 vision-pointer adapter by construction (G2),
#                 EVEN where T2 would technically work. Missing → "prohibited" (default-deny
#                 input injection — safest). ("restricted" treated as "permitted" at R0 —
#                 reserved for a future per-app scope limit.)
#      "route"  — surface owned by a sibling actor; "karakuri" routes browser apps to karakuri
#                 by construction (N7 — one owner per surface).
#    Anti-cheat games + DRM players are the canonical :prohibited case (the desktop analogue of
#    karakuri's Google/Facebook api-ok/browser-prohibited case). ──
APP_REGISTRY: dict[str, dict] = {
    # rich official scripting surface → T1
    "finder":      {"t1": True,  "t1_surface": "applescript+ax", "t2": "permitted"},
    "mail":        {"t1": True,  "t1_surface": "applescript+ax", "t2": "permitted"},
    "calendar":    {"t1": True,  "t1_surface": "applescript+ax", "t2": "permitted"},
    "excel":       {"t1": True,  "t1_surface": "applescript+uia", "t2": "permitted"},
    "terminal":    {"t1": True,  "t1_surface": "cli",            "t2": "permitted"},
    "keynote":     {"t1": True,  "t1_surface": "applescript",    "t2": "permitted"},
    # no usable T1 surface + synthetic input permitted → T2 vision-pointer is the sanctioned path
    "legacy-win-app": {"t1": False, "t1_surface": "", "t2": "permitted"},
    "kiosk-tool":     {"t1": False, "t1_surface": "", "t2": "permitted"},
    # synthetic input prohibited (anti-cheat / DRM / terms) → T2 refused by construction; T3 only
    "anticheat-game": {"t1": False, "t1_surface": "", "t2": "prohibited"},
    "drm-player":     {"t1": False, "t1_surface": "", "t2": "prohibited"},
    "banking-app":    {"t1": False, "t1_surface": "", "t2": "prohibited"},
    # browser surfaces belong to karakuri (N7) — tedai refuses to re-implement web automation
    "chrome":  {"t1": False, "t1_surface": "", "t2": "prohibited", "route": "karakuri"},
    "safari":  {"t1": False, "t1_surface": "", "t2": "prohibited", "route": "karakuri"},
    "firefox": {"t1": False, "t1_surface": "", "t2": "prohibited", "route": "karakuri"},
}

# The T2 (vision-pointer / computer-use) engine: an ON-DEVICE vision agent (baien edge,
# ADR-2605241900) or LAN Murakumo (G4). A screenshot never leaves the device — cloud computer-use
# APIs are structurally unrepresentable. See methods/t2_vision.py for the dry-run plan builder.
T2_ENGINE = "on-device-vision"

# Safety classification (G5). The verb determines whether an op reads, mutates, or leaves the device.
SAFETY_READ = "read"
SAFETY_CREATE = "create"
SAFETY_UPDATE = "update"
SAFETY_DELETE = "delete"
SAFETY_OUTWARD = "outward"   # OS-layer-specific: effect leaves the device (send/pay/post/upload)

VERB_SAFETY: dict[str, str] = {
    "list": SAFETY_READ, "get": SAFETY_READ, "read": SAFETY_READ, "find": SAFETY_READ,
    "search": SAFETY_READ, "show": SAFETY_READ, "export": SAFETY_READ,
    "create": SAFETY_CREATE, "add": SAFETY_CREATE, "new": SAFETY_CREATE, "save": SAFETY_CREATE,
    "update": SAFETY_UPDATE, "set": SAFETY_UPDATE, "edit": SAFETY_UPDATE,
    "move": SAFETY_UPDATE, "rename": SAFETY_UPDATE, "fill": SAFETY_UPDATE,
    "delete": SAFETY_DELETE, "remove": SAFETY_DELETE, "trash": SAFETY_DELETE,
    "empty": SAFETY_DELETE,
    "send": SAFETY_OUTWARD, "post": SAFETY_OUTWARD, "pay": SAFETY_OUTWARD,
    "purchase": SAFETY_OUTWARD, "share": SAFETY_OUTWARD, "upload": SAFETY_OUTWARD,
    "publish": SAFETY_OUTWARD,
}

# Adapter tiers (G2; safest-first).
TIER_T1 = "t1-scripting-api"
TIER_T2 = "t2-vision-pointer"
TIER_T3 = "t3-file-level"

# Stance gate outcomes (G2).
STANCE_OK = "ok"
STANCE_REFUSED = "refused-synthetic-input-prohibited"

# Mutate gate outcomes (G5). Outward ops carry the extra outward gate.
MUTATE_READ_ALLOWED = "read-allowed"
MUTATE_AWAIT_SIG = "awaiting-member-sig"
MUTATE_AWAIT_SIG_OUTWARD = "awaiting-member-sig-and-outward-gate"

# Honest degradations / routes (G8 / N7).
UNKNOWN_APP = "unknown-app"
ROUTE_KARAKURI = "route-to-karakuri"


@dataclass
class DesktopOp:
    app: str
    noun: str
    verb: str
    safety: str
    destructive: bool
    adapter_tier: str
    args: dict = field(default_factory=dict)
    app_known: bool = True
    dry_run: bool = True              # G6 invariant — R0 never actuates
    stance_gate: str = STANCE_OK
    mutate_gate: str = MUTATE_READ_ALLOWED
    t2_engine: str = ""              # on-device-vision, only on a permitted T2 op (G2/G4)
    route: str = ""                  # "karakuri" when the surface belongs to karakuri (N7)
    note: str = ""


def classify_safety(verb: str) -> str:
    """Map a verb to its op safety. Unknown verbs are treated conservatively as :update (mutating)."""
    return VERB_SAFETY.get((verb or "").strip().lower(), SAFETY_UPDATE)


def is_destructive(safety: str) -> bool:
    """G5: delete is the irreversible class; flagged for explicit member confirmation."""
    return safety == SAFETY_DELETE


def resolve_app(app_id: str) -> dict | None:
    """Look the app up in the :representative registry. None → honest :unknown-app (G8)."""
    return APP_REGISTRY.get((app_id or "").strip().lower())


def t2_stance(rec: dict) -> str:
    """The synthetic-input stance for an app. Missing → 'prohibited' (default-deny; G2)."""
    return rec.get("t2", "prohibited")


def select_tier(rec: dict) -> str:
    """Safest-first (G2): scripting/accessibility API > permitted vision-pointer > file-level."""
    if rec.get("t1"):
        return TIER_T1
    if t2_stance(rec) in ("permitted", "restricted"):
        return TIER_T2
    return TIER_T3


def stance_gate(rec: dict, tier: str) -> str:
    """G2: a T2 vision-pointer op on an app whose synthetic-input stance is 'prohibited' is
    refused by construction — anti-cheat games, DRM players, banking apps."""
    if tier == TIER_T2 and t2_stance(rec) == "prohibited":
        return STANCE_REFUSED
    return STANCE_OK


def t2_engine(rec: dict, tier: str, gate: str) -> str:
    """The on-device vision engine for a permitted T2 op; '' otherwise (G2/G4)."""
    if tier == TIER_T2 and gate == STANCE_OK and t2_stance(rec) in ("permitted", "restricted"):
        return T2_ENGINE
    return ""


def mutate_gate(safety: str) -> str:
    """G5: reads allowed at R0; mutations await member-sig; outward ops add the outward gate."""
    if safety == SAFETY_READ:
        return MUTATE_READ_ALLOWED
    if safety == SAFETY_OUTWARD:
        return MUTATE_AWAIT_SIG_OUTWARD
    return MUTATE_AWAIT_SIG


def parse_command(line: str) -> tuple[str, str, str, dict]:
    """Parse `[tedai] <app> <noun>.<verb> [--flag value ...]` → (app, noun, verb, args).

    Raises ValueError on a malformed command (G8 — never guesses the shape).
    """
    tokens = (line or "").strip().split()
    if tokens and tokens[0].lower() == "tedai":
        tokens = tokens[1:]
    if len(tokens) < 2:
        raise ValueError(f"malformed command (need '<app> <noun>.<verb>'): {line!r}")
    app = tokens[0].lower()
    nv = tokens[1]
    if "." not in nv:
        raise ValueError(f"malformed op (need '<noun>.<verb>'): {nv!r}")
    noun, verb = nv.split(".", 1)
    if not noun or not verb:
        raise ValueError(f"malformed op (empty noun or verb): {nv!r}")

    args: dict = {}
    rest = tokens[2:]
    j = 0
    while j < len(rest):
        tok = rest[j]
        if tok.startswith("--"):
            key = tok[2:]
            if j + 1 < len(rest) and not rest[j + 1].startswith("--"):
                args[key] = rest[j + 1]
                j += 2
            else:
                args[key] = True
                j += 1
        else:
            j += 1
    return app, noun.lower(), verb.lower(), args


def plan(line: str, prefer_tier: str | None = None) -> DesktopOp:
    """Parse a command into a dry-run DesktopOp plan with all gates applied (no input injection).

    `prefer_tier` lets a caller request a specific adapter (e.g. force T2) so the G2 stance gate
    can be demonstrated; by default the safest tier is selected.
    """
    if prefer_tier is not None and prefer_tier not in (TIER_T1, TIER_T2, TIER_T3):
        raise ValueError(f"unknown prefer_tier {prefer_tier!r} (expected one of T1/T2/T3 constants)")

    app, noun, verb, args = parse_command(line)
    safety = classify_safety(verb)
    rec = resolve_app(app)

    if rec is None:
        # G8: unknown app degrades honestly — no tier, no guess.
        return DesktopOp(
            app=app, noun=noun, verb=verb, safety=safety,
            destructive=is_destructive(safety), adapter_tier="",
            args=args, app_known=False, stance_gate=STANCE_OK,
            mutate_gate=mutate_gate(safety), note=UNKNOWN_APP,
        )

    if rec.get("route") == "karakuri":
        # N7: the browser surface belongs to karakuri — tedai refuses to re-implement it.
        return DesktopOp(
            app=app, noun=noun, verb=verb, safety=safety,
            destructive=is_destructive(safety), adapter_tier="",
            args=args, app_known=True, route="karakuri", note=ROUTE_KARAKURI,
        )

    tier = prefer_tier or select_tier(rec)
    gate = stance_gate(rec, tier)
    engine = t2_engine(rec, tier, gate)
    note = ""
    if gate == STANCE_REFUSED:
        note = ("G2: synthetic input prohibited on this app; T2 vision-pointer refused — "
                "use the scripting API (T1) or T3 file-level")

    return DesktopOp(
        app=app, noun=noun, verb=verb, safety=safety,
        destructive=is_destructive(safety), adapter_tier=tier,
        args=args, app_known=True, dry_run=True,
        stance_gate=gate, mutate_gate=mutate_gate(safety), t2_engine=engine, note=note,
    )


if __name__ == "__main__":  # pragma: no cover — tiny offline demo
    import sys

    line = " ".join(sys.argv[1:]) or "tedai finder files.list"
    op = plan(line)
    print(f"app={op.app} known={op.app_known} {op.noun}.{op.verb} "
          f"safety={op.safety} destructive={op.destructive} tier={op.adapter_tier} "
          f"stance={op.stance_gate} mutate={op.mutate_gate} dry_run={op.dry_run}"
          + (f"  engine={op.t2_engine}" if op.t2_engine else "")
          + (f"  route={op.route}" if op.route else "")
          + (f"  note={op.note}" if op.note else ""))
