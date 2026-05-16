"""Outlook reply-draft HITL helpers.

Manages LLM-generated reply drafts for emails that were triaged as "clean".
Drafts are held for human review (approve / discard / edit) before sending.

Table: ``vertex_email_reply_draft``
  vertex_id       VARCHAR PK   (format: ``draft-{email_vertex_id}``)
  email_vertex_id VARCHAR NOT NULL
  from_address    VARCHAR DEFAULT ''
  subject         VARCHAR DEFAULT ''
  draft_text      VARCHAR NOT NULL
  status          VARCHAR DEFAULT 'pending'   (pending | approved | discarded)
  action          VARCHAR DEFAULT ''
  final_text      VARCHAR DEFAULT ''
  actor_did       VARCHAR NOT NULL
  created_at      VARCHAR NOT NULL

DDL (run separately in autocommit — NOT executed here):

  CREATE TABLE vertex_email_reply_draft (
      vertex_id       VARCHAR PRIMARY KEY,
      email_vertex_id VARCHAR NOT NULL,
      from_address    VARCHAR DEFAULT '',
      subject         VARCHAR DEFAULT '',
      draft_text      VARCHAR NOT NULL,
      status          VARCHAR DEFAULT 'pending',
      action          VARCHAR DEFAULT '',
      final_text      VARCHAR DEFAULT '',
      actor_did       VARCHAR NOT NULL,
      created_at      VARCHAR NOT NULL
  );

RisingWave does NOT support ON CONFLICT — use INSERT ... SELECT ... WHERE NOT EXISTS.
DDL runs in autocommit.  No FK constraints.
"""

from __future__ import annotations

import os
import time
from typing import Any

from pymagatama.db_sync import sync_cursor

ACTOR_DID = "did:web:pregel.gftd.ai"


# ── Internal helpers ───────────────────────────────────────────────────


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _fetch_email_details(email_vertex_id: str) -> dict | None:
    """SELECT from_address, subject, body_preview FROM vertex_email_message WHERE vertex_id = %s."""
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT from_address, subject, body_preview
            FROM vertex_email_message
            WHERE vertex_id = %s
            LIMIT 1
            """,
            (email_vertex_id,),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "from_address": row[0] or "",
        "subject": row[1] or "",
        "body_preview": row[2] or "",
    }


def _generate_draft_text(from_address: str, subject: str, body_preview: str) -> str:
    """Generate a polite reply draft using LLM or template fallback.

    Tries langchain_openai or openai if OPENAI_API_KEY / OPENAI_BASE_URL is set.
    Falls back to a static Japanese template when LLM is unavailable.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "")

    if api_key or base_url:
        # Try LangChain first, then raw openai SDK
        try:
            from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]
            from langchain_core.messages import HumanMessage  # type: ignore[import-not-found]

            llm_kwargs: dict[str, Any] = {"model": "gpt-4o-mini", "temperature": 0.3}
            if api_key:
                llm_kwargs["api_key"] = api_key
            if base_url:
                llm_kwargs["base_url"] = base_url

            llm = ChatOpenAI(**llm_kwargs)
            prompt = (
                f"以下のメールに対する丁寧な日本語の返信下書きを作成してください。\n\n"
                f"送信元: {from_address}\n"
                f"件名: {subject}\n"
                f"本文抜粋: {body_preview[:500]}\n\n"
                f"返信下書き:"
            )
            result = llm.invoke([HumanMessage(content=prompt)])
            draft = str(result.content).strip()
            if draft:
                return draft
        except Exception:
            pass  # fall through to openai SDK or template

        try:
            import openai  # type: ignore[import-not-found]

            client_kwargs: dict[str, Any] = {}
            if api_key:
                client_kwargs["api_key"] = api_key
            if base_url:
                client_kwargs["base_url"] = base_url

            client = openai.OpenAI(**client_kwargs)
            prompt = (
                f"以下のメールに対する丁寧な日本語の返信下書きを作成してください。\n\n"
                f"送信元: {from_address}\n"
                f"件名: {subject}\n"
                f"本文抜粋: {body_preview[:500]}\n\n"
                f"返信下書き:"
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            draft = (response.choices[0].message.content or "").strip()
            if draft:
                return draft
        except Exception:
            pass  # fall through to template

    # Static template fallback
    return (
        "お世話になっております。\n\n"
        "ご連絡いただきありがとうございます。\n"
        "内容を確認の上、改めてご連絡いたします。\n\n"
        "よろしくお願いいたします。"
    )


# ── Internal helpers (continued) ──────────────────────────────────────


def _should_auto_approve(from_address: str) -> bool:
    """Return True if sender history is trusted enough to skip HITL.

    Criteria: at least 5 clean verdicts, zero spam verdicts in the last 90 days.
    """
    if not from_address:
        return False
    try:
        from pymagatama.agents.outlook_feedback import get_sender_prior as _gsp
        prior = _gsp(from_address)
        return prior.get("clean_count", 0) >= 5 and prior.get("spam_count", 0) == 0
    except Exception:
        return False


# ── Public API ─────────────────────────────────────────────────────────


def queue_reply_draft(
    email_vertex_id: str,
    from_address: str = "",
    subject: str = "",
    body_preview: str = "",
) -> str | None:
    """Generate and queue a reply draft.

    If *from_address*, *subject*, or *body_preview* are not provided,
    they are fetched from ``vertex_email_message``.

    Uses ``INSERT ... SELECT ... WHERE NOT EXISTS`` to avoid duplicates
    (RisingWave does not support ON CONFLICT).

    Returns the draft *vertex_id* if a new row was inserted,
    or ``None`` if a draft already existed for this email.
    """
    draft_vertex_id = f"draft-{email_vertex_id}"

    # Fill missing details from vertex_email_message
    if not (from_address and subject and body_preview):
        details = _fetch_email_details(email_vertex_id)
        if details:
            from_address = from_address or details.get("from_address", "")
            subject = subject or details.get("subject", "")
            body_preview = body_preview or details.get("body_preview", "")

    draft_text = _generate_draft_text(from_address, subject, body_preview)
    now = _now_iso()

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_email_reply_draft
                (vertex_id, email_vertex_id, from_address, subject,
                 draft_text, status, action, final_text, actor_did, created_at)
            SELECT %s, %s, %s, %s, %s, 'pending', '', '', %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM vertex_email_reply_draft
                WHERE vertex_id = %s
            )
            """,
            (
                draft_vertex_id,
                email_vertex_id,
                str(from_address)[:480],
                str(subject)[:480],
                draft_text,
                ACTOR_DID,
                now,
                draft_vertex_id,
            ),
        )
        inserted = (cur.rowcount or 0) > 0

    if inserted and _should_auto_approve(from_address):
        try:
            apply_draft_verdict(draft_vertex_id, "approve")
        except Exception:
            pass  # best-effort; draft remains pending for manual review

    return draft_vertex_id if inserted else None


def list_pending_drafts(limit: int = 50) -> list[dict]:
    """SELECT pending reply drafts.

    Returns a list of dicts with keys:
      thread_id (= vertex_id), updated_at (= created_at),
      email_vertex_id, from_address, subject, draft_text
    """
    limit = max(1, min(int(limit), 1000))
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, created_at, email_vertex_id,
                   from_address, subject, draft_text
            FROM vertex_email_reply_draft
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
                "subject": r["subject"],
                "draft_text": r["draft_text"],
            }
        )
    return result


def get_draft_item(draft_id: str) -> dict | None:
    """SELECT a single reply draft by vertex_id.

    Returns a dict with all column values or ``None`` if not found.
    """
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, created_at, email_vertex_id,
                   from_address, subject, draft_text,
                   status, action, final_text
            FROM vertex_email_reply_draft
            WHERE vertex_id = %s
            LIMIT 1
            """,
            (draft_id,),
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
        "subject": r["subject"],
        "draft_text": r["draft_text"],
        "status": r["status"],
        "action": r["action"],
        "final_text": r["final_text"],
    }


