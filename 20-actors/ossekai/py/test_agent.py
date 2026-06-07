#!/usr/bin/env python3
"""ossekai 御節介 — agent logic tests (ADR-2605264000).

Pure-logic tests over the two foundational cells; no kotoba host bindings required
(the datalog/llm imports degrade to None in local dev). Verifies the constitutional
invariants that distinguish ossekai from a marketing / CRM engine:

  - G3 passive-only: an active-probe source is refused, never consumed
  - information-asymmetry gap = benefit × (1 − accessibility); notable ≥ 0.5
  - G4 aggregate-first: every report/post is aggregate-shaped, no targeted handle
  - G7 weekly ceiling caps aggregate posts at 100
  - G1/G6 Charter-Rider + dark-pattern cleanliness refuses bad output
  - G9 signed sender DID present; broadcast operator-gated (default :draft)
"""
import agent


def _items():
    return [
        # high benefit, low accessibility → big gap (buried public right)
        {"topic": "クーリングオフ", "benefit": 0.9, "accessibility": 0.2,
         "publicRight": True, "sourceClass": "legal-corpus"},
        # high benefit, already accessible → small gap (skip)
        {"topic": "確定申告期限", "benefit": 0.8, "accessibility": 0.9,
         "sourceClass": "open-dataset"},
        # active probe → must be refused (G3)
        {"topic": "domain-owner", "benefit": 0.9, "accessibility": 0.1,
         "sourceClass": "whois"},
    ]


# ── arbitrage_observer ────────────────────────────────────────────────────
def test_observer_refuses_active_probe_g3():
    out = agent.handle_arbitrage_observer({"items": _items()})
    refused_topics = {r["topic"] for r in out["refused"]}
    assert "domain-owner" in refused_topics            # whois never consumed
    posted_topics = {r["topic"] for r in out["reports"]}
    assert "domain-owner" not in posted_topics


def test_observer_emits_notable_gap_only():
    out = agent.handle_arbitrage_observer({"items": _items()})
    topics = {r["topic"] for r in out["reports"]}
    assert "クーリングオフ" in topics                   # gap 0.72 ≥ 0.5
    assert "確定申告期限" not in topics                 # gap ~0.08 < 0.5 (already accessible)


def test_gap_score_formula():
    # benefit 0.9, accessibility 0.2 → 0.9 * 0.8 = 0.72
    s = agent._gap_score({"benefit": 0.9, "accessibility": 0.2})
    assert s == 0.72


def test_reports_are_aggregate_shaped_g4():
    out = agent.handle_arbitrage_observer({"items": _items()})
    assert all(r["shape"] == "aggregate" for r in out["reports"])


# ── aggregate_publisher ───────────────────────────────────────────────────
def _reports():
    return agent.handle_arbitrage_observer({"items": _items()})["reports"]


def test_publisher_default_is_draft_signed_aggregate():
    out = agent.handle_aggregate_publisher({"reports": _reports()})
    assert out["posts"], "a notable report should produce a post"
    p = out["posts"][0]
    assert p["state"] == "draft"                       # operator-gated broadcast (no-server-key)
    assert p["shape"] == "aggregate"                   # G4
    assert p["targetedHandle"] is None                 # G4 — never an individual
    assert p["signedDid"] == agent.OSSEKAI_DID         # G9
    assert p["nudge"] is False                         # G6
    assert out["aggregateSharePct"] == 100             # G4 audit


def test_publisher_posts_with_operator():
    out = agent.handle_aggregate_publisher({"reports": _reports(), "operatorRef": "op:council-123"})
    assert out["broadcast"] is True
    assert out["posts"][0]["state"] == "posted"


def test_publisher_weekly_ceiling_g7():
    out = agent.handle_aggregate_publisher(
        {"reports": _reports(), "postedThisWeek": agent.WEEKLY_CEILING})
    assert out["posts"] == []
    assert any("ceiling" in s["reason"] for s in out["skipped"])


def test_publisher_refuses_dark_pattern_and_charter_trips():
    assert agent.no_dark_pattern("落ち着いて確認してください") is True
    assert agent.no_dark_pattern("今すぐ確認 last chance") is False
    assert agent.charter_rider_clean("公共の制度の案内") is True
    assert agent.charter_rider_clean("predatory-loan offer") is False


