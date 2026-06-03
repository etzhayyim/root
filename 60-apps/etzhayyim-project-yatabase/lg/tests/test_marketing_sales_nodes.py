"""Unit coverage for lg-yatabase marketing + sales graph nodes (P19 ship).

DB-touching nodes are tested with monkey-patched fetch/fetchrow/
fetchval/execute so no live RW connection is needed.

LLM is tested only via the deterministic fallback paths — the real
HTTP path is exercised by the integration smoke `curl /runs marketing`
once the pod is deployed.

TODO(substrate-boundary): re-target test fixtures to use @etzhayyim/sdk
e.read/e.write MST mocks instead of asyncpg monkey-patching per ADR-2605172000.
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter

import pytest

from lg_yatabase import templates
from lg_yatabase.graphs import _llm
from lg_yatabase.graphs import marketing as mkt
from lg_yatabase.graphs import sales as sls


# ---------------------------------------------------------------------------
# Templates.
# ---------------------------------------------------------------------------

class TestTemplates:
    def test_marketing_touch_includes_company_and_placeholder(self):
        body = templates.marketing_touch("Acme Corp", "acme.com", "dev-tooling-saas", 1)
        assert "Acme Corp" in body.subject
        assert "[[PARTNER_NAME]]" in body.body_text
        assert "<p>" in body.body_html
        # Footer always present (CAN-SPAM)
        assert "Tokyo, Japan" in body.body_text
        assert "Don't want these" in body.body_text

    def test_marketing_touch_3_distinct_subjects(self):
        s = {templates.marketing_touch("X", "x.com", "bsky-builders", t).subject for t in (1, 2, 3)}
        assert len(s) == 3

    def test_segment_classify(self):
# CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
        assert templates.classify_segment({"tech_stack": "supabase,kysely"}) == "dev-tooling-saas"
        assert templates.classify_segment({"tech_stack": "atproto", "signal": ""}) == "bsky-builders"
        assert templates.classify_segment({"tech_stack": "", "signal": "bluesky stuff"}) == "bsky-builders"
        assert templates.classify_segment({"tech_stack": "snowflake"}) == "data-team-mid-market"
        assert templates.classify_segment({"domain": "acme.co.jp", "tech_stack": ""}) == "jp-saas-founders"
        assert templates.classify_segment({}) == "unknown"

    def test_sales_touch_kinds(self):
        b = templates.sales_touch("sales-onboarding", "did:etzhayyim:test", tenant_name="Acme")
        assert "Acme" in b.body_text
        assert "[[PARTNER_NAME]]" in b.body_text

        b2 = templates.sales_touch("sales-upgrade", "did:etzhayyim:test",
                                   metric_24h={"api_request": 1200})
        assert "1200" in b2.body_text
        assert "Starter" in b2.body_text

        b3 = templates.sales_touch("sales-book-call", "did:etzhayyim:test")
        assert "cal.etzhayyim.com/nishino" in b3.body_text


# ---------------------------------------------------------------------------
# LLM helper — fallback paths.
# ---------------------------------------------------------------------------

class TestLLMFallback:
    def test_no_key_path_returns_none_source(self, monkeypatch):
        monkeypatch.setattr(_llm, "_LLM_KEY", "")
        parsed, src = _llm.call_llm_json("hi", system="sys", max_tokens=64)
        assert parsed is None
        assert src == "fallback-no-key"

    def test_score_lead_falls_back_to_heuristic_when_no_key(self, monkeypatch):
        monkeypatch.setattr(_llm, "_LLM_KEY", "")
        res = _llm.score_lead(
            {"signal": "starred neo4j", "tech_stack": "neo4j,kysely", "contact_email": "x@y.com"},
            segment="dev-tooling-saas",
        )
        assert 0 <= res.score <= 100
        assert res.source == "fallback-no-key"
        # bonus from "starred" + contact_email + multi-tech stack lifts above base
        assert res.score >= 75

    def test_decide_sales_action_falls_back_to_default(self, monkeypatch):
        monkeypatch.setattr(_llm, "_LLM_KEY", "")
        decision, reasoning, source = _llm.decide_sales_action(
            {"plan": "free", "usage_24h": {"api_request": 0},
             "incident_count_24h": 0, "last_touch_at": None},
            default="send_onboarding",
        )
        assert decision == "send_onboarding"
        assert source == "fallback-no-key"
        assert "deterministic" in reasoning


# ---------------------------------------------------------------------------
# Marketing graph — pure node behaviour.
# ---------------------------------------------------------------------------

class TestMarketingPureNodes:
    def test_route_by_score_handoff_threshold(self):
        state = {"scored": [
            {"domain": "hot.com", "fit_score": 85},
            {"domain": "warm.com", "fit_score": 60},
            {"domain": "cold.com", "fit_score": 30},
            {"domain": "", "fit_score": 100},  # missing domain ignored
        ]}
        out = mkt._route_by_score(state)
        assert out["handoffs"] == ["hot.com"]

    def test_draft_outreach_skips_cold_and_hot(self):
        state = {"scored": [
            {"vertex_id": "lead:warm.com", "domain": "warm.com", "company": "Warm Co",
             "fit_score": 65, "segment": "dev-tooling-saas"},
            {"vertex_id": "lead:hot.com", "domain": "hot.com", "company": "Hot Co",
             "fit_score": 90, "segment": "bsky-builders"},
            {"vertex_id": "lead:cold.com", "domain": "cold.com", "company": "Cold Co",
             "fit_score": 20, "segment": "unknown"},
        ]}
        out = mkt._draft_outreach(state)
        drafts = out["drafts"]
        # only the warm lead gets 3 touches; hot is handed off, cold dropped
        assert len(drafts) == 3
        assert all(d["lead_domain"] == "warm.com" for d in drafts)
        assert sorted(d["touch"] for d in drafts) == [1, 2, 3]


# ---------------------------------------------------------------------------
# Marketing graph — DB-touching nodes (monkey-patched).
# ---------------------------------------------------------------------------

@pytest.fixture()
def patched_marketing_db(monkeypatch):
    calls: dict = {"fetch": [], "execute": [], "fetchrow": []}
    fetch_response: list[dict] = []

    async def fake_fetch(query, *args):
        calls["fetch"].append((query, args))
        return list(fetch_response)

    async def fake_execute(query, *args):
        calls["execute"].append((query, args))
        return "INSERT 0 1"

    async def fake_fetchrow(query, *args):
        calls["fetchrow"].append((query, args))
        return None

    monkeypatch.setattr(mkt, "fetch", fake_fetch)
    monkeypatch.setattr(mkt, "execute", fake_execute)
    monkeypatch.setattr(mkt, "fetchrow", fake_fetchrow)
    return calls, fetch_response


def test_marketing_discover_leads_pulls_from_vertex_lead(patched_marketing_db):
    calls, fetch_response = patched_marketing_db
    fetch_response.extend([
        {"vertex_id": "lead:a.com", "company": "A Co", "domain": "a.com",
         "contact_name": None, "contact_email": None, "source": "manual",
         "source_url": "", "signal": "starred neo4j",
         "tech_stack": "neo4j", "employees": "20", "fit_score": 0,
         "reasoning": "", "outreach_status": "new"},
    ])
    out = asyncio.run(mkt._discover_leads({}))
    assert len(out["candidate_leads"]) == 1
    assert out["candidate_leads"][0]["domain"] == "a.com"
    # SQL should target the right table + LIMIT inlined as int.
    sql = calls["fetch"][0][0]
    assert "vertex_lead" in sql
    assert "LIMIT " in sql and "$" not in sql.split("LIMIT", 1)[1].split("\n")[0]


def test_marketing_enrich_lead_infers_tech(monkeypatch, patched_marketing_db):
    calls, _ = patched_marketing_db
    state = {"candidate_leads": [
        {"vertex_id": "lead:a.com", "company": "A", "domain": "a.com",
         "signal": "starred supabase and atproto repos", "tech_stack": ""},
    ]}
    out = asyncio.run(mkt._enrich_lead(state))
    enriched = out["enriched_leads"]
    assert len(enriched) == 1
    stack = enriched[0]["tech_stack"].split(",")
    assert "atproto" in stack and "supabase" in stack
    assert enriched[0]["segment"] == "dev-tooling-saas"
    # Should have UPDATEd vertex_lead.tech_stack
    assert any("UPDATE vertex_lead" in q for q, _ in calls["execute"])


def test_marketing_score_lead_uses_fallback_without_llm(monkeypatch, patched_marketing_db):
    monkeypatch.setattr(_llm, "_LLM_KEY", "")
    state = {"enriched_leads": [
        {"vertex_id": "lead:a.com", "company": "A", "domain": "a.com",
         "signal": "starred neo4j", "tech_stack": "neo4j,kysely",
         "segment": "dev-tooling-saas"},
    ]}
    out = asyncio.run(mkt._score_lead(state))
    assert len(out["scored"]) == 1
    assert 0 <= out["scored"][0]["fit_score"] <= 100
    assert "fallback-no-key" in out["score_source"]


def test_marketing_schedule_send_emits_queued_no_recipient(patched_marketing_db):
    calls, _ = patched_marketing_db
    state = {
        "iteration_id": "iter-1",
        "drafts": [
            {"vertex_id": "lead:a.com", "lead_domain": "a.com", "touch": 1,
             "subject": "yatabase × A", "body_text": "Hi", "body_html": "<p>Hi</p>",
             "segment": "dev-tooling-saas"},
        ],
        "candidate_leads": [], "enriched_leads": [], "scored": [], "handoffs": [],
    }
    out = asyncio.run(mkt._schedule_send(state))
    assert out["queued_count"] == 1
    inserts = [q for q, _ in calls["execute"] if "INSERT INTO vertex_email_outbox" in q]
    assert inserts, "expected one outbox insert"
    # Status must be queued-no-recipient (human gate)
    assert any("'queued-no-recipient'" in q for q, _ in calls["execute"])
    # Lead row should also be flipped to drafted.
    assert any("UPDATE vertex_lead" in q and "outreach_status = 'drafted'" in q
               for q, _ in calls["execute"])


# ---------------------------------------------------------------------------
# Sales graph — pure node behaviour.
# ---------------------------------------------------------------------------

class TestSalesPureNodes:
    def test_compute_health_zero_when_idle(self):
        out = sls._compute_health({"plan": "free", "usage_24h": {}, "usage_30d": {},
                                   "incident_count_24h": 0})
        # No momentum + no api → only base
        assert 0 <= out["health_score"] <= 50

    def test_compute_health_incident_penalises(self):
        # Same usage profile; the only delta is an incident in the last 24h.
        active = {"plan": "free", "usage_24h": {"api_request": 10},
                  "usage_30d": {"api_request": 300}, "incident_count_24h": 0}
        with_incident = dict(active, incident_count_24h=1)
        h_active = sls._compute_health(active)["health_score"]
        h_incident = sls._compute_health(with_incident)["health_score"]
        assert h_incident < h_active
        # Incident penalty is -25 in the function, bounded into [0, 100].
        assert h_active - h_incident >= 20

    def test_deterministic_policy_incident_first(self):
        d = sls._deterministic_policy({"incident_count_24h": 1, "plan": "free",
                                       "usage_24h": {}, "last_touch_at": None})
        assert d["decision"] == "do_nothing"
        assert "incident" in d["reasoning"]

    def test_deterministic_policy_rate_limit(self):
        # last_touch fresh (just now)
        from datetime import datetime, timezone
        recent = datetime.now(timezone.utc).isoformat()
        d = sls._deterministic_policy({"incident_count_24h": 0, "plan": "free",
                                       "usage_24h": {}, "last_touch_at": recent})
        assert d["decision"] == "do_nothing"
        assert "rate-limit" in d["reasoning"]

    def test_deterministic_policy_new_tenant_onboards(self):
        d = sls._deterministic_policy({"incident_count_24h": 0, "plan": "free",
                                       "usage_24h": {"api_request": 0},
                                       "last_touch_at": None})
        assert d["decision"] == "send_onboarding"

    def test_deterministic_policy_free_upgrade(self):
        d = sls._deterministic_policy({"incident_count_24h": 0, "plan": "free",
                                       "usage_24h": {"api_request": 900},
                                       "last_touch_at": None})
        assert d["decision"] == "send_upgrade"

    def test_deterministic_policy_paid_silent_escalates(self):
        # Established paid customer that's gone quiet — the policy's
        # send_onboarding branch must NOT fire (it requires no prior touch),
        # so we set last_touch_at to >7d ago to clear both rate-limit and
        # onboarding gates first.
        from datetime import datetime, timedelta, timezone
        stale = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
        d = sls._deterministic_policy({"incident_count_24h": 0, "plan": "starter",
                                       "usage_24h": {"api_request": 0},
                                       "last_touch_at": stale})
        assert d["decision"] == "escalate_human"


# ---------------------------------------------------------------------------
# Sales graph — DB-touching nodes (monkey-patched).
# ---------------------------------------------------------------------------

@pytest.fixture()
def patched_sales_db(monkeypatch):
    calls: dict = {"fetch": [], "fetchrow": [], "fetchval": [], "execute": []}
    fetch_results: dict[str, list[dict]] = {}
    fetchrow_results: dict[str, dict | None] = {}
    fetchval_results: dict[str, object] = {}

    async def fake_fetch(query, *args):
        calls["fetch"].append((query, args))
        for key, rows in fetch_results.items():
            if key in query:
                return list(rows)
        return []

    async def fake_fetchrow(query, *args):
        calls["fetchrow"].append((query, args))
        for key, row in fetchrow_results.items():
            if key in query:
                return row
        return None

    async def fake_fetchval(query, *args):
        calls["fetchval"].append((query, args))
        for key, val in fetchval_results.items():
            if key in query:
                return val
        return 0

    async def fake_execute(query, *args):
        calls["execute"].append((query, args))
        return "INSERT 0 1"

    monkeypatch.setattr(sls, "fetch", fake_fetch)
    monkeypatch.setattr(sls, "fetchrow", fake_fetchrow)
    monkeypatch.setattr(sls, "fetchval", fake_fetchval)
    monkeypatch.setattr(sls, "execute", fake_execute)
    return calls, fetch_results, fetchrow_results, fetchval_results


def test_sales_load_org_state_aggregates_metrics(patched_sales_db):
    calls, fetch_r, fetchrow_r, fetchval_r = patched_sales_db
    fetchrow_r["vertex_billing_org_plan"] = {
        "plan": "starter", "status": "active",
        "billing_period_start": "2026-05-01",
    }
    fetch_r["FROM vertex_billing_event"] = [
        {"metric": "api_request", "qty": 1234},
        {"metric": "storage_gb_hour", "qty": 12},
    ]
    fetchval_r["FROM vertex_audit_log"] = 0
    fetchrow_r["FROM vertex_email_outbox"] = None
    out = asyncio.run(sls._load_org_state({"org_did": "did:etzhayyim:org-1"}))
    assert out["plan"] == "starter"
    assert out["usage_24h"]["api_request"] == 1234
    assert out["incident_count_24h"] == 0


def test_sales_execute_action_writes_outbox_for_upgrade(monkeypatch, patched_sales_db):
    monkeypatch.setattr(_llm, "_LLM_KEY", "")  # force fallback
    calls, *_ = patched_sales_db
    state = {
        "iteration_id": "iter-x",
        "org_did": "did:etzhayyim:org-2",
        "decision": "send_upgrade",
        "decision_reasoning": "free plan at 900 api/day",
        "decision_source": "deterministic",
        "tenant_name": "Test Tenant",
        "usage_24h": {"api_request": 900},
    }
    out = asyncio.run(sls._execute_action(state))
    assert out["touchpoint_status"] == "queued-no-recipient"
    assert any("INSERT INTO vertex_email_outbox" in q for q, _ in calls["execute"])
    assert any("'queued-no-recipient'" in q for q, _ in calls["execute"])


def test_sales_execute_action_skips_on_do_nothing(patched_sales_db):
    calls, *_ = patched_sales_db
    out = asyncio.run(sls._execute_action({
        "iteration_id": "i", "org_did": "did:etzhayyim:o",
        "decision": "do_nothing", "decision_reasoning": "rate-limit"}))
    assert out["touchpoint_status"] == "skipped"
    assert not calls["execute"], "do_nothing must not touch outbox"


def test_sales_execute_action_escalate_emits_marker(patched_sales_db):
    calls, *_ = patched_sales_db
    out = asyncio.run(sls._execute_action({
        "iteration_id": "i", "org_did": "did:etzhayyim:o",
        "decision": "escalate_human", "decision_reasoning": "paid + silent"}))
    assert out["touchpoint_status"] == "queued-escalation"
    assert any("'sales-escalate-human'" in q for q, _ in calls["execute"])
