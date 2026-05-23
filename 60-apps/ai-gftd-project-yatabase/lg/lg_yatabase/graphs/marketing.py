"""yatabase `marketing` graph — top-of-funnel demand-gen for yatabase.etzhayyim.com.

Pipeline (LangGraph state-machine):

    discover_leads → enrich_lead → score_lead → route_by_score
                                                  │
                              ┌───────────────────┼───────────┐
                              ▼                   ▼           ▼
                       handoff_to_sales    draft_outreach   drop
                                                  │
                                                  ▼
                                          schedule_send
                                          (kind=marketing-outbound,
                                           status=queued-no-recipient — human gate)

ICP segments (initial):
  - dev-tooling-saas      — Supabase / Hasura / Neo4j users
  - data-team-mid-market  — 50-500 employee data teams
  - bsky-builders         — devs building on AT Protocol
  - jp-saas-founders      — JP-based SaaS startups

Compliance:
  - All `marketing-outbound` rows land with status='queued-no-recipient'
    until a human reviewer fills in the recipient and approves the draft.
    No cold email is sent automatically (CCPA §1798.120 / GDPR Art 6 /
    改正個人情報保護法 §17 / CAN-SPAM 16 CFR 316.5).
  - Lead enrichment uses only public-surface signal already in the row
    (no live scrape of LinkedIn, no purchased lists).
  - LLM scoring is optional augmentation; deterministic heuristic
    fallback is always available so cron stays green when the LLM
    pod is down.

TODO(substrate-boundary): replace RW queries (fetch from vertex_lead,
execute UPDATE/INSERT into vertex_lead/vertex_email_outbox) with e.read/e.write
per ADR-2605172000. Leads collection: 'ai.gftd.apps.yata.leads', rkey=company_domain.
Outbox: 'ai.gftd.apps.yata.outbox', rkey=timestamp_hash. Update after SDK types land.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch, fetchrow
from lg_yatabase.templates import (
    ICPSegment,
    classify_segment,
    marketing_touch,
)

from . import _llm as _llm

_log = logging.getLogger(__name__)


# Bounds — picked to keep one tick well inside the 6h cron + 30s pool
# command timeout while still covering a busy day's pipeline.
_DISCOVER_CAP = 50
_ENRICH_CAP = 50
_SCORE_CAP = 50
_DRAFT_CAP = 25


class Lead(TypedDict, total=False):
    vertex_id: str
    company: str
    domain: str
    contact_name: str | None
    contact_email: str | None
    source: str
    source_url: str
    signal: str
    tech_stack: str  # comma-separated (matches vertex_lead column)
    employees: str
    fit_score: int
    reasoning: str
    outreach_status: str
    segment: ICPSegment


class Draft(TypedDict, total=False):
    vertex_id: str
    lead_domain: str
    touch: int
    subject: str
    body_text: str
    body_html: str
    segment: ICPSegment


class _State(TypedDict, total=False):
    iteration_id: str
    started_at: int
    icp_segments: list[str]
    candidate_leads: list[Lead]
    enriched_leads: list[Lead]
    scored: list[Lead]
    handoffs: list[str]
    drafts: list[Draft]
    queued_count: int
    notes: str
    score_source: str  # "llm" / "fallback-no-key" / ...


# ── Helpers ─────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_TECH_STACK_HINTS = (
# CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
    "neo4j", "supabase", "hasura", "prisma", "drizzle", "kysely",
    "snowflake", "databricks", "dbt", "atproto", "bsky", "bluesky",
    "graphql", "postgres", "graph",
)


def _infer_tech_from_signal(signal: str) -> list[str]:
    """Pure heuristic: pull known tokens out of the lead's signal text."""
    s = (signal or "").lower()
    return sorted({tok for tok in _TECH_STACK_HINTS if tok in s})


# ── Nodes ───────────────────────────────────────────────────────────────


def _bootstrap(state: _State) -> _State:
    return {
        "iteration_id": uuid.uuid4().hex,
        "started_at": int(time.time() * 1000),
        "icp_segments": [
            "dev-tooling-saas",
            "data-team-mid-market",
            "bsky-builders",
            "jp-saas-founders",
        ],
        "candidate_leads": [],
        "enriched_leads": [],
        "scored": [],
        "handoffs": [],
        "drafts": [],
        "queued_count": 0,
        "score_source": "",
    }


