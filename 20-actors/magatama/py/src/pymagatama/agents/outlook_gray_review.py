"""Outlook gray-zone email HITL review helpers.

Provides queue management for emails that scored in the gray zone during
automated triage.  These emails are held for human review before being
marked as triaged in ``vertex_email_message``.

Table: ``vertex_email_gray_queue``
  vertex_id          VARCHAR PK   (format: ``gray-{email_vertex_id}``)
  email_vertex_id    VARCHAR NOT NULL
  from_address       VARCHAR DEFAULT ''
  triage_score       INTEGER DEFAULT 0
  triage_reasons     VARCHAR DEFAULT ''  (comma-separated)
  status             VARCHAR DEFAULT 'pending'  (pending | resolved | skipped)
  verdict            VARCHAR DEFAULT ''
  actor_did          VARCHAR NOT NULL
  created_at         VARCHAR NOT NULL

RisingWave does NOT support ON CONFLICT — use INSERT ... SELECT ... WHERE NOT EXISTS.
DDL runs in autocommit.  No FK constraints.
"""

from __future__ import annotations

import time
from typing import Any

from pymagatama.db_sync import sync_cursor

ACTOR_DID = "did:web:pregel.gftd.ai"


# ── Internal helpers ───────────────────────────────────────────────────


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── Public API ─────────────────────────────────────────────────────────


def enqueue_gray_emails(rows: list[dict]) -> int:
    """INSERT gray emails into ``vertex_email_gray_queue``.

    Each *row* must contain:
      - ``vertex_id``   — email vertex ID (becomes the email_vertex_id column)
      - ``from_address`` or ``from_addr`` — sender address (optional)
      - ``score``       — integer triage score
      - ``reasons``     — list[str] of triage reason strings

    Uses ``INSERT ... SELECT ... WHERE NOT EXISTS`` to avoid duplicates
    (RisingWave does not support ON CONFLICT).

    Returns the number of rows actually inserted.
    """
    if not rows:
        return 0

    now = _now_iso()
    inserted = 0

    with sync_cursor() as cur:
        for row in rows:
            email_vertex_id = str(row.get("vertex_id") or "")
            if not email_vertex_id:
                continue
            gray_vertex_id = f"gray-{email_vertex_id}"
            from_address = str(
                row.get("from_address") or row.get("from_addr") or ""
            )[:480]
            score = int(row.get("score") or 0)
            reasons_list = row.get("reasons") or []
            if isinstance(reasons_list, (list, tuple)):
                reasons_csv = ",".join(str(r) for r in reasons_list)[:480]
            else:
                reasons_csv = str(reasons_list)[:480]

            cur.execute(
                """
                INSERT INTO vertex_email_gray_queue
                    (vertex_id, email_vertex_id, from_address,
                     triage_score, triage_reasons,
                     status, verdict, actor_did, created_at)
                SELECT %s, %s, %s, %s, %s, 'pending', '', %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM vertex_email_gray_queue
                    WHERE vertex_id = %s
                )
                """,
                (
                    gray_vertex_id,
                    email_vertex_id,
                    from_address,
                    score,
                    reasons_csv,
                    ACTOR_DID,
                    now,
                    gray_vertex_id,
                ),
            )
            # rowcount may be 0 (already exists) or 1 (inserted)
            if (cur.rowcount or 0) > 0:
                inserted += 1

    return inserted


def list_pending_gray(limit: int = 50) -> list[dict]:
    """SELECT pending gray-zone emails from the queue.

    Returns a list of dicts with keys:
      thread_id, updated_at, email_vertex_id, from_address,
      triage_score, triage_reasons
    """
    limit = max(1, min(int(limit), 1000))
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, created_at, email_vertex_id,
                   from_address, triage_score, triage_reasons
            FROM vertex_email_gray_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        cols = [d[0] for d in cur.description]
        raw_rows = cur.fetchall() or []

    result: list[dict] = []
    for row in raw_rows:
        r: dict[str, Any] = dict(zip(cols, row))
        result.append(
            {
                "thread_id": r["vertex_id"],
                "updated_at": r["created_at"],
                "email_vertex_id": r["email_vertex_id"],
                "from_address": r["from_address"],
                "triage_score": r["triage_score"],
                "triage_reasons": r["triage_reasons"],
            }
        )
    return result


def get_gray_item(thread_id: str) -> dict | None:
    """SELECT a single gray-queue item by vertex_id.

    Returns a dict with keys:
      thread_id, updated_at, email_vertex_id, from_address,
      triage_score, triage_reasons, status
    or ``None`` if not found.
    """
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, created_at, email_vertex_id,
                   from_address, triage_score, triage_reasons, status
            FROM vertex_email_gray_queue
            WHERE vertex_id = %s
            LIMIT 1
            """,
            (thread_id,),
        )
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()

    if row is None:
        return None

    r: dict[str, Any] = dict(zip(cols, row))
    return {
        "thread_id": r["vertex_id"],
        "updated_at": r["created_at"],
        "email_vertex_id": r["email_vertex_id"],
        "from_address": r["from_address"],
        "triage_score": r["triage_score"],
        "triage_reasons": r["triage_reasons"],
        "status": r["status"],
    }


def apply_verdict(thread_id: str, verdict: str) -> bool:
    """Apply a human verdict to a gray-queue item.

    Sets ``status='resolved'`` and ``verdict=verdict`` on the queue row,
    and also propagates the decision to ``vertex_email_message`` by
    setting ``triaged_at`` and ``triage_classification``.

    Returns ``True`` on success, ``False`` if the queue item was not found.
    """
    now = _now_iso()
    verdict = str(verdict)[:120]

    with sync_cursor() as cur:
        # Fetch email_vertex_id, triage_score, and from_address
        cur.execute(
            """
            SELECT email_vertex_id, triage_score, from_address
            FROM vertex_email_gray_queue
            WHERE vertex_id = %s
            LIMIT 1
            """,
            (thread_id,),
        )
        row = cur.fetchone()
        if row is None:
            return False
        email_vertex_id: str = row[0]
        triage_score: int = int(row[1] or 0)
        from_address: str = str(row[2] or "")

        # Update the gray queue row
        cur.execute(
            """
            UPDATE vertex_email_gray_queue
            SET status = 'resolved', verdict = %s
            WHERE vertex_id = %s
            """,
            (verdict, thread_id),
        )

        # Propagate to vertex_email_message
        cur.execute(
            """
            UPDATE vertex_email_message
            SET triaged_at = %s, triage_classification = %s
            WHERE vertex_id = %s
            """,
            (now, verdict, email_vertex_id),
        )

    # Record feedback for auto-learning (best-effort)
    try:
        from pymagatama.agents.outlook_feedback import record_verdict as _rv
        _rv(email_vertex_id, from_address, triage_score, verdict)
    except Exception:
        pass  # feedback recording is best-effort

    # If classified as clean, queue a reply draft (best-effort)
    if verdict == "clean":
        try:
            from pymagatama.agents.outlook_reply_draft import queue_reply_draft as _qrd
            _qrd(email_vertex_id)
        except Exception:
            pass  # draft generation is best-effort

    return True


__all__ = [
    "enqueue_gray_emails",
    "list_pending_gray",
    "get_gray_item",
    "apply_verdict",
]
