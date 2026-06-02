"""webmk `list_proposals` graph — paginated proposal list.

NSID: com.etzhayyim.apps.webmk.listProposals
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL", "")


class _State(TypedDict, total=False):
    limit: int
    offset: int
    status: str | None
    items: list
    total: int
    ok: bool
    error: str | None


async def _list(state: _State) -> dict[str, Any]:
    limit = min(int(state.get("limit") or 50), 100)
    offset = max(int(state.get("offset") or 0), 0)
    status_filter = state.get("status")
    if not _RW_URL:
        return {"ok": True, "items": [], "total": 0, "limit": limit, "offset": offset}
    try:
        import psycopg
        async with await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True) as conn:
            where = "WHERE status = %s" if status_filter else ""
            params_list = [status_filter, limit, offset] if status_filter else [limit, offset]
            cur = await conn.execute(
                f"SELECT proposal_id, client_name, industry, quality_score, status, created_at "
                f"FROM vertex_webmk_proposal {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                params_list,
            )
            rows = await cur.fetchall()
            items = [
                {"proposalId": r[0], "clientName": r[1], "industry": r[2],
                 "qualityScore": float(r[3] or 0), "status": r[4], "createdAt": str(r[5])}
                for r in rows
            ]
            return {"ok": True, "items": items, "total": len(items), "limit": limit, "offset": offset}
    except Exception as exc:  # noqa: BLE001
        _log.error("list_proposals failed: %s", exc)
        return {"ok": False, "error": str(exc)[:200], "items": [], "total": 0, "limit": limit, "offset": offset}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("list", _list)
    g.add_edge(START, "list")
    g.add_edge("list", END)
    return g


GRAPH = _build().compile(name="list_proposals")