def test_composed_advisory_is_clean():
    post = agent.compose_advisory({"topic": "クーリングオフ"})
    assert post["clean"] is True
    assert post["wellbecomingPositive"] is True


# ── consent_registry (G15) ────────────────────────────────────────────────
def test_consent_block_overrides_contactable():
    out = agent.handle_consent_registry({"now": 100, "events": [
        {"handle": "alice", "kind": "consent", "at": 10, "expiry": 1000},
        {"handle": "alice", "kind": "block", "at": 20},
    ]})
    a = out["consentState"]["alice"]
    assert a["blocked"] is True
    assert a["contactable"] is False           # G15: block wins over consent


def test_consent_validity_window():
    out = agent.handle_consent_registry({"now": 500, "events": [
        {"handle": "bob", "kind": "consent", "at": 400, "expiry": 600},   # valid (within 365d, >now)
        {"handle": "carol", "kind": "consent", "at": 10, "expiry": 100},  # expired by now=500
    ]})
    assert out["consentState"]["bob"]["consentValid"] is True
    assert out["consentState"]["carol"]["consentValid"] is False


def test_consent_revoke_clears():
    out = agent.handle_consent_registry({"now": 100, "events": [
        {"handle": "dave", "kind": "consent", "at": 10, "expiry": 1000},
        {"handle": "dave", "kind": "revoke", "at": 20},
    ]})
    assert out["consentState"]["dave"]["consentValid"] is False


def test_consent_expiry_clamped_to_365d():
    out = agent.handle_consent_registry({"now": 0, "events": [
        {"handle": "eve", "kind": "consent", "at": 0, "expiry": 10_000},  # > 365d
    ]})
    assert out["consentState"]["eve"]["consentExpiry"] == agent.CONSENT_MAX_DAYS


# ── mention_dispatcher (G13/G15/G7) ───────────────────────────────────────
_ATT_OK = {"councilLevel": 6, "signers": 3, "ref": "att:cid-123"}


def test_dispatcher_refuses_without_council_attestation():
    out = agent.handle_mention_dispatcher({"handles": ["a"], "attestation": {},
                                           "memberImpactAttestationCid": "mi:1"})
    assert out["campaignRefused"] is True
    assert out["dispatches"] == []


def test_dispatcher_large_campaign_needs_four_signers():
    handles = [f"h{i}" for i in range(51)]      # > 50 → needs ≥4
    out = agent.handle_mention_dispatcher({"handles": handles, "attestation": _ATT_OK,
                                           "memberImpactAttestationCid": "mi:1"})
    assert out["campaignRefused"] is True       # only 3 signers


def test_dispatcher_rejects_blocked_before_composition_g15():
    cs = agent.handle_consent_registry({"now": 100, "events": [
        {"handle": "blk", "kind": "block", "at": 1}]})["consentState"]
    out = agent.handle_mention_dispatcher({
        "handles": ["blk"], "attestation": _ATT_OK,
        "memberImpactAttestationCid": "mi:1", "consentState": cs, "now": 100})
    assert out["dispatches"] == []
    assert "G15" in out["rejected"][0]["reason"]


def test_dispatcher_needs_consent_or_member_impact():
    out = agent.handle_mention_dispatcher({
        "handles": ["nocon"], "attestation": _ATT_OK, "consentState": {}, "now": 100})
    assert out["dispatches"] == []              # no member-impact, no consent
    assert "G13" in out["rejected"][0]["reason"]


def test_dispatcher_rate_budget_g7():
    out = agent.handle_mention_dispatcher({
        "handles": ["recent"], "attestation": _ATT_OK, "memberImpactAttestationCid": "mi:1",
        "consentState": {}, "lastMentionAt": {"recent": 80}, "now": 100})  # 20d < 90d
    assert out["dispatches"] == []
    assert "G7" in out["rejected"][0]["reason"]


def test_dispatcher_allows_with_member_impact_default_draft():
    out = agent.handle_mention_dispatcher({
        "handles": ["ok"], "attestation": _ATT_OK, "memberImpactAttestationCid": "mi:1",
        "consentState": {}, "now": 100, "topic": "クーリングオフ"})
    assert len(out["dispatches"]) == 1
    d = out["dispatches"][0]
    assert d["state"] == "draft"               # operator-gated broadcast
    assert d["shape"] == "targeted"            # secondary path, not aggregate
    assert d["signedDid"] == agent.OSSEKAI_DID  # G9


