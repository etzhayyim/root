"""triage.py — 朱 (ake) edit triage: risk + quality scoring and routing. ADR-2606052100.

THE HEART of the membrane and the G2 anchor. Given a member-signed proposal it produces:

  - risk     ∈ {low, medium, high, invariant}   — a SCORE, never a verdict
  - quality  ∈ [0, 1]                            — sourcing + plausibility + Rider-clean
                                                    (the Wikipedia "ORES" analogue)
  - route    ∈ {auto-accept, vote, council-lv7, refused}

The single invariant that makes this charter-clean: **route is a PURE FUNCTION of
(risk, quality)** computed by `route_for(...)`. An LLM may, at R1, refine the risk/quality
SCORES (Murakumo-only, G6) — but it never emits a route and never accepts or rejects (非裁定,
G2). `score_edit` REFUSES to carry a `decision` field; the only acceptance authorities are the
optimistic threshold rule, a 1 SBT = 1 vote, or Council.

Validation enforced here (mirrors the schema :db/allowed + lexicon :const):
  G1 — author-kind must be `member`; an unsourced server/anon author is a ValueError.
  G1 — server-held-key must be falsey (no-server-key, ADR-2605231525).
  G4 — provenance is mandatory; an unsourced proposal is a ValueError (not merely low-quality).
  G3 — target-kind must be kg-fact | actor-profile (impersonation unrepresentable upstream).

Stdlib only. Deterministic at R0 (honest: no live LLM here — the LLM refines scores at R1).
"""

from __future__ import annotations

from typing import Any

# ── closed vocab (mirror of the ontology :db/allowed) ───────────────────────────
TARGET_KINDS = ("kg-fact", "actor-profile")
RISKS = ("low", "medium", "high", "invariant")
ROUTES = ("auto-accept", "vote", "council-lv7", "refused")

# Attributes whose edit touches a constitutional invariant → never optimistic-accept (G7).
INVARIANT_ATTRS = frozenset({
    "license", "charter", "force-class", "forceclass", "server-held-key", "serverheldkey",
    "verification-method", "verificationmethod", "vm", "gates", "is-mirror", "ismirror",
})
# Attributes that are materially sensitive (state, identity) → escalate to a vote (G).
SENSITIVE_ATTRS = frozenset({
    "status", "did", "handle", "owner", "operator", "controller", "adr", "primary-lexicon",
})

# Charter-Rider §2(a)-(h) hard-gate tokens (a local mirror of charter_rider.scan(),
# ADR-2605192200). A hit cannot be promoted by ANY vote → route :refused.
RIDER_FORBIDDEN = (
    "advertis", "affiliate", "adsense", "meta pixel", "ga4",            # §2 ad/affiliate
    "weapon", "munition", "fire-control", "directed-energy",            # §2(a) force
    "surveillance", "biometric", "pattern-of-life",                     # §2 surveillance
    "addictive", "dark-pattern", "engagement-maxim",                    # §1.13 Wellbecoming
    "広告", "アフィリエイト", "兵器",
)

QUALITY_AUTO_ACCEPT = 0.7   # optimistic fast-path threshold


def _kw(v: Any) -> str:
    """Normalize an edn keyword/string to a bare lowercase token (':actor/status' → 'status')."""
    s = str(v or "").lstrip(":")
    return s.split("/")[-1].lower()


def _verifiable_provenance(p: str) -> bool:
    p = (p or "").strip().lower()
    return p.startswith(("http://", "https://", "ipfs://", "cid:", "bafy")) or "://" in p


def rider_hit(*texts: str) -> str:
    """Return the first Charter-Rider §2 forbidden token found, or '' if clean."""
    blob = " ".join(t or "" for t in texts).lower()
    for tok in RIDER_FORBIDDEN:
        if tok in blob:
            return tok
    return ""