def apply_draft_verdict(draft_id: str, action: str, final_text: str = "") -> bool:
    """Apply a human verdict to a reply draft.

    *action* must be one of ``'approve'``, ``'discard'``, or ``'edit'``.

    - ``approve`` → ``status='approved'``, ``final_text`` = provided text or original draft
    - ``discard`` → ``status='discarded'``, ``final_text`` = provided text or original draft
    - ``edit``    → ``status='approved'``, ``final_text`` = provided text (edited version)

    Returns ``True`` on success, ``False`` if the draft was not found.
    """
    action = str(action).lower()[:120]

    with sync_cursor() as cur:
        # Fetch existing draft to fall back to draft_text when final_text is empty
        cur.execute(
            """
            SELECT draft_text
            FROM vertex_email_reply_draft
            WHERE vertex_id = %s
            LIMIT 1
            """,
            (draft_id,),
        )
        row = cur.fetchone()
        if row is None:
            return False

        original_draft_text: str = row[0] or ""
        resolved_final_text = str(final_text).strip() if str(final_text).strip() else original_draft_text

        if action == "discard":
            new_status = "discarded"
        else:
            # approve or edit both result in approved status
            new_status = "approved"

        cur.execute(
            """
            UPDATE vertex_email_reply_draft
            SET status = %s, action = %s, final_text = %s
            WHERE vertex_id = %s
            """,
            (new_status, action, resolved_final_text, draft_id),
        )

    if new_status == "approved":
        try:
            from pymagatama.agents.outlook_reply_sender import send_reply_for_draft as _srf
            _srf(draft_id, resolved_final_text)
        except Exception:
            pass  # sending is best-effort; DB status already updated

    return True


__all__ = [
    "queue_reply_draft",
    "list_pending_drafts",
    "get_draft_item",
    "apply_draft_verdict",
]
