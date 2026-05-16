"""Outlook triage analytics helpers.

Runs lightweight COUNT/GROUP BY queries against the triage tables.
All queries use LIMIT to stay within RisingWave safe read paths.
"""

from __future__ import annotations

import time
from typing import Any

from pymagatama.db_sync import sync_cursor


def _cutoff_iso(days: int) -> str:
    ts = time.gmtime(time.time() - days * 86400)
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", ts)


def get_triage_stats(days: int = 30) -> dict[str, Any]:
    """COUNT triage_classification from vertex_email_message (last N days)."""
    cutoff = _cutoff_iso(days)
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT triage_classification, COUNT(*) AS cnt
            FROM vertex_email_message
            WHERE triaged_at >= %s
            GROUP BY triage_classification
            LIMIT 20
            """,
            (cutoff,),
        )
        rows = cur.fetchall() or []
    return {str(r[0] or "unknown"): int(r[1]) for r in rows}


def get_gray_queue_stats() -> dict[str, Any]:
    """COUNT status/verdict breakdown from vertex_email_gray_queue."""
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT status, verdict, COUNT(*) AS cnt
            FROM vertex_email_gray_queue
            GROUP BY status, verdict
            LIMIT 30
            """,
        )
        rows = cur.fetchall() or []
    result: dict[str, Any] = {"pending": 0, "resolved": {}, "skipped": 0}
    for status, verdict, cnt in rows:
        cnt = int(cnt)
        status = str(status or "")
        verdict = str(verdict or "")
        if status == "pending":
            result["pending"] = result.get("pending", 0) + cnt
        elif status == "skipped":
            result["skipped"] = result.get("skipped", 0) + cnt
        elif status == "resolved":
            resolved = result.setdefault("resolved", {})
            resolved[verdict or "unknown"] = resolved.get(verdict or "unknown", 0) + cnt
    return result


def get_draft_stats() -> dict[str, Any]:
    """COUNT status/action breakdown from vertex_email_reply_draft."""
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT status, action, COUNT(*) AS cnt
            FROM vertex_email_reply_draft
            GROUP BY status, action
            LIMIT 30
            """,
        )
        rows = cur.fetchall() or []
    result: dict[str, Any] = {"pending": 0, "approved": {}, "discarded": 0}
    for status, action, cnt in rows:
        cnt = int(cnt)
        status = str(status or "")
        action = str(action or "")
        if status == "pending":
            result["pending"] = result.get("pending", 0) + cnt
        elif status == "discarded":
            result["discarded"] = result.get("discarded", 0) + cnt
        elif status == "approved":
            approved = result.setdefault("approved", {})
            approved[action or "approve"] = approved.get(action or "approve", 0) + cnt
    return result


def get_feedback_stats(days: int = 90) -> dict[str, Any]:
    """COUNT verdict from vertex_email_triage_feedback (last N days)."""
    cutoff = _cutoff_iso(days)
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT verdict, COUNT(*) AS cnt
            FROM vertex_email_triage_feedback
            WHERE created_at >= %s
            GROUP BY verdict
            LIMIT 10
            """,
            (cutoff,),
        )
        rows = cur.fetchall() or []
    return {str(r[0] or "unknown"): int(r[1]) for r in rows}


def get_all_stats(days: int = 30) -> dict[str, Any]:
    """Aggregate all stats into a single response dict."""
    result: dict[str, Any] = {"days": days, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        result["triage"] = get_triage_stats(days)
    except Exception as e:
        result["triage"] = {"error": str(e)[:120]}
    try:
        result["gray_queue"] = get_gray_queue_stats()
    except Exception as e:
        result["gray_queue"] = {"error": str(e)[:120]}
    try:
        result["drafts"] = get_draft_stats()
    except Exception as e:
        result["drafts"] = {"error": str(e)[:120]}
    try:
        result["feedback"] = get_feedback_stats(days)
    except Exception as e:
        result["feedback"] = {"error": str(e)[:120]}
    return result


__all__ = ["get_all_stats"]