def assess_quality(edit: dict, rider: str) -> float:
    """0..1 sourcing + plausibility + Rider-clean score (the ORES analogue)."""
    if rider:
        return 0.0   # a Charter-Rider violation is unpromotable, full stop
    q = 0.0
    if _verifiable_provenance(edit.get(":edit/provenance", "")):
        q += 0.5
    elif edit.get(":edit/provenance"):
        q += 0.15    # present but not obviously verifiable
    rationale = str(edit.get(":edit/rationale", ""))
    if len(rationale.strip()) >= 10:
        q += 0.2
    # plausibility: a non-empty proposed value for an :assert, sane length
    val = str(edit.get(":edit/proposed-value", ""))
    if edit_op(edit) in ("assert", "promote-sourcing") and 0 < len(val) <= 4000:
        q += 0.3
    elif edit_op(edit) in ("retract", "challenge"):
        q += 0.3     # retraction/challenge needs no value
    return round(min(q, 1.0), 4)


def edit_op(edit: dict) -> str:
    return _kw(edit.get(":edit/op", "assert"))


def assess_risk(edit: dict, rider: str) -> str:
    attr = _kw(edit.get(":edit/target-attr", ""))
    if rider:
        return "invariant"            # a Rider hit is treated as the highest risk class
    if attr in INVARIANT_ATTRS:
        return "invariant"
    if edit_op(edit) == "challenge" or attr in SENSITIVE_ATTRS:
        return "high"
    if _kw(edit.get(":edit/target-kind", "")) == "actor-profile":
        return "medium"               # subjective prose → community eyes
    return "low"                      # a sourced KG fact


def route_for(risk: str, quality: float, rider: str) -> str:
    """G2 INVARIANT — route is a PURE FUNCTION of (risk, quality, rider). No model decides this."""
    if rider:
        return "refused"              # Charter-Rider §2 hit: no vote can promote it
    if risk == "invariant":
        return "council-lv7"          # constitutional-adjacent → Council Lv7+ (G7)
    if risk == "low" and quality >= QUALITY_AUTO_ACCEPT:
        return "auto-accept"          # optimistic fast-path (the Wikipedia good-edit case)
    return "vote"                     # everything else → 1 SBT = 1 vote


def score_edit(edit: dict, by: str = "murakumo:gemma3:4b") -> dict:
    """Validate (G1/G3/G4) then score + route a proposal. Raises ValueError on a hard gate.

    Returns a triage dict with risk + quality + route + by. It NEVER returns a decision (G2).
    """
    if "decision" in edit or ":triage/decision" in edit:
        raise ValueError("G2: triage scores risk+quality and routes; it never accepts/rejects (非裁定)")

    kind = _kw(edit.get(":edit/target-kind", ""))
    if kind not in TARGET_KINDS:
        raise ValueError(
            f"G3: target-kind {kind!r} not in {TARGET_KINDS} — entity-speech/impersonation unrepresentable"
        )
    if _kw(edit.get(":edit/author-kind", "")) != "member":
        raise ValueError("G1: author-kind must be 'member' (no-server-key + 信者-gated; server/anon refused)")
    if edit.get(":edit/server-held-key", False):
        raise ValueError("G1/no-server-key: server-held-key must be false (ADR-2605231525)")
    if not str(edit.get(":edit/provenance", "")).strip():
        raise ValueError("G4: an unsourced proposal is refused — provenance (URL/CID) is mandatory")

    rider = rider_hit(edit.get(":edit/proposed-value", ""), edit.get(":edit/rationale", ""))
    risk = assess_risk(edit, rider)
    quality = assess_quality(edit, rider)
    route = route_for(risk, quality, rider)
    return {
        ":triage/edit": edit.get(":edit/id", "?"),
        ":triage/risk": ":" + risk,
        ":triage/quality": quality,
        ":triage/route": ":" + route,
        ":triage/by": by,
        ":triage/rider-token": rider,   # diagnostic; "" when clean
    }


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-edit-graph.kotoba.edn")
    print("# 朱 (ake) — triage of the :representative seed batch\n")
    print("| edit | target | risk | quality | route |")
    print("|---|---|---|---|---|")
    for e in seed[":edit/batch"]:
        t = score_edit(e)
        print(f"| {t[':triage/edit']} | {_kw(e.get(':edit/target-kind'))}:"
              f"{_kw(e.get(':edit/target-attr'))} | {t[':triage/risk']} | "
              f"{t[':triage/quality']} | {t[':triage/route']} |")
