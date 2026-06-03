"""webmk `deliver_proposal` graph — send proposal via Resend email.

NSID: com.etzhayyim.apps.webmk.deliverProposal
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_webmk.audit import emit_audit_bg

_log = logging.getLogger(__name__)
_APP_DID = os.environ.get("WEBMK_APP_DID", "did:web:webmk.etzhayyim.com")
_RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
_RESEND_FROM = os.environ.get("RESEND_FROM", "webmk@etzhayyim.com")


class _State(TypedDict, total=False):
    proposal_id: str
    delivery_email: str
    copy_markdown: str
    ok: bool
    delivered: bool
    error: str | None


async def _fetch_proposal(state: _State) -> dict[str, Any]:
    """Fetch copy_markdown from vertex_webmk_proposal if not provided inline."""
    if state.get("copy_markdown"):
        return {}
    proposal_id = state.get("proposal_id", "")
    rw_url = os.environ.get("RW_URL", "")
    if not rw_url or not proposal_id:
        return {"copy_markdown": ""}
    try:
        import psycopg
        async with await psycopg.AsyncConnection.connect(rw_url, autocommit=True) as conn:
            cur = await conn.execute(
                "SELECT copy_markdown FROM vertex_webmk_proposal WHERE proposal_id = %s LIMIT 1",
                (proposal_id,),
            )
            row = await cur.fetchone()
            return {"copy_markdown": row[0] if row else ""}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_proposal failed: %s", exc)
        return {"copy_markdown": ""}


async def _send_email(state: _State) -> dict[str, Any]:
    """Send via Resend API."""
    delivery_email = state.get("delivery_email", "")
    copy_markdown = state.get("copy_markdown", "")
    proposal_id = state.get("proposal_id", "unknown")
    if not delivery_email:
        return {"ok": False, "delivered": False, "error": "delivery_email not set"}
    if not _RESEND_API_KEY:
        _log.warning("RESEND_API_KEY not set, skipping email delivery")
        return {"ok": True, "delivered": False}
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {_RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": _RESEND_FROM,
                    "to": [delivery_email],
                    "subject": f"[webmk] Marketing Proposal #{proposal_id}",
                    "text": copy_markdown[:10000],
                },
            )
            resp.raise_for_status()
        return {"ok": True, "delivered": True}
    except Exception as exc:  # noqa: BLE001
        _log.error("email delivery failed: %s", exc)
        return {"ok": False, "delivered": False, "error": str(exc)[:200]}


async def _update_status(state: _State) -> dict[str, Any]:
    """Mark proposal as delivered in RisingWave."""
    if not state.get("delivered"):
        return {}
    proposal_id = state.get("proposal_id", "")
    rw_url = os.environ.get("RW_URL", "")
    if not rw_url or not proposal_id:
        return {}
    try:
        import psycopg
        async with await psycopg.AsyncConnection.connect(rw_url, autocommit=True) as conn:
            await conn.execute(
                "DELETE FROM vertex_webmk_proposal WHERE proposal_id = %s AND status = 'draft'",
                (proposal_id,),
            )
            await conn.execute(
                "INSERT INTO vertex_webmk_proposal (vertex_id, proposal_id, status, actor_did, org_did, created_at) "
                "VALUES (%s, %s, 'delivered', %s, 'anon', NOW()) ",
                (f"at://did:web:webmk.etzhayyim.com/com.etzhayyim.apps.webmk.proposal/{proposal_id}", proposal_id, _APP_DID),
            )
    except Exception as exc:  # noqa: BLE001
        _log.warning("update_status failed (non-fatal): %s", exc)
    return {}


async def _audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="webmk.deliverProposal",
        object_id=state.get("proposal_id", "unknown"),
        object_type="webmk.proposal",
        attributes={"delivered": state.get("delivered", False)},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_proposal", _fetch_proposal)
    g.add_node("send_email", _send_email)
    g.add_node("update_status", _update_status)
    g.add_node("audit", _audit)
    g.add_edge(START, "fetch_proposal")
    g.add_edge("fetch_proposal", "send_email")
    g.add_edge("send_email", "update_status")
    g.add_edge("update_status", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="deliver_proposal")
