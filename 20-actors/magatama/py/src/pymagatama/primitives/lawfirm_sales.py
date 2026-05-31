"""
lawfirm.sales.* + lawfirm.mail.replyWebhook — LangServer handlers.

Task types:
  lawfirm.mail.replyWebhook        Match incoming mail reply → outreach event + stage advance
  lawfirm.sales.pipelineTransition Update lead stage with audit row
  lawfirm.sales.recordOutreach     Record outbound touchpoint manually

ADR-0036 Hyperdrive direct.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import uuid
from typing import Any

LOG = logging.getLogger("lawfirm.sales")

_FIRM_DID = "did:web:lawfirm.etzhayyim.com"


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d %H:%M:%S")

def _vid(kind: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    return f"at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.lawfirm.{kind}/{stamp}-{uuid.uuid4().hex[:8]}"


def _execute(sql_str: str, params: dict) -> bool:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_rowcount
        sa_rowcount(text(sql_str), params)
        return True
    except Exception as exc:
        LOG.warning("execute failed: %s", exc)
        return False

def _query(sql_str: str, params: dict | None = None) -> list[dict]:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_query
        return sa_query(text(sql_str), params or {})
    except Exception as exc:
        LOG.warning("query failed: %s", exc)
        return []


# ── Stage advance map ────────────────────────────────────────────────────────

_STAGE_ON_REPLY = {
    "lead":              "contacted",   # never possible (reply requires outbound first)
    "contacted":         "engaged",
    "engaged":           "engaged",     # idempotent
    "meeting_requested": "meeting_set",
    "meeting_set":       "meeting_set",
    "pilot":             "pilot",
    "paid":              "paid",
}


# ── Task: lawfirm.mail.replyWebhook ──────────────────────────────────────────

async def task_lawfirm_mail_reply_webhook(
    message_id: str = "",
    in_reply_to: str = "",
    from_email: str = "",
    from_name: str = "",
    to_emails: list[str] | None = None,
    subject: str = "",
    body_preview: str = "",
    received_at: str = "",
    graph_event_id: str = "",
    raw_headers: str = "",
) -> dict:
    """Match incoming reply to a tracked lead, persist event, advance stage."""
    if not from_email:
        return {"ok": False, "error": "from_email required"}

    # Idempotency check
    if graph_event_id:
        dup = _query(
            "SELECT vertex_id FROM vertex_lawfirm_outreach_event "
            "WHERE asset_uri = :gid LIMIT 1",
            {"gid": f"graph://{graph_event_id}"},
        )
        if dup:
            return {"ok": True, "matched_lead_id": "", "stage_advanced": False, "duplicate": True}

    # Match strategy: domain → target_email substring → subject keyword
    domain = from_email.split("@")[-1].lower() if "@" in from_email else ""

    rows = _query(
        "SELECT lead_id, stage FROM vertex_lawfirm_lead "
        "WHERE LOWER(target_email) LIKE :pat OR LOWER(target_name) LIKE :npat "
        "LIMIT 5",
        {"pat": f"%{domain}%", "npat": f"%{domain.split('.')[0]}%"},
    )
    matched_lead_id = ""
    matched_stage = ""
    if rows:
        matched_lead_id = rows[0]["lead_id"]
        matched_stage = rows[0]["stage"]

    # Persist inbound outreach event
    event_uri = _vid("outreachEvent")
    _execute(
        "INSERT INTO vertex_lawfirm_outreach_event "
        "(vertex_id, lead_id, event_kind, channel, direction, subject, "
        " body_preview, asset_uri, occurred_at, actor_did, created_at, owner_did) "
        "VALUES (:vid, :lid, 'reply_received', 'email', 'in', :subj, "
        " :body, :asset, :occ, :actor, :now, :owner)",
        {
            "vid":   event_uri,
            "lid":   matched_lead_id,
            "subj":  subject[:500],
            "body":  body_preview[:1500],
            "asset": f"graph://{graph_event_id}" if graph_event_id else "",
            "occ":   received_at or _now_iso(),
            "actor": from_email,
            "now":   _now_iso(),
            "owner": _FIRM_DID,
        },
    )

    stage_advanced = False
    new_stage = matched_stage
    if matched_lead_id and matched_stage in _STAGE_ON_REPLY:
        nxt = _STAGE_ON_REPLY[matched_stage]
        if nxt != matched_stage:
            _execute(
                "UPDATE vertex_lawfirm_lead "
                "SET stage = :s, last_reply_at = :now, last_touch_at = :now "
                "WHERE lead_id = :lid",
                {"s": nxt, "now": _now_iso(), "lid": matched_lead_id},
            )
            _execute(
                "INSERT INTO vertex_lawfirm_pipeline_stage "
                "(vertex_id, lead_id, from_stage, to_stage, transitioned_at, "
                " reason, decided_by_did, created_at, owner_did) "
                "VALUES (:vid, :lid, :from, :to, :now, 'mail_reply_received', "
                " :actor, :now, :owner)",
                {
                    "vid":   _vid("pipelineStage"),
                    "lid":   matched_lead_id,
                    "from":  matched_stage,
                    "to":    nxt,
                    "now":   _now_iso(),
                    "actor": from_email,
                    "owner": _FIRM_DID,
                },
            )
            stage_advanced = True
            new_stage = nxt

    LOG.info(
        "mail reply matched lead=%s domain=%s advanced=%s new_stage=%s",
        matched_lead_id, domain, stage_advanced, new_stage,
    )
    return {
        "ok":                  True,
        "matched_lead_id":     matched_lead_id,
        "outreach_event_uri":  event_uri,
        "stage_advanced":      stage_advanced,
        "new_stage":           new_stage,
    }


# ── Task: lawfirm.sales.pipelineTransition ───────────────────────────────────

_VALID_STAGES = {
    "lead", "contacted", "engaged", "meeting_requested", "meeting_set",
    "demo", "pilot", "paid", "lost", "declined_conflict",
}


async def task_lawfirm_pipeline_transition(
    lead_id: str = "",
    to_stage: str = "",
    reason: str = "",
    decided_by_did: str = "",
) -> dict:
    if not lead_id or to_stage not in _VALID_STAGES:
        return {"ok": False, "error": f"invalid lead_id or stage: {to_stage!r}"}

    cur = _query(
        "SELECT stage FROM vertex_lawfirm_lead WHERE lead_id = :lid LIMIT 1",
        {"lid": lead_id},
    )
    if not cur:
        return {"ok": False, "error": f"lead not found: {lead_id}"}
    from_stage = cur[0]["stage"]

    _execute(
        "UPDATE vertex_lawfirm_lead SET stage = :s, last_touch_at = :now WHERE lead_id = :lid",
        {"s": to_stage, "now": _now_iso(), "lid": lead_id},
    )
    _execute(
        "INSERT INTO vertex_lawfirm_pipeline_stage "
        "(vertex_id, lead_id, from_stage, to_stage, transitioned_at, "
        " reason, decided_by_did, created_at, owner_did) "
        "VALUES (:vid, :lid, :from, :to, :now, :reason, :dec, :now, :owner)",
        {
            "vid":    _vid("pipelineStage"),
            "lid":    lead_id,
            "from":   from_stage,
            "to":     to_stage,
            "now":    _now_iso(),
            "reason": reason[:500],
            "dec":    decided_by_did or _FIRM_DID,
            "owner":  _FIRM_DID,
        },
    )
    LOG.info("pipeline transition lead=%s %s → %s by %s", lead_id, from_stage, to_stage, decided_by_did)
    return {"ok": True, "lead_id": lead_id, "from_stage": from_stage, "to_stage": to_stage}


# ── Task: lawfirm.sales.recordOutreach ───────────────────────────────────────

async def task_lawfirm_record_outreach(
    lead_id: str = "",
    event_kind: str = "mail_sent",
    channel: str = "email",
    direction: str = "out",
    subject: str = "",
    body_preview: str = "",
    asset_uri: str = "",
    actor_did: str = "",
) -> dict:
    if not lead_id:
        return {"ok": False, "error": "lead_id required"}
    event_uri = _vid("outreachEvent")
    _execute(
        "INSERT INTO vertex_lawfirm_outreach_event "
        "(vertex_id, lead_id, event_kind, channel, direction, subject, "
        " body_preview, asset_uri, occurred_at, actor_did, created_at, owner_did) "
        "VALUES (:vid, :lid, :ek, :ch, :dir, :subj, :body, :asset, :now, :actor, :now, :owner)",
        {
            "vid":   event_uri,
            "lid":   lead_id,
            "ek":    event_kind,
            "ch":    channel,
            "dir":   direction,
            "subj":  subject[:500],
            "body":  body_preview[:1500],
            "asset": asset_uri,
            "now":   _now_iso(),
            "actor": actor_did,
            "owner": _FIRM_DID,
        },
    )
    if direction == "out":
        _execute(
            "UPDATE vertex_lawfirm_lead SET last_touch_at = :now WHERE lead_id = :lid",
            {"now": _now_iso(), "lid": lead_id},
        )
    return {"ok": True, "event_uri": event_uri}


# ── Worker registration ──────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 60_000) -> None:
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="lawfirm.mail.replyWebhook",
              timeout_ms=timeout_ms, max_jobs_to_activate=8)
    async def _wh(message_id: str = "", in_reply_to: str = "",
                  from_email: str = "", from_name: str = "",
                  to_emails: list[str] | None = None, subject: str = "",
                  body_preview: str = "", received_at: str = "",
                  graph_event_id: str = "", raw_headers: str = "") -> dict:
        return await task_lawfirm_mail_reply_webhook(
            message_id=message_id, in_reply_to=in_reply_to,
            from_email=from_email, from_name=from_name,
            to_emails=to_emails or [], subject=subject,
            body_preview=body_preview, received_at=received_at,
            graph_event_id=graph_event_id, raw_headers=raw_headers,
        )

    @app.task(task_type="lawfirm.sales.pipelineTransition",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _trans(lead_id: str = "", to_stage: str = "",
                     reason: str = "", decided_by_did: str = "") -> dict:
        return await task_lawfirm_pipeline_transition(
            lead_id=lead_id, to_stage=to_stage,
            reason=reason, decided_by_did=decided_by_did,
        )

    @app.task(task_type="lawfirm.sales.recordOutreach",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _rec(lead_id: str = "", event_kind: str = "mail_sent",
                   channel: str = "email", direction: str = "out",
                   subject: str = "", body_preview: str = "",
                   asset_uri: str = "", actor_did: str = "") -> dict:
        return await task_lawfirm_record_outreach(
            lead_id=lead_id, event_kind=event_kind, channel=channel,
            direction=direction, subject=subject, body_preview=body_preview,
            asset_uri=asset_uri, actor_did=actor_did,
        )

    LOG.info("Registered tasks: lawfirm.mail.replyWebhook, lawfirm.sales.{pipelineTransition,recordOutreach}")