def test_dispatcher_posts_with_operator():
    out = agent.handle_mention_dispatcher({
        "handles": ["ok"], "attestation": _ATT_OK, "memberImpactAttestationCid": "mi:1",
        "consentState": {}, "now": 100, "operatorRef": "op:1"})
    assert out["dispatches"][0]["state"] == "posted"


# ── intel_analyzer (G1/G10/G11/G12) ───────────────────────────────────────
def test_analyzer_emits_community_framed_advisory():
    out = agent.handle_intel_analyzer({"reports": [{"topic": "図書館の無料サービス", "gapScore": 0.7}]})
    assert len(out["advisories"]) == 1
    adv = out["advisories"][0]
    assert adv["framingAuditPassed"] is True       # G10
    assert adv["communityContext"] is True         # G11
    assert adv["domain"] is None                   # general topic → no citation needed
    assert adv["crossActorCitation"] is None


def test_analyzer_requires_cross_actor_citation_for_legal():
    out = agent.handle_intel_analyzer({"reports": [{"topic": "クーリングオフ", "gapScore": 0.7}]})
    adv = out["advisories"][0]
    assert adv["domain"] == "legal"
    assert adv["crossActorCitation"] == "chigiri"  # UPL boundary — route, never render


def test_analyzer_classify_domain():
    assert agent.classify_domain("処方薬の話") == ("pharma", "yakushi")
    assert agent.classify_domain("投資の話") == ("financial", "toritate")
    assert agent.classify_domain("天気") == (None, None)


def test_framing_audit_rejects_fear():
    assert agent.framing_audit("落ち着いて確認しましょう") is True
    assert agent.framing_audit("恐怖を煽る punish message") is False


# ── analyzer → publisher pipeline ─────────────────────────────────────────
def test_publisher_consumes_advisories_with_citation():
    advisories = agent.handle_intel_analyzer(
        {"reports": [{"topic": "クーリングオフ", "gapScore": 0.7}]})["advisories"]
    out = agent.handle_aggregate_publisher({"advisories": advisories})
    assert len(out["posts"]) == 1
    p = out["posts"][0]
    assert p["crossActorCitation"] == "chigiri"
    assert "chigiri" in p["text"]                  # citation routed into the post
    assert p["state"] == "draft"                   # operator-gated


def test_publisher_refuses_domain_advisory_without_citation():
    # a domain-sensitive advisory whose citation was stripped must be refused (UPL boundary)
    bad = [{"topic": "クーリングオフ", "text": "…", "shape": "aggregate",
            "framingAuditPassed": True, "domain": "legal", "crossActorCitation": None}]
    out = agent.handle_aggregate_publisher({"advisories": bad})
    assert out["posts"] == []
    assert any("UPL" in s["reason"] for s in out["skipped"])


# ── kaizen_observer (G4/G5/G14) — self-reflection / deploy-autonomy ────────
def test_kaizen_healthy_quarter_no_halt_no_throttle():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 80, "targetedDispatches": 20, "deliveries": 100,
        "reEngagementAfterOptOut": 0, "commercialCrmPenetrationPct": 0.0,
        "unsubscribeCount": 1, "framingAuditFailures": 0}})
    assert out["halt"] is False
    assert out["throttleMentionCapFactor"] == 1.0
    assert out["review"]["aggregateSharePctIntegerHundredths"] == 8000  # 80.00%


def test_kaizen_re_engagement_is_critical_halt():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 90, "targetedDispatches": 10, "deliveries": 100,
        "reEngagementAfterOptOut": 1}})
    assert out["halt"] is True                       # G14 const 0 breached
    assert any(p["rule"] == "R12" and p["severity"] == "critical" for p in out["proposals"])
    assert any("disputeMediation" in p["action"] for p in out["proposals"])


def test_kaizen_commercial_crm_is_critical_halt():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 90, "targetedDispatches": 10, "deliveries": 100,
        "commercialCrmPenetrationPct": 3.0}})
    assert out["halt"] is True                       # G5 const 0 breached
    assert any(p["rule"] == "R13" for p in out["proposals"])


def test_kaizen_low_aggregate_share_halves_mention_cap():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 30, "targetedDispatches": 70, "deliveries": 100}})  # 30% < 50%
    assert out["halt"] is False
    assert out["throttleMentionCapFactor"] == 0.5    # structural throttle (G4/G14)
    assert any(p["rule"] == "R14" for p in out["proposals"])


