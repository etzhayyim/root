"""yatabase BMC autonomous strategy agent — daily cron graph.

Runs daily at 09:03 JST via APScheduler (registered in server.py).
Checks pipeline health and notifies Jun via Teams webhook.

Pipeline:
    check_outbox → check_sprint → assess_state → notify → done

Notification channel priority:
  1. TEAMS_BMC_WEBHOOK_URL env var (Teams incoming webhook)
  2. vertex_email_outbox with kind='bmc-daily-report' (Studio visible)

Env vars:
  TEAMS_BMC_WEBHOOK_URL  — Teams incoming webhook URL (optional)
  etzhayyim_LLM_URL / etzhayyim_LLM_API_KEY — for LLM-augmented assessment (optional)
  BMC_H1_SUBMITTED       — "true" when Cursor MCP registry PR submitted
  BMC_H2_VERIFIED        — "true" when LP 7-day metrics verified
  BMC_H3_DECIDED         — "true" when /storage page decision made
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date, datetime, timezone
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch, fetchval

from . import _llm

_log = logging.getLogger(__name__)

TODAY = date.today  # called at runtime, not import time


# ── State ─────────────────────────────────────────────────────────────────────

class BmcAgentState(TypedDict, total=False):
    run_date: str                    # YYYY-MM-DD
    outbox_stats: dict[str, int]     # status → count
    pipeline_stuck: bool             # any item queued-no-recipient > 48h
    h1_submitted: bool               # Cursor MCP registry PR submitted
    h2_gate: bool                    # today >= 2026-05-28
    h2_verified: bool
    h3_decided: bool
    is_monday: bool
    priority_action: str
    summary: str
    notified: bool


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def check_outbox(state: BmcAgentState) -> BmcAgentState:
    today_str = TODAY().isoformat()
    stats: dict[str, int] = {}
    stuck = False
    try:
        rows = await fetch(
            """
            SELECT status, COUNT(*) AS cnt
            FROM vertex_email_outbox
            GROUP BY status
            LIMIT 20
            """
        )
        for r in rows:
            stats[r["status"]] = int(r["cnt"])

        # Stuck = queued-no-recipient items older than 48h
        stuck_count = await fetchval(
            """
            SELECT COUNT(*) FROM vertex_email_outbox
            WHERE status = 'queued-no-recipient'
              AND created_at < NOW() - INTERVAL '48 hours'
            """
        )
        stuck = (stuck_count or 0) > 0
    except Exception as e:
        _log.warning("[bmc_agent] outbox query failed: %s", e)
        stats = {"_error": 1}

    return {**state, "run_date": today_str, "outbox_stats": stats, "pipeline_stuck": stuck}


async def check_sprint(state: BmcAgentState) -> BmcAgentState:
    today = TODAY()
    return {
        **state,
        "h1_submitted": os.environ.get("BMC_H1_SUBMITTED", "").lower() == "true",
        "h2_gate": today >= date(2026, 5, 28),
        "h2_verified": os.environ.get("BMC_H2_VERIFIED", "").lower() == "true",
        "h3_decided": os.environ.get("BMC_H3_DECIDED", "").lower() == "true",
        "is_monday": today.weekday() == 0,
    }


async def assess_state(state: BmcAgentState) -> BmcAgentState:
    # Deterministic priority logic
    pending_nr = state.get("outbox_stats", {}).get("queued-no-recipient", 0)
    stuck = state.get("pipeline_stuck", False)

    if stuck:
        priority = "URGENT: outbox stuck >48h — approve or reject items in /studio/admin/outbox"
    elif not state.get("h1_submitted"):
        priority = "H1: Cursor MCP registry PR not yet submitted — submit today"
    elif state.get("h2_gate") and not state.get("h2_verified"):
        priority = "H2: LP 7日経過 — CF Analytics で bounce rate / time-on-page を確認してください"
    elif state.get("h2_gate") and not state.get("h3_decided"):
        priority = "H3: /storage page 判断 — organic traffic 50% 閾値を確認してください"
    elif state.get("is_monday"):
        priority = "週次: Pro tier 契約数を確認 (BEP=9件)"
    elif pending_nr > 0:
        priority = f"outbox: {pending_nr}件の承認待ちリードがあります → /studio/admin/outbox"
    else:
        priority = "異常なし — marketing/sales cron が自律運転中"

    # Optional LLM augmentation (sync call — _llm uses urllib, not async)
    llm_note = ""
    try:
        prompt = (
            f"yatabase BMC daily. outbox={json.dumps(state.get('outbox_stats', {}), default=str)}. "
            f"priority={priority}. "
            "One concise strategic observation ≤80 chars (Japanese OK). "
            'JSON: {"note": "..."}'
        )
        parsed, source = _llm.call_llm_json(prompt, max_tokens=100)
        if parsed and source == "llm":
            llm_note = f" | {str(parsed.get('note', ''))[:80]}"
    except Exception:
        pass

    outbox_stats = state.get("outbox_stats", {})
    sent = outbox_stats.get("sent", 0)
    queued = outbox_stats.get("queued", 0)
    run_date = state.get("run_date", date.today().isoformat())

    summary = (
        f"[{run_date}] outbox承認待ち:{pending_nr}件 sent:{sent} queued:{queued} "
        f"| H1:{'✅' if state.get('h1_submitted') else '⏳'} "
        f"H2:{'✅' if state.get('h2_verified') else ('🔔' if state.get('h2_gate') else '⏳')} "
        f"H3:{'✅' if state.get('h3_decided') else ('🔔' if state.get('h2_gate') else '⏳')} "
        f"| {priority}{llm_note}"
    )

    return {**state, "priority_action": priority, "summary": summary}


async def notify(state: BmcAgentState) -> BmcAgentState:
    summary = state.get("summary", "")
    notified = False

    # 1. Teams incoming webhook
    webhook_url = os.environ.get("TEAMS_BMC_WEBHOOK_URL", "")
    if webhook_url:
        try:
            payload = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [{
                            "type": "TextBlock",
                            "text": "yatabase BMC Daily",
                            "weight": "Bolder",
                            "size": "Medium",
                        }, {
                            "type": "TextBlock",
                            "text": summary,
                            "wrap": True,
                        }],
                    },
                }],
            }
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(webhook_url, json=payload)
                r.raise_for_status()
            notified = True
            _log.info("[bmc_agent] Teams notification sent")
        except Exception as e:
            _log.warning("[bmc_agent] Teams webhook failed: %s", e)

    # 2. Fallback: vertex_email_outbox as internal bmc-daily-report
    if not notified:
        run_date = state.get("run_date", date.today().isoformat())
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox
                  (vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                str(uuid.uuid4()),
                "did:plc:yatabase-bmc-agent",
                "bmc-daily-report",
                f"yatabase BMC Daily {run_date}",
                summary,
                "jun@etzhayyim.com",
                "queued-no-recipient",
                datetime.now(timezone.utc),
            )
            notified = True
            _log.info("[bmc_agent] summary written to outbox")
        except Exception as e:
            _log.warning("[bmc_agent] outbox insert failed: %s", e)

    _log.info("[bmc_agent] %s", summary)
    return {**state, "notified": notified}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(BmcAgentState)
    sg.add_node("check_outbox", check_outbox)
    sg.add_node("check_sprint", check_sprint)
    sg.add_node("assess_state", assess_state)
    sg.add_node("notify", notify)
    sg.add_edge(START, "check_outbox")
    sg.add_edge("check_outbox", "check_sprint")
    sg.add_edge("check_sprint", "assess_state")
    sg.add_edge("assess_state", "notify")
    sg.add_edge("notify", END)
    return sg.compile()


GRAPH = _build()
