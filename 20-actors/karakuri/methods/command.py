"""karakuri (絡繰) ServiceOp parser/planner — web-service-to-CLI, stdlib only (ADR-2606039200).

The uniform vocabulary is a normalized **ServiceOp**: `service` · `noun` · `verb` · classified
`safety` (read/create/update/delete) + a `destructive` flag + the selected adapter `tier`. A CLI
string

    karakuri <service> <noun>.<verb> [--flag value ...]

parses into exactly one ServiceOp. This module does the offline-safe parts purely and
deterministically: command parsing, service resolution against a :representative registry, safety
classification, adapter-tier selection (official-API-first), the **ToS gate** (the T2 browser-use
adapter is refused on a browser-automation-prohibited service — G2; Google + Facebook route to their
official API and refuse browser automation), the **browser-use engine** selection for a permitted T2
op, and the **mutate gate** (mutating ops require member authorization — G5). It emits a **dry-run
plan** and never touches the network (G6). The T2 browser action plan is built by `t2_browser.py`.

G1 own-account · G2 official-API-first / ToS-honest · G5 read-default/mutate-gated · G6 outward-gated
· G8 :representative registry (bounded subset; unknown service/op degrades honestly).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── :representative service capability + ToS registry (mirrors data/service-registry.kotoba.edn; G8).
#    Runtime source of truth is the EDN registry; operator MUST verify a ToS stance before live use.
#    TWO independent stance axes (a service can sanction its API yet forbid browser automation):
#      "tos" — the OFFICIAL-API stance (governs T1 selection).
#      "t2"  — the BROWSER-AUTOMATION stance: "permitted" / "restricted" / "prohibited"; a
#              "prohibited" t2 stance refuses the T2 browser-use adapter by construction (G2),
#              EVEN when an official API exists. A missing "t2" defaults to "prohibited"
#              (default-deny browser automation — safest).
#    Google + Facebook are the canonical api-ok / t2-prohibited case: drive their official API
#    on the member's OWN account (T1), never browser-automate the consumer surface (T2 refused). ──
SERVICE_REGISTRY: dict[str, dict] = {
    "squarespace": {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "wix":         {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "notion":      {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "shopify":     {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "stripe":      {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "github":      {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "airtable":    {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "wordpress":   {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    # api-ok yet browser-automation-prohibited → default path is the official API (T1); T2 refused.
    "google":      {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    "facebook":    {"official_api": True,  "tos": "api-ok", "t2": "prohibited"},
    # no usable official API + ToS permits automation → T2 browser-use is the sanctioned path.
    "legacy-portal": {"official_api": False, "tos": "automation-allowed", "t2": "permitted"},
    "noauto-saas":   {"official_api": False, "tos": "automation-prohibited", "t2": "prohibited"},
}

# The T2 (headless-browser) engine: browser-use, a LangGraph-driven browser agent over Playwright.
# It is selected ONLY for a T2 op whose service t2 stance permits automation (G2). Live execution is
# Council Lv6+ + operator gated (G6); see methods/t2_browser.py for the dry-run action-plan builder.
T2_ENGINE = "browser-use"

# Safety classification (G5). The verb determines whether an op reads or mutates.
SAFETY_READ = "read"
SAFETY_CREATE = "create"
SAFETY_UPDATE = "update"
SAFETY_DELETE = "delete"

VERB_SAFETY: dict[str, str] = {
    "list": SAFETY_READ, "get": SAFETY_READ, "search": SAFETY_READ,
    "query": SAFETY_READ, "show": SAFETY_READ, "export": SAFETY_READ,
    "create": SAFETY_CREATE, "add": SAFETY_CREATE, "new": SAFETY_CREATE,
    "update": SAFETY_UPDATE, "set": SAFETY_UPDATE, "edit": SAFETY_UPDATE, "publish": SAFETY_UPDATE,
    "delete": SAFETY_DELETE, "remove": SAFETY_DELETE, "destroy": SAFETY_DELETE,
}

# Adapter tiers (G2; safest-first).
TIER_T1 = "t1-official-api"
TIER_T2 = "t2-headless-browser"
TIER_T3 = "t3-structured-export"

# ToS gate outcomes (G2).
TOS_OK = "ok"
TOS_REFUSED = "refused-automation-prohibited"

# Mutate gate outcomes (G5).
MUTATE_READ_ALLOWED = "read-allowed"
MUTATE_AWAIT_SIG = "awaiting-member-sig"

# Honest degradations (G8).
UNKNOWN_SERVICE = "unknown-service"
UNSUPPORTED_OP = "unsupported-op"


@dataclass
class ServiceOp:
    service: str
    noun: str
    verb: str
    safety: str
    destructive: bool
    adapter_tier: str
    args: dict = field(default_factory=dict)
    service_known: bool = True
    dry_run: bool = True              # G6 invariant — R0 never executes
    tos_gate: str = TOS_OK
    mutate_gate: str = MUTATE_READ_ALLOWED
    t2_engine: str = ""              # browser-use, only on a permitted T2 op (G2)
    note: str = ""


def classify_safety(verb: str) -> str:
    """Map a verb to its op safety. Unknown verbs are treated conservatively as :update (mutating)."""
    return VERB_SAFETY.get((verb or "").strip().lower(), SAFETY_UPDATE)


def is_destructive(safety: str) -> bool:
    """G5: delete is the only irreversible class; flagged for explicit member confirmation."""
    return safety == SAFETY_DELETE


def resolve_service(service_id: str) -> dict | None:
    """Look the service up in the :representative registry. None → honest :unknown-service (G8)."""
    return SERVICE_REGISTRY.get((service_id or "").strip().lower())


def t2_stance(rec: dict) -> str:
    """The browser-automation stance for a service. Missing → 'prohibited' (default-deny; G2)."""
    return rec.get("t2", "prohibited")


def select_tier(rec: dict) -> str:
    """Safest-first (G2): official API > ToS-permitted browser-use > structured export."""
    if rec.get("official_api"):
        return TIER_T1
    if t2_stance(rec) in ("permitted", "restricted"):
        return TIER_T2
    return TIER_T3


def tos_gate(rec: dict, tier: str) -> str:
    """G2: a T2 browser-use op on a service whose browser-automation stance is 'prohibited' is
    refused by construction — even when an official API exists (e.g. Google, Facebook)."""
    if tier == TIER_T2 and t2_stance(rec) == "prohibited":
        return TOS_REFUSED
    return TOS_OK


def t2_engine(rec: dict, tier: str, gate: str) -> str:
    """The browser-automation engine (browser-use) for a permitted T2 op; '' otherwise (G2)."""
    if tier == TIER_T2 and gate == TOS_OK and t2_stance(rec) in ("permitted", "restricted"):
        return T2_ENGINE
    return ""


def mutate_gate(safety: str) -> str:
    """G5: reads are allowed at R0; any mutation awaits a member signature."""
    return MUTATE_READ_ALLOWED if safety == SAFETY_READ else MUTATE_AWAIT_SIG


def parse_command(line: str) -> tuple[str, str, str, dict]:
    """Parse `[karakuri] <service> <noun>.<verb> [--flag value ...]` → (service, noun, verb, args).

    Raises ValueError on a malformed command (G8 — never guesses the shape).
    """
    tokens = (line or "").strip().split()
    if tokens and tokens[0].lower() == "karakuri":
        tokens = tokens[1:]
    if len(tokens) < 2:
        raise ValueError(f"malformed command (need '<service> <noun>.<verb>'): {line!r}")
    service = tokens[0].lower()
    nv = tokens[1]
    if "." not in nv:
        raise ValueError(f"malformed op (need '<noun>.<verb>'): {nv!r}")
    noun, verb = nv.split(".", 1)
    if not noun or not verb:
        raise ValueError(f"malformed op (empty noun or verb): {nv!r}")

    args: dict = {}
    i = 2
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
    return service, noun.lower(), verb.lower(), args


def plan(line: str, prefer_tier: str | None = None) -> ServiceOp:
    """Parse a command into a dry-run ServiceOp plan with the ToS + mutate gates applied (no network).

    `prefer_tier` lets a caller request a specific adapter (e.g. force T2) so the G2 ToS gate can be
    demonstrated; by default the safest tier is selected.
    """
    service, noun, verb, args = parse_command(line)
    safety = classify_safety(verb)
    rec = resolve_service(service)

    if rec is None:
        # G8: unknown service degrades honestly — no tier, no guess.
        return ServiceOp(
            service=service, noun=noun, verb=verb, safety=safety,
            destructive=is_destructive(safety), adapter_tier="",
            args=args, service_known=False, tos_gate=TOS_OK,
            mutate_gate=mutate_gate(safety), note=UNKNOWN_SERVICE,
        )

    tier = prefer_tier or select_tier(rec)
    gate = tos_gate(rec, tier)
    engine = t2_engine(rec, tier, gate)
    note = ""
    if gate == TOS_REFUSED:
        note = "G2: ToS prohibits browser automation; T2 browser-use refused — use the official API (T1) or T3 export"

    return ServiceOp(
        service=service, noun=noun, verb=verb, safety=safety,
        destructive=is_destructive(safety), adapter_tier=tier,
        args=args, service_known=True, dry_run=True,
        tos_gate=gate, mutate_gate=mutate_gate(safety), t2_engine=engine, note=note,
    )


if __name__ == "__main__":  # pragma: no cover — tiny offline demo
    import sys

    line = " ".join(sys.argv[1:]) or "karakuri squarespace pages.list"
    op = plan(line)
    print(f"service={op.service} known={op.service_known} {op.noun}.{op.verb} "
          f"safety={op.safety} destructive={op.destructive} tier={op.adapter_tier} "
          f"tos={op.tos_gate} mutate={op.mutate_gate} dry_run={op.dry_run}"
          + (f"  engine={op.t2_engine}" if op.t2_engine else "")
          + (f"  note={op.note}" if op.note else ""))
