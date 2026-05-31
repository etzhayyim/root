"""email_route — route pregel-triaged Outlook emails to projector convos.

Task type: ``outlook.email.route``

Architecture (Phase 1 — metadata-only, no body decryption):

  SELECT pending non-sales emails from graphar.vertex_email_message (written
  by the pregel LangGraph server) that are not yet present in
  edge_email_routes_to_project.
  For each email, match against vertex_email_project_route routing rules
  (ordered by priority DESC).  If a rule matches, write:
    * edge_email_routes_to_project  (email → project)
    * INSERT into vertex_projector_message so the projector convo gets a
      notification: "New email from <from_addr> [<from_domain>]"

  Returns {routedTotal, skippedTotal, errors[]} as BPMN process variables.

Table SSoT (Alembic migration 20260512_0001):
  vertex_email_project_route  — routing rules
  edge_email_routes_to_project — routing results (FK: graphar.vertex_email_message.message_id)
Graph schema SSoT (20260512100000_vertex_email_pregel.up.sql):
  graphar.vertex_email_message — pregel LangGraph output (PK: message_id)
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

ACTOR_PREGEL = "did:web:pregel.etzhayyim.com"
COLLECTION_MESSAGE = "app.etzhayyim.convo.message"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_vid() -> str:
    return f"email-route-{uuid.uuid4().hex[:16]}"


async def task_email_route(
    batchSize: int = 100,
    accountDid: str = "",
) -> dict[str, Any]:
    """Route clean, triaged Outlook emails to projector project convos.

    BPMN variables in:
      batchSize  (int, default 100) — max emails to process per run
      accountDid (str, default "")  — filter to a single M365 account

    BPMN variables out:
      routedTotal  (int)  — emails successfully routed to a project
      skippedTotal (int)  — clean emails with no matching routing rule
      errors       (str)  — JSON array of {messageId, error} for failed rows
    """
    batch = max(1, min(int(batchSize or 100), 500))
    account_filter = (accountDid or "").strip()

    # 1. Fetch pending non-sales emails from pregel output, not yet routed
    with sync_cursor() as cur:
        sql = (
            "SELECT em.message_id, em.from_address, "
            "SPLIT_PART(em.from_address, '@', 2) AS from_domain, "
            "em.received_at "
            "FROM graphar.vertex_email_message em "
            "WHERE em.response_status = 'pending' AND em.is_sales = false "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM edge_email_routes_to_project e "
            "  WHERE e.email_vertex_id = em.message_id"
            ") "
        )
        params: list[Any] = []
        if account_filter:
            sql += "AND em.owner = %s "
            params.append(account_filter)
        sql += f"ORDER BY em.received_at DESC LIMIT {batch}"
        cur.execute(sql, params or None)
        cols = [d[0] for d in cur.description]
        emails = [dict(zip(cols, row)) for row in (cur.fetchall() or [])]

    if not emails:
        return {"routedTotal": 0, "skippedTotal": 0, "errors": "[]"}

    # 2. Load all routing rules ordered by priority
    with sync_cursor() as cur:
        cur.execute(
            "SELECT rule_id, project_slug, convo_id, match_type, "
            "match_value, priority "
            "FROM vertex_email_project_route "
            "WHERE active = true "
            "ORDER BY priority DESC, rule_id"
        )
        rule_cols = [d[0] for d in cur.description]
        rules = [dict(zip(rule_cols, row)) for row in (cur.fetchall() or [])]

    now = _now_iso()
    routed = 0
    skipped = 0
    errors: list[dict[str, str]] = []

    for email in emails:
        from_domain = str(email.get("from_domain") or "").lower()
        from_addr = str(email.get("from_address") or "").lower()
        email_vid = email.get("message_id")
        msg_id = email.get("message_id", "")

        matched_rule: dict[str, Any] | None = None
        for rule in rules:
            mt = str(rule.get("match_type") or "").lower()
            mv = str(rule.get("match_value") or "").lower()
            if mt == "domain" and from_domain == mv:
                matched_rule = rule
                break
            if mt == "address" and from_addr == mv:
                matched_rule = rule
                break
            if mt == "domain_suffix" and from_domain.endswith(mv):
                matched_rule = rule
                break

        if matched_rule is None:
            skipped += 1
            continue

        project_slug = matched_rule["project_slug"]
        convo_id = matched_rule.get("convo_id") or f"project:{project_slug}"
        edge_vid = _new_vid()
        msg_rkey = f"pregel-{uuid.uuid4().hex[:12]}"
        msg_uri = f"at://{ACTOR_PREGEL}/{COLLECTION_MESSAGE}/{msg_rkey}"

        try:
            with sync_cursor() as cur:
                cur.execute(
                    "INSERT INTO edge_email_routes_to_project "
                    "(vertex_id, email_vertex_id, project_slug, convo_id, "
                    "rule_id, matched_at, actor_did, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        edge_vid,
                        email_vid,
                        project_slug,
                        convo_id,
                        str(matched_rule.get("rule_id") or ""),
                        now,
                        ACTOR_PREGEL,
                        now,
                    ),
                )
                cur.execute(
                    "INSERT INTO vertex_projector_message "
                    "(vertex_id, convo_id, text, created_at, actor_id, "
                    "rkey, uri, value_json) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        f"proj-msg-{uuid.uuid4().hex[:12]}",
                        convo_id,
                        f"[pregel] New email from {from_addr or from_domain} "
                        f"routed to project:{project_slug}",
                        now,
                        ACTOR_PREGEL,
                        msg_rkey,
                        msg_uri,
                        json.dumps({
                            "sourceMessageId": str(msg_id),
                            "fromDomain": from_domain,
                            "fromAddress": from_addr,
                            "matchType": matched_rule.get("match_type"),
                            "matchValue": matched_rule.get("match_value"),
                        }, ensure_ascii=False),
                    ),
                )
            routed += 1
        except Exception as exc:
            errors.append({"messageId": str(msg_id), "error": str(exc)[:120]})

    return {
        "routedTotal": routed,
        "skippedTotal": skipped,
        "errors": json.dumps(errors, ensure_ascii=False),
    }


def register(worker: object, *, timeout_ms: int = 60_000) -> None:
    """Wire ``outlook.email.route`` onto the shared LangServer worker."""
    worker.task(  # type: ignore[attr-defined]
        task_type="outlook.email.route",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_email_route)


__all__ = ["task_email_route", "register"]
