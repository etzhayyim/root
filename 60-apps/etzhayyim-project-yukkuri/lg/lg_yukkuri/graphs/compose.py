"""yukkuri `compose` graph — topic → video enqueue (status: queued).

NSID: com.etzhayyim.apps.yukkuri.compose

Creates a vertex_yukkuri_video row with status='queued'.
The CF Worker onCommit handler picks this up and calls generate_script.
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_REPO = os.environ.get("YUKKURI_REPO_DID", "did:web:y5kk5r1x.etzhayyim.com")


class _State(TypedDict, total=False):
    topic: str
    outline: str | None
    owner_did: str | None
    # output
    video_id: str | None
    video_uri: str | None
    error: str | None


async def _node_validate(state: _State) -> dict[str, Any]:
    topic = (state.get("topic") or "").strip()
    if not topic:
        return {"error": "topic is required"}
    if len(topic) > 500:
        return {"error": "topic too long (max 500 chars)"}
    return {}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    topic = (state.get("topic") or "").strip()
    outline = (state.get("outline") or "").strip() or None
    owner_did = state.get("owner_did") or _APP_DID
    rkey = f"video-{secrets.token_hex(6)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.apps.yukkuri.video/{rkey}"
    created_at = datetime.now(tz=timezone.utc).isoformat()
    title = f"ゆっくり実況: {topic[:48]}"
    try:
        import asyncio
        from pymagatama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        await asyncio.to_thread(client.insert_row, "vertex_yukkuri_video", {
            "vertex_id": vertex_id,
            "video_id": rkey,
            "repo": _REPO,
            "owner_did": owner_did,
            "title": title,
            "topic": topic,
            "outline": outline,
            "status": "queued",
            "created_at": created_at
        })
    except Exception as exc:  # noqa: BLE001
        _log.exception("compose insert failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"video_id": rkey, "video_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="yukkuri.compose",
        object_id=f"video:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.video",
        attributes={
            "videoId": state.get("video_id"),
            "topic": (state.get("topic") or "")[:100],
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("validate", _node_validate)
    g.add_node("insert", _node_insert, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "validate")
    g.add_edge("validate", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="compose")
