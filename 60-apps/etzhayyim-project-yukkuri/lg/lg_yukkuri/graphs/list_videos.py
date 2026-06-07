"""yukkuri `listVideos` graph — read-only DB query.

NSID: com.etzhayyim.apps.yukkuri.listVideos
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")


class _State(TypedDict, total=False):
    owner_did: str | None
    status: str | None      # optional filter (queued/script/assembled/...)
    limit: int
    offset: int
    videos: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_query(state: _State) -> dict[str, Any]:
    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    owner = state.get("owner_did")
    status_filter = state.get("status")
    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        import asyncio
        client = get_kotoba_client()

        # Build EDN datalog query dynamically if needed, or pull all and filter
        # Since the filter depends on owner_did and status, we'll fetch all matching type 
        # and sort/slice in python (similar to other kotoba shims unless we write EDN).
        # Actually, let's use client.select_where which is easier.
        # It doesn't natively support multi-where, so we fetch all for the primary filter.

        if owner:
            raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "owner_did", owner, limit=2000)
            if status_filter:
                raw_rows = [r for r in raw_rows if r.get("status") == status_filter]
        elif status_filter:
            raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "status", status_filter, limit=2000)
        else:
            # no filter, just fetch a bunch (kotoba query fallback)
            raw_rows = await asyncio.to_thread(client.q, '[:find (pull ?e [*]) :where [?e :vertex-yukkuri-video/video-id ?v]]')
            raw_rows = [r[0] for r in raw_rows if r]

        raw_rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
        total = len(raw_rows)
        paged = raw_rows[offset:offset+limit]

        out = []
        for r in paged:
            out.append({
                "video_id": r.get("video_id") or r.get("video-id"),
                "owner_did": r.get("owner_did") or r.get("owner-did"),
                "topic": r.get("topic"),
                "status": r.get("status"),
                "render_url": r.get("render_url") or r.get("render-url"),
                "created_at": r.get("created_at") or r.get("created-at"),
            })
        return {"videos": out, "total": total}
    except Exception as exc:  # noqa: BLE001
        _log.exception("list_videos failed")
        return {"error": f"query: {exc!s}"[:300]}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="yukkuri.listVideos",
        object_id=f"listVideos:{int(time.time())}",
        object_type="yukkuri.video",
        attributes={"returned": int(state.get("total", 0))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("query", _node_query, retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="list_videos")
