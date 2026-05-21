"""yatabase Email Sender — outbox drain via Resend API.

Runs every 5 minutes via APScheduler (registered in server.py).
Fetches up to 20 status='queued' rows from vertex_email_outbox,
sends each via Resend, then marks sent/failed.

Env: RESEND_API_KEY — Resend v1 key (re_...).
     RESEND_FROM    — sender address (default: yatabase@gftd.ai)

Pipeline: fetch_queued → send_batch → report
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch

_log = logging.getLogger(__name__)

_RESEND_URL = "https://api.resend.com/emails"
_FROM_DEFAULT = "yatabase <yatabase@gftd.ai>"
_BATCH_LIMIT = 20


# ── State ─────────────────────────────────────────────────────────────────────

class EmailSenderState(TypedDict, total=False):
    queued: list[dict]
    sent: int
    failed: int
    skipped: int
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def fetch_queued(state: EmailSenderState) -> EmailSenderState:
    rows: list[dict] = []
    try:
        rows_raw = await fetch(
            """
            SELECT vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status
            FROM vertex_email_outbox
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT $1
            """,
            _BATCH_LIMIT,
        )
        rows = [dict(r) for r in rows_raw]
    except Exception as e:
        _log.warning("[email_sender] fetch_queued failed: %s", e)
    _log.info("[email_sender] fetched %d queued rows", len(rows))
    return {**state, "queued": rows}


async def send_batch(state: EmailSenderState) -> EmailSenderState:
    api_key = os.environ.get("RESEND_API_KEY", "")
    from_addr = os.environ.get("RESEND_FROM", _FROM_DEFAULT)
    sent = 0
    failed = 0
    skipped = 0

    if not api_key:
        _log.warning("[email_sender] RESEND_API_KEY not set — skipping send")
        return {**state, "sent": 0, "failed": 0, "skipped": len(state.get("queued") or [])}

    async with httpx.AsyncClient(timeout=15) as client:
        for row in (state.get("queued") or []):
            vid = row.get("vertex_id", "")
            to_email = (row.get("recipient_email") or "").strip()

            if not to_email or "@" not in to_email:
                skipped += 1
                _log.debug("[email_sender] skip %s — no valid recipient", vid[:32])
                continue

            try:
                resp = await client.post(
                    _RESEND_URL,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "from": from_addr,
                        "to": [to_email],
                        "subject": row.get("subject", ""),
                        "text": row.get("body_text", ""),
                    },
                )
                if resp.status_code in (200, 201):
                    resend_id = resp.json().get("id", "")
                    await execute(
                        """
                        UPDATE vertex_email_outbox
                        SET status = 'sent',
                            sent_at = $2,
                            last_error = $3
                        WHERE vertex_id = $1
                        """,
                        vid,
                        datetime.now(timezone.utc),
                        resend_id,
                    )
                    sent += 1
                    _log.info("[email_sender] sent %s → %s (resend=%s)", vid[:24], to_email, resend_id)
                else:
                    err = resp.text[:200]
                    await _mark_failed(vid, f"HTTP {resp.status_code}: {err}")
                    failed += 1
                    _log.warning("[email_sender] send failed %s: %s", vid[:24], err)
            except Exception as e:
                await _mark_failed(vid, str(e)[:200])
                failed += 1
                _log.warning("[email_sender] send error %s: %s", vid[:24], e)

    return {**state, "sent": sent, "failed": failed, "skipped": skipped}


async def _mark_failed(vertex_id: str, error: str) -> None:
    try:
        await execute(
            """
            UPDATE vertex_email_outbox
            SET status = 'failed', last_error = $2
            WHERE vertex_id = $1
            """,
            vertex_id,
            error,
        )
    except Exception as e:
        _log.warning("[email_sender] mark_failed DB error: %s", e)


async def report(state: EmailSenderState) -> EmailSenderState:
    total = len(state.get("queued") or [])
    sent = state.get("sent", 0)
    failed = state.get("failed", 0)
    skipped = state.get("skipped", 0)
    summary = f"email_sender: queued={total} sent={sent} failed={failed} skipped={skipped}"
    _log.info("[email_sender] %s", summary)
    return {**state, "summary": summary}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(EmailSenderState)
    sg.add_node("fetch_queued", fetch_queued)
    sg.add_node("send_batch", send_batch)
    sg.add_node("report", report)
    sg.add_edge(START, "fetch_queued")
    sg.add_edge("fetch_queued", "send_batch")
    sg.add_edge("send_batch", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
