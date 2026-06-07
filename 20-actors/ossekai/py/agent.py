#!/usr/bin/env python3
"""ossekai 御節介 — information-arbitrage observer + aggregate-first publisher (kotoba WASM cell).

ADR-2605264000. Runs in-WASM on kotoba :8077. ossekai eliminates INFORMATION arbitrage —
places where a beneficial public fact (a refund right, a free service, a deadline, an
entitlement) exists but is buried beneath legalese, paywalls, or dispersed sources — and
delivers Wellbecoming-nudges. This R1 build implements the two foundational cells:

  handle_arbitrage_observer   pre-published archives → information-asymmetry pockets (G3 passive-only)
  handle_aggregate_publisher  gap reports → anonymized aggregate AT Proto advisory (G4 aggregate-first)

Constitutional posture (the discipline that separates ossekai from a marketing/CRM engine):

  G1 Charter-Rider-clean — every emitted advisory is scanned for the §2(a)..(h) prohibited
                           categories; a hit refuses the output.
  G3 passive-only        — the observer consumes ONLY pre-published archives / voluntary AT
                           Proto records (source-class in PASSIVE_SOURCE_CLASSES). A live-probe
                           / handle-enum / WHOIS source is refused outright — never fetched.
  G4 aggregate-first     — the anonymized public feed is the DEFAULT; advisories carry no
                           targeted handle and `shape == "aggregate"`. Individual @mention is a
                           SECONDARY, Council-gated path (mention_dispatcher, not this cell).
  G6 no dark patterns    — composed text carries no urgency / scarcity / engagement hook.
  G7 rate limit          — ≤100 aggregate posts/week (hard ceiling).
  G9 signed sender DID   — every post carries did:web:ossekai.etzhayyim.com (transparent sender).
  G10 Wellbecoming framing — no fear / shame / zero-sum; framing is opportunity-positive.
  G12 Murakumo-only      — any LLM narration is via the kotoba `llm` host binding (no external LLM).

This R1 build computes and returns records/drafts; it does not run live archive ingest and
does not broadcast posts (both operator-gated). Seed data is representative (G11 honesty).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# G7 — hard weekly ceiling on aggregate posts.
WEEKLY_CEILING = 100
# G13 — non-member @mention campaign attestation thresholds.
COUNCIL_MIN_LEVEL = 6          # Council Lv6+
MIN_SIGNERS = 3               # ≥3 attesters …
MIN_SIGNERS_LARGE = 4        # … ≥4 if the campaign exceeds LARGE_CAMPAIGN handles
LARGE_CAMPAIGN = 50
# G7 — non-member rate budget: at most one @mention per handle per 90 days.
NONMEMBER_RATE_DAYS = 90
# externalMentionConsent validity window (revocable, ≤365 days).
CONSENT_MAX_DAYS = 365
# A gap at/above this score is "notable" enough to advise on.
NOTABLE_GAP = 0.5
# G3 — the ONLY source classes the observer may consume (pre-published / voluntary).
PASSIVE_SOURCE_CLASSES = frozenset({
    "pre-published-archive", "public-broadcast", "voluntary-atproto",
    "open-dataset", "legal-corpus",
})
# G3 — source classes that are an active probe; consuming these is a hard refusal.
ACTIVE_PROBE_CLASSES = frozenset({
    "live-dns", "traceroute", "whois", "rdap", "doh", "handle-enum", "port-scan",
})
# G1 — Charter Rider §2(a)..(h) prohibited-category trip words (representative scanner;
# the canonical scanner is etzhayyim_organism.sensors.charter_rider.scan()).
_CHARTER_RIDER_TRIP = ("weapon", "surveillance-for-hire", "addictive", "gore",
                       "non-consensual", "deceptive-ad", "predatory-loan")
# G6 — dark-pattern / urgency vocabulary that must NEVER appear in a composed advisory.
_DARK_PATTERN_WORDS = ("hurry", "act now", "limited time", "last chance", "only today",
                       "don't miss", "urgent", "急いで", "今すぐ", "残りわずか")

OSSEKAI_DID = "did:web:ossekai.etzhayyim.com"


# --------------------------------------------------------------------------- #
# shared gate helpers
# --------------------------------------------------------------------------- #
def charter_rider_clean(text: str) -> bool:
    """G1 — True iff the text trips none of the §2(a)..(h) prohibited categories."""
    low = text.lower()
    return not any(w in low for w in _CHARTER_RIDER_TRIP)


def no_dark_pattern(text: str) -> bool:
    """G6 — True iff the text carries no urgency / scarcity / engagement hook."""
    low = text.lower()
    return not any(w in low for w in _DARK_PATTERN_WORDS)


# --------------------------------------------------------------------------- #
# arbitrage_observer — detect information-asymmetry pockets (G3 passive-only)
# --------------------------------------------------------------------------- #
class ObserverState(TypedDict, total=False):
    items: list
    reports: list
    refused: list


def _gap_score(item: dict) -> float:
    """Higher = a more valuable public fact that is harder to reach. benefit ∈ [0,1] is
    how beneficial the fact is to a person; accessibility ∈ [0,1] is how easy it already
    is to find/use. The arbitrage pocket is benefit that accessibility has not yet closed."""
    benefit = max(0.0, min(1.0, float(item.get("benefit", 0.0))))
    accessibility = max(0.0, min(1.0, float(item.get("accessibility", 0.0))))
    return round(benefit * (1.0 - accessibility), 4)


def handle_arbitrage_observer(state: ObserverState) -> ObserverState:
    """Consume pre-published info items, refuse any active-probe source (G3), and emit an
    arbitrageGapReport per item whose information-asymmetry gap is notable. Reports default
    to `shape: aggregate` (G4) — the observer never targets an individual."""
    reports: list = []
    refused: list = []
    for item in state.get("items", []):
        sclass = item.get("sourceClass", "unknown")
        if sclass in ACTIVE_PROBE_CLASSES:
            # G3 — an active probe is structurally refused; it is never consumed.
            refused.append({"topic": item.get("topic"), "reason": f"active-probe source refused (G3): {sclass}"})
            continue
        if sclass not in PASSIVE_SOURCE_CLASSES:
            refused.append({"topic": item.get("topic"), "reason": f"non-passive source skipped (G3): {sclass}"})
            continue
        score = _gap_score(item)
        if score < NOTABLE_GAP:
            continue
        reports.append({
            "topic": item.get("topic"),
            "gapScore": score,
            "notable": True,
            "publicRight": bool(item.get("publicRight", False)),
            "shape": "aggregate",          # G4 — aggregate-first, never targeted
            "sourceClass": sclass,         # G11 — provenance carried
        })
    return {**state, "reports": reports, "refused": refused}


# --------------------------------------------------------------------------- #
# aggregate_publisher — compose anonymized aggregate advisory (G4/G6/G7/G9/G10)
# --------------------------------------------------------------------------- #
def compose_advisory(report: dict) -> dict:
    """Compose ONE anonymized, Wellbecoming-positive advisory from a gap report. No targeted
    handle (G4), no urgency (G6), Charter-Rider-clean (G1). Returns the post + a clean flag."""
    topic = report.get("topic", "a public benefit")
    text = (
        f"知っておくと役立つ公共情報: 「{topic}」は利用できる権利/制度ですが、"
        "情報が見つけにくい状態です。落ち着いて確認してみてください。"
    )
    clean = charter_rider_clean(text) and no_dark_pattern(text)
    return {
        "text": text,
        "shape": "aggregate",          # G4
        "lexicon": "app.bsky.feed.post",
        "signedDid": OSSEKAI_DID,      # G9 — transparent signed sender
        "targetedHandle": None,        # G4 — never an individual in this cell
        "nudge": False,                # G6 — no engagement hook
        "wellbecomingPositive": True,  # G10
        "clean": clean,
    }


def handle_aggregate_publisher(state: dict) -> dict:
    """Compose anonymized aggregate advisories from gap reports and (optionally) post them.
    Enforces the weekly ceiling (G7), aggregate-first shape (G4), Charter-Rider + dark-pattern
    cleanliness (G1/G6). Live broadcast is operator-gated (no-server-key): without `operatorRef`
    the posts are returned as :draft and nothing is broadcast."""
    reports = state.get("reports", [])
    posted_this_week = int(state.get("postedThisWeek", 0))
    operator_ref = state.get("operatorRef")

    posts: list = []
    skipped: list = []
    for r in reports:
        if posted_this_week + len(posts) >= WEEKLY_CEILING:
            skipped.append({"topic": r.get("topic"), "reason": f"weekly ceiling {WEEKLY_CEILING} reached (G7)"})
            continue
        post = compose_advisory(r)
        if not post["clean"]:
            skipped.append({"topic": r.get("topic"), "reason": "Charter-Rider/dark-pattern refusal (G1/G6)"})
            continue
        post["state"] = "posted" if operator_ref else "draft"   # operator-gated broadcast
        posts.append(post)

    return {
        **state,
        "posts": posts,
        "skipped": skipped,
        "broadcast": bool(operator_ref),
        # G4 audit: every produced post is aggregate-shaped
        "aggregateSharePct": 100 if posts and all(p["shape"] == "aggregate" for p in posts) else 0,
    }


# =========================================================================== #
# R2 — consent_registry (G15) + mention_dispatcher (G13/G15) — targeted path
# =========================================================================== #
# The SECONDARY, Council-gated path. aggregate_publisher is and stays the default
# (G4); these two cells make individual @mention possible ONLY under the strongest
# constitutional gates. A block/mute is honored BEFORE composition (G15) — the post
# never enters MST — and every campaign needs a Council Lv6+ ≥3 attestation (G13).


def handle_consent_registry(state: dict) -> dict:
    """Fold AT Proto block/mute events + externalMentionConsent grants into a per-handle
    consent state. A block or mute is permanent until explicitly lifted (G15, honored
    immediately); a consent grant is valid only until its expiry (≤365d) and is revocable.
    Pure fold over `events` (each {handle, kind, at, [expiry]}) as-of `now`.

    kind ∈ {block, mute, unblock, unmute, consent, revoke}. Returns {handle → state}."""
    now = int(state.get("now", 0))
    st: dict = {}
    for ev in sorted(state.get("events", []), key=lambda e: int(e.get("at", 0))):
        h = ev.get("handle")
        if h is None:
            continue
        cur = st.setdefault(h, {"handle": h, "blocked": False, "muted": False,
                                "consentExpiry": None})
        kind = ev.get("kind")
        if kind == "block":
            cur["blocked"] = True
        elif kind == "unblock":
            cur["blocked"] = False
        elif kind == "mute":
            cur["muted"] = True
        elif kind == "unmute":
            cur["muted"] = False
        elif kind == "consent":
            exp = ev.get("expiry")
            # clamp to the ≤365d window from grant time
            cap = int(ev.get("at", now)) + CONSENT_MAX_DAYS
            cur["consentExpiry"] = min(int(exp), cap) if exp is not None else cap
        elif kind == "revoke":
            cur["consentExpiry"] = None
    for h, cur in st.items():
        cur["consentValid"] = (cur["consentExpiry"] is not None and cur["consentExpiry"] > now)
        # G15: a do-not-contact signal overrides any consent
        cur["contactable"] = (not cur["blocked"]) and (not cur["muted"])
    return {**state, "consentState": st}


def _attestation_ok(attestation: dict, campaign_size: int) -> tuple[bool, str]:
    """G13 — a non-member @mention campaign needs Council Lv6+ with ≥3 signers (≥4 if the
    campaign exceeds LARGE_CAMPAIGN handles). Returns (ok, reason)."""
    if not attestation:
        return False, "no Council attestation (G13)"
    if int(attestation.get("councilLevel", 0)) < COUNCIL_MIN_LEVEL:
        return False, f"Council Lv{COUNCIL_MIN_LEVEL}+ required (G13)"
    need = MIN_SIGNERS_LARGE if campaign_size > LARGE_CAMPAIGN else MIN_SIGNERS
    if int(attestation.get("signers", 0)) < need:
        return False, f"≥{need} attesters required for campaign size {campaign_size} (G13)"
    return True, "council-attested"


def handle_mention_dispatcher(state: dict) -> dict:
    """Compose non-member @mentions ONLY under the full gate stack. Order matters:

      1. G13 — the whole campaign is refused unless Council Lv6+ ≥3 (≥4 if >50) attests.
      2. consent — each handle needs EITHER a campaign-wide memberImpactAttestationCid OR
         its own valid externalMentionConsent.
      3. G15 — a blocked/muted handle is rejected BEFORE composing; the post never exists.
      4. G7 — at most one @mention per handle per 90 days (lastMentionAt budget).

    Allowed handles get a :draft post (broadcast operator-gated, no-server-key). Every
    rejection carries its reason; rejected handles never enter MST."""
    handles = list(state.get("handles", []))
    attestation = state.get("attestation", {})
    consent_state = state.get("consentState", {})
    member_impact_cid = state.get("memberImpactAttestationCid")
    last_mention = state.get("lastMentionAt", {})    # {handle → ts}
    now = int(state.get("now", 0))
    operator_ref = state.get("operatorRef")
    topic = state.get("topic", "a public benefit")

    ok, reason = _attestation_ok(attestation, len(handles))
    if not ok:
        return {**state, "dispatches": [], "rejected": [{"handle": h, "reason": reason} for h in handles],
                "campaignRefused": True}

    dispatches: list = []
    rejected: list = []
    for h in handles:
        cs = consent_state.get(h, {})
        # G15 — do-not-contact wins, checked BEFORE composing anything
        if cs.get("blocked") or cs.get("muted"):
            rejected.append({"handle": h, "reason": "blocked/muted — rejected before composition (G15)"})
            continue
        # consent path: campaign-wide member-impact OR per-recipient valid consent
        if not member_impact_cid and not cs.get("consentValid"):
            rejected.append({"handle": h, "reason": "no member-impact attestation and no valid externalMentionConsent (G13)"})
            continue
        # G7 — per-handle 90d rate budget
        last = last_mention.get(h)
        if last is not None and (now - int(last)) < NONMEMBER_RATE_DAYS:
            rejected.append({"handle": h, "reason": f"within {NONMEMBER_RATE_DAYS}d rate budget (G7)"})
            continue
        text = (f"@{h} 参考情報として: 「{topic}」が利用できる可能性があります。"
                " 不要な場合はブロック/ミュートで今後お送りしません。")
        if not (charter_rider_clean(text) and no_dark_pattern(text)):
            rejected.append({"handle": h, "reason": "Charter-Rider/dark-pattern refusal (G1/G6)"})
            continue
        dispatches.append({
            "handle": h, "text": text, "lexicon": "app.bsky.feed.post",
            "signedDid": OSSEKAI_DID,                 # G9
            "shape": "targeted",                       # secondary path (NOT aggregate)
            "attestation": attestation.get("ref"),     # G13 audit trail
            "state": "posted" if operator_ref else "draft",
        })
    return {**state, "dispatches": dispatches, "rejected": rejected,
            "campaignRefused": False, "broadcast": bool(operator_ref)}
