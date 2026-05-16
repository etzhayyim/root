"""SES Phase 3 — Outlook 15-min cron pull via Microsoft Graph API (ADR-2605120000).

Differential fetch: reads last_sync_at cursor from vertex_m365_sync_state,
fetches messages received since that timestamp, runs each through the SES
LangGraph pipeline with source_kind='email_cron', then advances the cursor.
"""

from __future__ import annotations

import hashlib
import html
import logging
import re
import time
import uuid
from typing import Any

import httpx

from pymagatama.db_sync import sync_cursor

_log = logging.getLogger(__name__)

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
_DATA_KIND = "ses_email_cron"

# Fetch window floor when no cursor exists (ISO 8601 UTC)
_EPOCH_FLOOR = "2020-01-01T00:00:00Z"


def _sync_vid(upn: str, data_kind: str) -> str:
    return hashlib.sha256(f"{upn}|{data_kind}".encode()).hexdigest()[:16]


# ── auth ─────────────────────────────────────────────────────────────────────


def _acquire_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    url = _TOKEN_URL.format(tenant=tenant_id)
    resp = httpx.post(
        url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


# ── cursor ────────────────────────────────────────────────────────────────────


def _read_cursor(mailbox_upn: str) -> str | None:
    """Return ISO 8601 string of last_sync_at, or None if no row yet."""
    sql = (
        "SELECT last_sync_at FROM vertex_m365_sync_state "
        "WHERE upn = %s AND data_kind = %s LIMIT 1"
    )
    with sync_cursor() as cur:
        cur.execute(sql, (mailbox_upn, _DATA_KIND))
        row = cur.fetchone()
    if row is None:
        return None
    val = row[0]
    return str(val) if val is not None else None


def _upsert_cursor(
    mailbox_upn: str,
    last_sync_at: str,
    record_count: int,
    run_id: str,
) -> None:
    check_sql = (
        "SELECT 1 FROM vertex_m365_sync_state "
        "WHERE upn = %s AND data_kind = %s LIMIT 1"
    )
    insert_sql = (
        "INSERT INTO vertex_m365_sync_state "
        "(vertex_id, upn, data_kind, last_sync_at, record_count, run_id, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, 'ok')"
    )
    update_sql = (
        "UPDATE vertex_m365_sync_state "
        "SET last_sync_at = %s, record_count = record_count + %s, "
        "run_id = %s, status = 'ok', last_error = NULL "
        "WHERE upn = %s AND data_kind = %s"
    )
    with sync_cursor() as cur:
        cur.execute(check_sql, (mailbox_upn, _DATA_KIND))
        exists = cur.fetchone() is not None
        if exists:
            cur.execute(update_sql, (last_sync_at, record_count, run_id, mailbox_upn, _DATA_KIND))
        else:
            vid = _sync_vid(mailbox_upn, _DATA_KIND)
            cur.execute(insert_sql, (vid, mailbox_upn, _DATA_KIND, last_sync_at, record_count, run_id))


def _write_cursor_error(mailbox_upn: str, error: str, run_id: str) -> None:
    check_sql = (
        "SELECT 1 FROM vertex_m365_sync_state "
        "WHERE upn = %s AND data_kind = %s LIMIT 1"
    )
    insert_sql = (
        "INSERT INTO vertex_m365_sync_state "
        "(vertex_id, upn, data_kind, last_sync_at, error_count, last_error, run_id, status) "
        "VALUES (%s, %s, %s, %s, 1, %s, %s, 'error')"
    )
    update_sql = (
        "UPDATE vertex_m365_sync_state "
        "SET error_count = error_count + 1, last_error = %s, "
        "run_id = %s, status = 'error' "
        "WHERE upn = %s AND data_kind = %s"
    )
    with sync_cursor() as cur:
        cur.execute(check_sql, (mailbox_upn, _DATA_KIND))
        exists = cur.fetchone() is not None
        error_truncated = error[:500]
        if exists:
            cur.execute(update_sql, (error_truncated, run_id, mailbox_upn, _DATA_KIND))
        else:
            vid = _sync_vid(mailbox_upn, _DATA_KIND)
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cur.execute(insert_sql, (vid, mailbox_upn, _DATA_KIND, now, error_truncated, run_id))


# ── graph api ─────────────────────────────────────────────────────────────────


def _fetch_messages(
    token: str,
    mailbox_upn: str,
    since_iso: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Fetch inbox messages received after since_iso, oldest-first, up to page_size."""
    params = {
        "$filter": f"receivedDateTime ge {since_iso}",
        "$orderby": "receivedDateTime asc",
        "$top": str(page_size),
        "$select": "id,subject,from,receivedDateTime,body",
    }
    url = f"{_GRAPH_BASE}/users/{mailbox_upn}/mailFolders/Inbox/messages"
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return list(resp.json().get("value", []))


# ── text extraction ───────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _html_to_text(raw: str) -> str:
    unescaped = html.unescape(raw)
    no_tags = _TAG_RE.sub(" ", unescaped)
    return _WS_RE.sub(" ", no_tags).strip()


def _message_to_text(msg: dict[str, Any]) -> str:
    subject = msg.get("subject") or ""
    sender = (msg.get("from") or {}).get("emailAddress", {}).get("address", "")
    body_raw = (msg.get("body") or {}).get("content", "")
    body_type = (msg.get("body") or {}).get("contentType", "text")
    body_text = _html_to_text(body_raw) if body_type == "html" else body_raw.strip()
    lines = [f"件名: {subject}", f"差出人: {sender}", "", body_text]
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────


async def run_outlook_pull(
    graph: Any,
    *,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    mailbox_upn: str,
    actor_did: str,
    org_did: str,
) -> dict[str, Any]:
    """Differential fetch + SES pipeline. Returns summary dict."""
    run_id = str(uuid.uuid4())
    started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _log.info("[outlook-pull][%s] start mailbox=%s", run_id, mailbox_upn)

    # Read cursor
    cursor = _read_cursor(mailbox_upn) or _EPOCH_FLOOR
    _log.info("[outlook-pull][%s] cursor=%s", run_id, cursor)

    # Acquire token
    try:
        token = _acquire_token(tenant_id, client_id, client_secret)
    except Exception as exc:
        _log.error("[outlook-pull][%s] token error: %s", run_id, exc)
        _write_cursor_error(mailbox_upn, f"token: {exc}", run_id)
        return {"ok": False, "error": f"token: {exc}", "run_id": run_id}

    # Fetch messages
    try:
        messages = _fetch_messages(token, mailbox_upn, cursor)
    except Exception as exc:
        _log.error("[outlook-pull][%s] fetch error: %s", run_id, exc)
        _write_cursor_error(mailbox_upn, f"fetch: {exc}", run_id)
        return {"ok": False, "error": f"fetch: {exc}", "run_id": run_id}

    _log.info("[outlook-pull][%s] fetched %d messages", run_id, len(messages))

    if not messages:
        _upsert_cursor(mailbox_upn, cursor, 0, run_id)
        return {"ok": True, "fetched": 0, "processed": 0, "run_id": run_id}

    # Process each message through SES graph
    processed = 0
    errors = 0
    last_received_at = cursor

    for msg in messages:
        msg_id = msg.get("id", "")
        received_at = msg.get("receivedDateTime", "")
        subject = msg.get("subject") or ""
        sender = (msg.get("from") or {}).get("emailAddress", {}).get("address", "")

        raw_text = _message_to_text(msg)
        child_run_id = str(uuid.uuid4())

        inp = {
            "source_kind": "email_cron",
            "raw_text": raw_text,
            "actor_did": actor_did,
            "org_did": org_did,
            "run_id": child_run_id,
            "started_at": started_at,
            "source_email_subject": subject[:300] if subject else None,
            "source_email_from": sender[:200] if sender else None,
        }

        try:
            result = await graph.ainvoke(inp)
            status = getattr(result, "status", None)
            if hasattr(status, "value"):
                status = status.value
            _log.info(
                "[outlook-pull][%s] msg=%s status=%s",
                run_id, msg_id[:16], status,
            )
            processed += 1
        except Exception as exc:
            _log.error("[outlook-pull][%s] graph error msg=%s: %s", run_id, msg_id[:16], exc)
            errors += 1

        # Advance watermark to the latest receivedDateTime we touched
        if received_at and received_at > last_received_at:
            last_received_at = received_at

    # Advance cursor to just past the last processed message
    _upsert_cursor(mailbox_upn, last_received_at, processed, run_id)

    return {
        "ok": True,
        "fetched": len(messages),
        "processed": processed,
        "errors": errors,
        "cursor_advanced_to": last_received_at,
        "run_id": run_id,
    }
