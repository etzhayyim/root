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
