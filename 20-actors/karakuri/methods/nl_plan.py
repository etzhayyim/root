"""karakuri (絡繰) NL→ServiceOp planner — Murakumo-only, stdlib (ADR-2606039200, G4).

Turns a member's natural-language brief into an ordered list of normalized ServiceOps (each gated by
`command.plan`), Charter-Rider scanned (N6), as a dry-run plan (G6). The canonical NL parser is the
**Murakumo** LLM (LiteLLM 127.0.0.1:4000, gemma3:4b — G4); a deterministic heuristic is the always-
available, hermetic fallback. The live LLM call is a refused-by-default membrane (operator + flag
gated), so this module is offline-safe and never reaches the network at R0.

G4 Murakumo-only (no other inference path) · G5 mutate-gated · G6 dry-run only · N6 Charter-Rider scan.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from command import ServiceOp, SERVICE_REGISTRY, plan

# ── service synonyms a member might say (→ canonical registry id; G8 honest beyond this set) ──
SERVICE_SYNONYMS: dict[str, str] = {
    "gmail": "google", "googlemail": "google", "gdrive": "google", "drive": "google",
    "gcal": "google", "google-calendar": "google", "calendar": "google", "google": "google",
    "fb": "facebook", "meta": "facebook", "facebook": "facebook",
    "wp": "wordpress", "wordpress": "wordpress", "gh": "github", "github": "github",
}

# ── natural verb → canonical ServiceOp verb (command.VERB_SAFETY classifies the canonical verb) ──
NL_VERB: dict[str, str] = {
    "list": "list", "show": "list", "see": "list", "view": "list", "read": "list",
    "get": "get", "fetch": "get", "open": "get",
    "find": "search", "search": "search",
    "create": "create", "add": "add", "new": "create", "make": "create",
    "update": "update", "change": "update", "edit": "update", "rename": "update",
    "set": "set", "publish": "publish",
    "delete": "delete", "remove": "delete", "drop": "delete", "destroy": "delete",
    "export": "export", "download": "export", "backup": "export",
}

_STOPWORDS = frozenset({
    "the", "a", "an", "my", "all", "of", "from", "in", "on", "to", "for", "me", "please",
    "and", "with", "some", "any", "this", "that",
})

# ── N6 Charter-Rider §2(a)-(h) representative scan (canonical SSoT is
#    etzhayyim_organism.sensors.charter_rider.scan(); this is a stdlib stand-in) ──
CHARTER_RIDER_TERMS: dict[str, str] = {
    "weapon": "§2(a) force/weapons", "munition": "§2(a) force/weapons", "firearm": "§2(a) force/weapons",
    "casino": "§2(b) gambling", "gambling": "§2(b) gambling", "betting": "§2(b) gambling",
    "adsense": "§2 advertising", "affiliate": "§2 advertising", "ad-network": "§2 advertising",
    "surveil": "§2 surveillance", "stalk": "§2 surveillance", "scrape-everyone": "§2 surveillance",
    "captcha-farm": "§2 detection-evasion", "proxy-rotate": "§2 detection-evasion",
}

INFERENCE_MURAKUMO = "murakumo"   # G4 invariant


class LiveLLMRefused(RuntimeError):
    """Raised when a live Murakumo call is requested without the operator gate (G4/G6 default-deny)."""


@dataclass
class CommandPlan:
    brief: str
    ops: list[ServiceOp] = field(default_factory=list)
    charter_clean: bool = True
    charter_hits: list[str] = field(default_factory=list)
    inference: str = INFERENCE_MURAKUMO   # G4
    dry_run: bool = True                   # G6


def charter_scan(text: str) -> tuple[bool, list[str]]:
    """N6: scan a brief (or op) for Charter-Rider §2(a)-(h) prohibited categories. (clean, hits)."""
    low = (text or "").lower()
    hits = sorted({tag for term, tag in CHARTER_RIDER_TERMS.items() if term in low})
    return (not hits, hits)


def _find_service(tokens: list[str]) -> str | None:
    for t in tokens:
        canon = SERVICE_SYNONYMS.get(t)
        if canon:
            return canon
        if t in SERVICE_REGISTRY:
            return t
    return None


def heuristic_parse(brief: str) -> str | None:
    """Best-effort deterministic NL→command (the hermetic fallback; honest about its limits).

    Recognizes a known service + a natural verb, infers a noun from nearby tokens. Returns a
    `<service> <noun>.<verb>` command string, or None when it cannot confidently parse (G8 — never
    guesses a service that is not in the registry).
    """
    raw = [t.strip(".,!?;:'\"()").lower() for t in (brief or "").split()]
    tokens = [t for t in raw if t]
    if not tokens:
        return None

    service = _find_service(tokens)
    if service is None:
        return None
    service_idx = next(
        i for i, t in enumerate(tokens) if t == service or SERVICE_SYNONYMS.get(t) == service
    )

    verb_idx = next((i for i, t in enumerate(tokens) if t in NL_VERB), None)
    if verb_idx is None:
        return None
    verb = NL_VERB[tokens[verb_idx]]

    # Noun candidates: tokens that name neither the service, a verb, a stopword, nor a flag.
    candidates = [
        (i, t) for i, t in enumerate(tokens)
        if t not in NL_VERB and t not in _STOPWORDS and t != service
        and t not in SERVICE_SYNONYMS and not t.startswith("--")
    ]
    # Prefer the first candidate after the service name (the natural "<service> <noun>" order),
    # else the last candidate anywhere, else a safe generic.
    after = [t for i, t in candidates if i > service_idx]
    noun = after[0] if after else (candidates[-1][1] if candidates else "items")
    return f"{service} {noun}.{verb}"


def _murakumo_complete(brief: str, *, operator_attestation: str | None, env: dict | None) -> str:
    """G4: the Murakumo NL→command path. Refused unless explicitly operator-gated (default-deny).

    When gated on it would POST to LiteLLM 127.0.0.1:4000 (loopback, TCC-exempt per ADR-2605302355).
    At R0 this membrane refuses; no other inference provider is reachable from here (G4).
    """
    flag = (env or os.environ).get("KARAKURI_ALLOW_LIVE_LLM")
    if flag != "1" or not operator_attestation:
        raise LiveLLMRefused(
            "G4/G6: live Murakumo NL planning is operator-gated "
            "(KARAKURI_ALLOW_LIVE_LLM=1 + operator attestation); R0 uses the deterministic fallback"
        )
    # Gated path (not exercised at R0): a real impl would POST to 127.0.0.1:4000 and return a command.
    raise LiveLLMRefused("live Murakumo client not wired at R0 (Council activation pending)")


def plan_from_brief(
    brief: str,
    *,
    use_live_llm: bool = False,
    operator_attestation: str | None = None,
    env: dict | None = None,
) -> CommandPlan:
    """Plan a member's NL brief into an ordered, gated, Charter-scanned ServiceOp list (dry-run).

    `use_live_llm=True` routes through Murakumo (operator-gated; raises LiveLLMRefused if not gated).
    Otherwise the deterministic heuristic is used. Either way every op passes through `command.plan`
    so the ToS + mutate gates apply (G2/G5), and the brief + ops are Charter-Rider scanned (N6).
    """
    clean, hits = charter_scan(brief)

    command_line = None
    if use_live_llm:
        command_line = _murakumo_complete(
            brief, operator_attestation=operator_attestation, env=env
        )
    else:
        command_line = heuristic_parse(brief)

    ops: list[ServiceOp] = []
    if command_line and clean:
        op = plan(command_line)
        # N6: also scan the resolved op text.
        op_clean, op_hits = charter_scan(f"{op.service} {op.noun} {op.verb}")
        if op_clean:
            ops.append(op)
        else:
            clean = False
            hits = sorted(set(hits) | set(op_hits))

    return CommandPlan(
        brief=brief, ops=ops, charter_clean=clean, charter_hits=hits,
        inference=INFERENCE_MURAKUMO, dry_run=True,
    )


if __name__ == "__main__":  # pragma: no cover — offline demo
    import sys

    brief = " ".join(sys.argv[1:]) or "list all my gmail messages"
    cp = plan_from_brief(brief)
    print(f"brief={cp.brief!r} clean={cp.charter_clean} inference={cp.inference} dry_run={cp.dry_run}")
    for op in cp.ops:
        print(f"  -> {op.service} {op.noun}.{op.verb} tier={op.adapter_tier} "
              f"mutate={op.mutate_gate}" + (f" engine={op.t2_engine}" if op.t2_engine else ""))
    if not cp.ops:
        print("  (no confident parse; the Murakumo LLM path is operator-gated at R0)")