async def _discover_leads(state: _State) -> _State:
    """Pull leads from vertex_lead that need a top-of-funnel pass.

    Priority order (oldest first within each bucket):
      1. outreach_status='new' (just ingested, never touched)
      2. outreach_status='drafted' (drafted but didn't progress)

    NOTE: RW rejects parameterised LIMIT — caller validates _DISCOVER_CAP
    to an int constant and inlines into the SQL.
    """
    cap = max(1, min(_DISCOVER_CAP, 200))
    try:
        rows = await fetch(
            f"""
            SELECT vertex_id, company, domain, contact_name, contact_email,
                   source, source_url, signal, tech_stack, employees,
                   fit_score, reasoning, outreach_status
              FROM vertex_lead
             WHERE outreach_status IN ('new', 'drafted')
             ORDER BY ingested_at ASC
             LIMIT {cap}
            """
        )
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[marketing.discover_leads] db error: %s", e)
        rows = []

    candidates: list[Lead] = [
        Lead(
            vertex_id=str(r.get("vertex_id") or ""),
            company=str(r.get("company") or ""),
            domain=str(r.get("domain") or ""),
            contact_name=r.get("contact_name"),
            contact_email=r.get("contact_email"),
            source=str(r.get("source") or ""),
            source_url=str(r.get("source_url") or ""),
            signal=str(r.get("signal") or ""),
            tech_stack=str(r.get("tech_stack") or ""),
            employees=str(r.get("employees") or ""),
            fit_score=int(r.get("fit_score") or 0),
            reasoning=str(r.get("reasoning") or ""),
            outreach_status=str(r.get("outreach_status") or ""),
        )
        for r in rows
    ]
    _log.info("[marketing.discover_leads] picked %d candidates", len(candidates))
    return {"candidate_leads": candidates}


async def _enrich_lead(state: _State) -> _State:
    """Cheap, public-surface enrichment.

    Source of truth = the row's existing `signal` text + `domain` TLD.
    We do NOT make live HTTP calls in the cron (deferred to a separate
    enrichment worker). What this node does:
      * tag tech_stack tokens inferred from signal
      * classify ICP segment
      * persist the enrichment (status: drafted → drafted, but tech_stack
        and segment-rich row is now ready for scoring)
    """
    enriched: list[Lead] = []
    for L in state.get("candidate_leads", [])[:_ENRICH_CAP]:
        signal = L.get("signal", "")
        existing_tech = [t.strip() for t in (L.get("tech_stack") or "").split(",") if t.strip()]
        inferred = _infer_tech_from_signal(signal)
        merged = sorted(set(existing_tech + inferred))
        L = dict(L)  # copy
        L["tech_stack"] = ",".join(merged)
        L["segment"] = classify_segment(L)  # type: ignore[typeddict-item]
        enriched.append(L)  # type: ignore[arg-type]

        if merged != existing_tech and L.get("vertex_id"):
            try:
                await execute(
                    "UPDATE vertex_lead SET tech_stack = $1, updated_at = $2 WHERE vertex_id = $3",
                    ",".join(merged)[:1024],
                    _now_iso(),
                    L["vertex_id"],
                )
            except Exception as e:                                       # noqa: BLE001
                _log.warning("[marketing.enrich_lead] update failed for %s: %s", L.get("vertex_id"), e)

    _log.info("[marketing.enrich_lead] enriched=%d", len(enriched))
    return {"enriched_leads": enriched}


async def _score_lead(state: _State) -> _State:
    """LLM-augmented fit scoring, deterministic fallback always available."""
    scored: list[Lead] = []
    sources: list[str] = []
    for L in state.get("enriched_leads", [])[:_SCORE_CAP]:
        segment = L.get("segment") or classify_segment(L)  # type: ignore[arg-type]
        result = _llm.score_lead(L, segment=segment)
        L = dict(L)
        L["fit_score"] = result.score
        L["reasoning"] = result.reasoning
        scored.append(L)  # type: ignore[arg-type]
        sources.append(result.source)

        if L.get("vertex_id"):
            try:
                await execute(
                    """
                    UPDATE vertex_lead
                       SET fit_score = $1, reasoning = $2, updated_at = $3
                     WHERE vertex_id = $4
                    """,
                    result.score, result.reasoning[:2048], _now_iso(), L["vertex_id"],
                )
            except Exception as e:                                       # noqa: BLE001
                _log.warning("[marketing.score_lead] update failed for %s: %s", L.get("vertex_id"), e)

    # Surface the dominant source so the audit log + ledger tell whether
    # this iteration was LLM-powered or fully deterministic.
    src_summary = ""
    if sources:
        from collections import Counter
        c = Counter(sources)
        src_summary = ",".join(f"{s}:{n}" for s, n in c.most_common(3))
    _log.info("[marketing.score_lead] scored=%d sources=[%s]", len(scored), src_summary)
    return {"scored": scored, "score_source": src_summary}


def _route_by_score(state: _State) -> _State:
    """Annotate state with handoffs (≥80) vs draft (50-79) vs drop (<50)."""
    handoffs = [
        L["domain"]
        for L in state.get("scored", [])
        if int(L.get("fit_score", 0)) >= 80 and L.get("domain")
    ]
    return {"handoffs": handoffs}


