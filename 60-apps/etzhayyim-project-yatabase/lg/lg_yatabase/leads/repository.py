"""vertex_lead repository — read + targeted UPDATE writes.

Mirrors src/leads.ts row shape. Unlike vertex_bmc_* (record-log
append-only), vertex_lead is operator-state that transitions across
days, so we use UPDATE for status / contact_email / tech_stack /
outreach_outbox. INSERT remains idempotent via PK on vertex_id.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from lg_yatabase.bmc.db import execute, fetch, fetchrow

_log = logging.getLogger(__name__)


_VALID_DOMAIN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _vertex_id_for_domain(domain: str) -> str:
    cleaned = re.sub(r"[^a-z0-9.-]", "", domain.lower())
    return f"lead:{cleaned}"


async def ingest_lead(payload: dict[str, Any]) -> dict[str, Any]:
    """Insert a vertex_lead row. Idempotent unless force=True."""
    company = (payload.get("company") or "").strip()[:200]
    domain = (payload.get("domain") or "").strip().lower()[:200]
    if not company or not domain:
        return {"ok": False, "error": "BadRequest", "message": "company + domain required"}
    if not _VALID_DOMAIN.match(domain):
        return {"ok": False, "error": "BadRequest", "message": f"invalid domain: {domain}"}

    vertex_id = _vertex_id_for_domain(domain)
    force = bool(payload.get("force"))

    if not force:
        existing = await fetchrow(
            "SELECT outreach_status FROM vertex_lead WHERE vertex_id = $1 LIMIT 1",
            vertex_id,
        )
        if existing is not None:
            return {
                "ok": True,
                "vertex_id": vertex_id,
                "domain": domain,
                "outreach_status": existing["outreach_status"],
                "message": f"Lead already exists with outreach_status='{existing['outreach_status']}'; not re-ingested. Pass force:true to overwrite.",
            }

    tech_list = payload.get("tech_stack") or []
    tech_stack = ",".join(map(str, tech_list))[:1024] if isinstance(tech_list, list) else ""
    fit_score = payload.get("fit_score") or 0
    try:
        fit_score = max(0, min(100, int(fit_score)))
    except (TypeError, ValueError):
        fit_score = 0

    now_iso = _now_iso()
    await execute(
        """
        INSERT INTO vertex_lead (
            vertex_id, company, domain, contact_name, contact_email,
            source, source_url, signal, tech_stack, employees,
            fit_score, reasoning, outreach_status, outreach_outbox,
            last_touch_at, notes, ingested_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
            $11, $12, 'new', '', '', $13, $14, $14
        )
        """,
        vertex_id,
        company,
        domain,
        (payload.get("contact_name") or "")[:200],
        (payload.get("contact_email") or "")[:320],
        (payload.get("source") or "manual")[:64],
        (payload.get("source_url") or "")[:1024],
        (payload.get("signal") or "")[:1024],
        tech_stack,
        (payload.get("employees") or "")[:64],
        fit_score,
        (payload.get("reasoning") or "")[:2048],
        (payload.get("notes") or "")[:2048],
        now_iso,
    )
    return {
        "ok": True,
        "vertex_id": vertex_id,
        "domain": domain,
        "outreach_status": "new",
        "message": "Lead persisted; nishino will draft outreach on next /_agents/nishino/run.",
    }


_LIST_COLUMNS = (
    "vertex_id, company, domain, contact_email, source, signal, "
    "tech_stack, fit_score, outreach_status, outreach_outbox, "
    "last_touch_at, ingested_at, updated_at"
)


async def list_leads(*, status: str | None, domain: str | None, limit: int) -> dict[str, Any]:
    # RisingWave's pgwire rejects parameterized LIMIT ("non-const expression").
    # Validate limit to a clamped integer and inline it into the SQL.
    cap = max(1, min(200, int(limit)))
    if status and domain:
        rows = await fetch(
            f"SELECT {_LIST_COLUMNS} FROM vertex_lead "
            f"WHERE outreach_status = $1 AND domain = $2 "
            f"ORDER BY ingested_at DESC LIMIT {cap}",
            status, domain,
        )
    elif status:
        rows = await fetch(
            f"SELECT {_LIST_COLUMNS} FROM vertex_lead WHERE outreach_status = $1 "
            f"ORDER BY ingested_at DESC LIMIT {cap}",
            status,
        )
    elif domain:
        rows = await fetch(
            f"SELECT {_LIST_COLUMNS} FROM vertex_lead WHERE domain = $1 "
            f"ORDER BY ingested_at DESC LIMIT {cap}",
            domain,
        )
    else:
        rows = await fetch(
            f"SELECT {_LIST_COLUMNS} FROM vertex_lead "
            f"ORDER BY ingested_at DESC LIMIT {cap}"
        )
    return {"count": len(rows), "leads": rows}


async def get_lead_by_vertex_id(vertex_id: str) -> dict[str, Any] | None:
    row = await fetchrow(
        f"SELECT {_LIST_COLUMNS}, contact_name FROM vertex_lead "
        "WHERE vertex_id = $1 LIMIT 1",
        vertex_id,
    )
    return dict(row) if row else None


async def set_outreach_status(*, vertex_id: str, status: str) -> dict[str, Any]:
    now_iso = _now_iso()
    await execute(
        "UPDATE vertex_lead SET outreach_status = $1, last_touch_at = $2, updated_at = $2 "
        "WHERE vertex_id = $3",
        status, now_iso, vertex_id,
    )
    return {"ok": True, "vertex_id": vertex_id, "new_status": status}


async def set_contact_email(*, vertex_id: str, email: str) -> dict[str, Any]:
    trimmed = (email or "").strip()[:320]
    if trimmed and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", trimmed):
        return {"ok": False, "vertex_id": vertex_id, "contact_email": trimmed, "error": "invalid email format"}
    now_iso = _now_iso()
    await execute(
        "UPDATE vertex_lead SET contact_email = $1, updated_at = $2 WHERE vertex_id = $3",
        trimmed, now_iso, vertex_id,
    )
    return {"ok": True, "vertex_id": vertex_id, "contact_email": trimmed}


async def set_enrichment(
    *,
    vertex_id: str,
    contact_email: str | None = None,
    tech_stack: list[str] | None = None,
) -> dict[str, Any]:
    email = (contact_email or "").strip()[:320]
    tech = ",".join(map(str, tech_stack or []))[:1024]
    now_iso = _now_iso()
    await execute(
        "UPDATE vertex_lead SET contact_email = $1, tech_stack = $2, updated_at = $3 "
        "WHERE vertex_id = $4",
        email, tech, now_iso, vertex_id,
    )
    return {
        "ok": True,
        "vertex_id": vertex_id,
        "applied": {"contact_email": email, "tech_stack": tech},
    }


async def mark_drafted(*, vertex_id: str, outbox_id: str) -> dict[str, Any]:
    now_iso = _now_iso()
    await execute(
        "UPDATE vertex_lead SET outreach_status = 'drafted', outreach_outbox = $1, "
        "last_touch_at = $2, updated_at = $2 WHERE vertex_id = $3",
        outbox_id[:200], now_iso, vertex_id,
    )
    return {"ok": True}


async def leads_ready_for_outreach(limit: int) -> dict[str, Any]:
    cap = max(1, min(50, int(limit)))
    rows = await fetch(
        "SELECT vertex_id, company, domain, contact_email, signal, fit_score "
        "FROM vertex_lead WHERE outreach_status = 'new' "
        f"ORDER BY fit_score DESC, ingested_at ASC LIMIT {cap}"
    )
    return {"count": len(rows), "leads": rows}


async def leads_sendable(limit: int) -> dict[str, Any]:
    cap = max(1, min(200, int(limit)))
    rows = await fetch(
        f"SELECT {_LIST_COLUMNS} FROM vertex_lead "
        "WHERE outreach_status = 'approved' "
        "  AND contact_email IS NOT NULL AND contact_email <> '' "
        "  AND outreach_outbox IS NOT NULL AND outreach_outbox <> '' "
        f"ORDER BY fit_score DESC, ingested_at ASC LIMIT {cap}"
    )
    return {"count": len(rows), "leads": rows}


async def leads_needing_enrichment(limit: int) -> dict[str, Any]:
    cap = max(1, min(50, int(limit)))
    rows = await fetch(
        "SELECT vertex_id, domain FROM vertex_lead "
        "WHERE (contact_email IS NULL OR contact_email = '') "
        "  AND outreach_status IN ('new', 'drafted') "
        f"ORDER BY ingested_at ASC LIMIT {cap}"
    )
    return {"count": len(rows), "leads": rows}
