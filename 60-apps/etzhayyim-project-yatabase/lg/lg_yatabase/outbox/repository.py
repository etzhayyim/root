"""vertex_email_outbox repository — list pending drafts + targeted
UPDATEs by reviewers (approve / reject).

Reads stay over vertex_email_outbox directly (no MV). Writes are
narrow UPDATEs keyed by vertex_id (the marketing/sales graph composes
this as `marketing:{iter}:{domain}:t{n}` / `sales:{iter}:{org}:{decision}`).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from lg_yatabase.bmc.db import execute, fetch, fetchval

_log = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_LIST_COLUMNS = (
    "vertex_id, org_did, recipient_email, recipient_name, subject, "
    "body_text, body_html, kind, status, scheduled_at, sent_at, "
    "retry_count, last_error, created_at"
)


async def list_outbox(
    *,
    status: str | None,
    kind: str | None,
    limit: int,
) -> dict[str, Any]:
    """Return rows matching (status, kind). RW pgwire rejects parameterised
    LIMIT — we validate `limit` to an int constant and inline it.
    """
    cap = max(1, min(200, int(limit)))
    where_parts: list[str] = ["1=1"]
    args: list[Any] = []
    if status:
        args.append(status)
        where_parts.append(f"status = ${len(args)}")
    if kind:
        args.append(kind)
        where_parts.append(f"kind = ${len(args)}")

    where_sql = " AND ".join(where_parts)
    rows = await fetch(
        f"""
        SELECT {_LIST_COLUMNS}
          FROM vertex_email_outbox
         WHERE {where_sql}
         ORDER BY scheduled_at DESC
         LIMIT {cap}
        """,
        *args,
    )
    total = await fetchval(
        f"SELECT COUNT(*) FROM vertex_email_outbox WHERE {where_sql}",
        *args,
    ) or 0
    return {
        "rows": rows,
        "total": int(total),
        "offset": 0,
        "limit": cap,
    }


async def approve_outbox(payload: dict[str, Any]) -> dict[str, Any]:
    vertex_id = str(payload.get("vertex_id") or "").strip()
    recipient_email = str(payload.get("recipient_email") or "").strip()
    if not vertex_id:
        return {"ok": False, "vertex_id": vertex_id, "status": "error",
                "message": "vertex_id required"}
    if not _EMAIL_RE.match(recipient_email):
        return {"ok": False, "vertex_id": vertex_id, "status": "error",
                "message": f"invalid recipient_email: {recipient_email}"}

    recipient_name = str(payload.get("recipient_name") or "")[:200]
    body_text = payload.get("body_text")
    body_html = payload.get("body_html")
    subject = payload.get("subject")

    # Only update body fields when caller explicitly provided one;
    # otherwise preserve the graph-generated content.
    sets = [
        "recipient_email = $1",
        "recipient_name = $2",
        "status = 'queued'",
        "scheduled_at = $3",
        "last_error = ''",
    ]
    args: list[Any] = [recipient_email[:320], recipient_name, _now_iso()]
    if body_text is not None:
        args.append(str(body_text)[:32768])
        sets.append(f"body_text = ${len(args)}")
    if body_html is not None:
        args.append(str(body_html)[:32768])
        sets.append(f"body_html = ${len(args)}")
    if subject is not None:
        args.append(str(subject)[:512])
        sets.append(f"subject = ${len(args)}")
    args.append(vertex_id[:400])
    sets_sql = ", ".join(sets)
    sql = (
        f"UPDATE vertex_email_outbox SET {sets_sql} "
        f"WHERE vertex_id = ${len(args)} AND status = 'queued-no-recipient'"
    )
    await execute(sql, *args)

    # Read-back so the API contract returns the freshly-flipped status.
    rows = await fetch(
        "SELECT status FROM vertex_email_outbox WHERE vertex_id = $1 LIMIT 1",
        vertex_id,
    )
    new_status = str(rows[0].get("status")) if rows else "unknown"
    return {
        "ok": new_status == "queued",
        "vertex_id": vertex_id,
        "status": new_status,
        "message": (
            "approved — sender worker picks up on next tick."
            if new_status == "queued"
            else f"unchanged (current status: {new_status}); only queued-no-recipient rows can be approved."
        ),
    }


async def reject_outbox(payload: dict[str, Any]) -> dict[str, Any]:
    vertex_id = str(payload.get("vertex_id") or "").strip()
    reason = str(payload.get("reason") or "")[:512]
    if not vertex_id:
        return {"ok": False, "vertex_id": vertex_id, "status": "error",
                "message": "vertex_id required"}
    await execute(
        """
        UPDATE vertex_email_outbox
           SET status = 'rejected',
               last_error = $1,
               sent_at = $2
         WHERE vertex_id = $3 AND status IN ('queued-no-recipient', 'queued')
        """,
        reason or "rejected by reviewer", _now_iso(), vertex_id[:400],
    )
    rows = await fetch(
        "SELECT status FROM vertex_email_outbox WHERE vertex_id = $1 LIMIT 1",
        vertex_id,
    )
    new_status = str(rows[0].get("status")) if rows else "unknown"
    return {
        "ok": new_status == "rejected",
        "vertex_id": vertex_id,
        "status": new_status,
        "message": (
            f"rejected: {reason}"
            if new_status == "rejected"
            else f"unchanged (current status: {new_status})."
        ),
    }