def test_kaizen_unsubscribe_and_framing_spikes_warn():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 90, "targetedDispatches": 10, "deliveries": 100,
        "unsubscribeCount": 10, "framingAuditFailures": 5}})
    rules = {p["rule"] for p in out["proposals"]}
    assert "R15" in rules and "R16" in rules
    assert out["halt"] is False                       # warns, does not halt


def test_kaizen_review_record_carries_const_zero_invariants():
    out = agent.handle_kaizen_observer({"metrics": {
        "aggregatePosts": 60, "targetedDispatches": 40, "deliveries": 100}})
    r = out["review"]
    assert r["reEngagementAfterOptOutCount"] == 0
    assert r["commercialIntelCrmSoftwarePenetrationPct"] == 0.0
    assert r["aggregateSharePctIntegerHundredths"] >= 5000   # ≥50.00% floor met


# ── member_digest (G8) ────────────────────────────────────────────────────
_ADV = [{"topic": "図書館サービス", "category": "civic"},
        {"topic": "健康診断補助", "category": "health"}]


def test_member_digest_encrypts_no_plaintext_g8():
    out = agent.handle_member_digest({
        "members": [{"did": "did:m:1", "sbtActive": True, "optedIn": True, "categories": ["civic"]}],
        "advisories": _ADV, "now": 100})
    assert len(out["digests"]) == 1
    d = out["digests"][0]
    assert d["envelope"]["envelopeRef"].startswith("com.etzhayyim.encrypted:")
    assert "topics" in d["envelope"]["sealedFields"]   # only KEYS, never values
    assert d["state"] == "draft"                        # operator-gated


def test_member_digest_requires_active_sbt_and_optin():
    out = agent.handle_member_digest({
        "members": [
            {"did": "did:m:2", "sbtActive": False, "optedIn": True},
            {"did": "did:m:3", "sbtActive": True, "optedIn": False},
        ], "advisories": _ADV, "now": 100})
    assert out["digests"] == []                          # one inactive, one not opted-in (filtered)


def test_member_digest_weekly_rate_limit():
    out = agent.handle_member_digest({
        "members": [{"did": "did:m:4", "sbtActive": True, "optedIn": True, "lastDigestAt": 96}],
        "advisories": _ADV, "now": 100})                 # 4d < 7d
    assert out["digests"] == []
    assert any("period" in s["reason"] for s in out["skipped"])


def test_member_digest_roster_cap_500():
    members = [{"did": f"did:m:{i}", "sbtActive": True, "optedIn": True} for i in range(505)]
    out = agent.handle_member_digest({"members": members, "advisories": _ADV, "now": 100})
    assert out["rosterSize"] == agent.MEMBER_OPT_IN_CAP  # capped at 500
    assert any("cap" in s["reason"] for s in out["skipped"])


def test_member_digest_category_filter():
    out = agent.handle_member_digest({
        "members": [{"did": "did:m:5", "sbtActive": True, "optedIn": True, "categories": ["health"]}],
        "advisories": _ADV, "now": 100})
    assert out["digests"][0]["itemCount"] == 1           # only the health advisory


# ── emergency_advisory (G10) ──────────────────────────────────────────────
def test_emergency_refused_without_kazaori_attestation():
    out = agent.handle_emergency_advisory({"attestation": {"valid": False}, "topic": "x"})
    assert out["refused"] is True
    assert "self-declare" in out["reason"]


def test_emergency_posts_calm_advisory_with_attestation():
    out = agent.handle_emergency_advisory({
        "attestation": {"valid": True, "declarer": "kazaori"}, "topic": "避難所情報"})
    assert out["refused"] is False
    assert out["post"]["expedited"] is True
    assert out["post"]["declarer"] == "kazaori"
    assert out["post"]["state"] == "draft"              # operator-gated


def test_emergency_refuses_panic_framing_g10():
    out = agent.handle_emergency_advisory({
        "attestation": {"valid": True, "declarer": "kazaori"},
        "text": "panic now, catastrophe is here"})
    assert out["refused"] is True
    assert "G10" in out["reason"]


def test_emergency_posts_with_operator():
    out = agent.handle_emergency_advisory({
        "attestation": {"valid": True, "declarer": "kazaori"}, "topic": "避難所情報",
        "operatorRef": "op:emergency-1"})
    assert out["post"]["state"] == "posted"