def _draft_outreach(state: _State) -> _State:
    """Build 3-touch deterministic drafts for warm leads (50-79).

    Hot leads (≥80) are handed off to sales — they get a different
    touchpoint shape and skip the marketing sequence. Cold leads (<50)
    are dropped (we re-evaluate next cron).
    """
    drafts: list[Draft] = []
    for L in state.get("scored", [])[:_DRAFT_CAP]:
        fit = int(L.get("fit_score", 0))
        if fit < 50 or fit >= 80:
            continue
        domain = (L.get("domain") or "").strip()
        company = (L.get("company") or "").strip() or domain
        segment: ICPSegment = L.get("segment") or "unknown"  # type: ignore[assignment]
        for touch in (1, 2, 3):
            body = marketing_touch(company, domain, segment, touch)
            drafts.append(Draft(
                vertex_id=L.get("vertex_id", ""),
                lead_domain=domain,
                touch=touch,
                subject=body.subject,
                body_text=body.body_text,
                body_html=body.body_html,
                segment=segment,
            ))
    _log.info("[marketing.draft_outreach] drafts=%d", len(drafts))
    return {"drafts": drafts}


async def _schedule_send(state: _State) -> _State:
    """Append drafted rows to vertex_email_outbox with status='queued-no-recipient'.

    Reviewer fills in `recipient_email` + `recipient_name` and flips
    status='queued' to make it eligible for the actual sender worker.
    """
    drafts = state.get("drafts", [])
    iteration_id = state.get("iteration_id", "")
    now = _now_iso()
    written = 0
    for d in drafts:
        outbox_id = f"marketing:{iteration_id}:{d.get('lead_domain', '')}:t{d.get('touch', 0)}"
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox (
                    vertex_id, org_did, recipient_email, recipient_name,
                    subject, body_text, body_html, kind, status,
                    scheduled_at, sent_at, retry_count, last_error, created_at
                ) VALUES (
                    $1, 'gftd', '', '', $2, $3, $4,
                    'marketing-outbound', 'queued-no-recipient',
                    $5, '', 0, '', $5
                )
                """,
                outbox_id[:400],
                str(d.get("subject", ""))[:512],
                str(d.get("body_text", ""))[:32768],
                str(d.get("body_html", ""))[:32768],
                now,
            )
            written += 1
        except Exception as e:                                       # noqa: BLE001
            _log.warning(
                "[marketing.schedule_send] insert failed for %s: %s",
                outbox_id, e,
            )
            continue

        # Mark lead as drafted so the next cron skips it unless reviewer
        # flips it back. INSERT vs UPDATE both idempotent.
        vid = d.get("vertex_id", "")
        if vid:
            try:
                await execute(
                    """
                    UPDATE vertex_lead
                       SET outreach_status = 'drafted',
                           outreach_outbox = $1,
                           updated_at = $2
                     WHERE vertex_id = $3
                       AND outreach_status IN ('new', 'drafted')
                    """,
                    outbox_id, now, vid,
                )
            except Exception as e:                                       # noqa: BLE001
                _log.warning(
                    "[marketing.schedule_send] lead update failed for %s: %s", vid, e,
                )

    _log.info("[marketing.schedule_send] outbox writes=%d / drafts=%d", written, len(drafts))
    return {
        "queued_count": written,
        "notes": (
            f"iteration_id={iteration_id} "
            f"discovered={len(state.get('candidate_leads', []))} "
            f"enriched={len(state.get('enriched_leads', []))} "
            f"scored={len(state.get('scored', []))} "
            f"handoffs={len(state.get('handoffs', []))} "
            f"queued_drafts={written} "
            f"score_source={state.get('score_source', '')} "
            f"(reviewer gate: status=queued-no-recipient)"
        ),
    }


# ── Graph wiring ────────────────────────────────────────────────────────

_g: StateGraph = StateGraph(_State)
_g.add_node("bootstrap", _bootstrap)
_g.add_node("discover_leads", _discover_leads)
_g.add_node("enrich_lead", _enrich_lead)
_g.add_node("score_lead", _score_lead)
_g.add_node("route_by_score", _route_by_score)
_g.add_node("draft_outreach", _draft_outreach)
_g.add_node("schedule_send", _schedule_send)

_g.add_edge(START, "bootstrap")
_g.add_edge("bootstrap", "discover_leads")
_g.add_edge("discover_leads", "enrich_lead")
_g.add_edge("enrich_lead", "score_lead")
_g.add_edge("score_lead", "route_by_score")
_g.add_edge("route_by_score", "draft_outreach")
_g.add_edge("draft_outreach", "schedule_send")
_g.add_edge("schedule_send", END)

GRAPH = _g.compile()
