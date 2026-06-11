"""animeka `list_works` graph — read-only DB query.

Replaces BPMN `animeka_list_works` (NSID: com.etzhayyim.animeka.listWorks).
Returns recent work records from `vertex_animeka` filtered by collection.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")


class _ListWorksState(TypedDict, total=False):
    owner_did: str          # optional filter
    limit: int              # default 50
    offset: int             # default 0
    works: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_query(state: _ListWorksState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "works": []}

    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    owner = state.get("owner_did")

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            params: list[Any] = ["com.etzhayyim.animeka.work"]
            where = "collection = %s"
            if owner:
                where += " AND repo = %s"
                params.append(owner)
            # f-string LIMIT/OFFSET to dodge RW parameterised-LIMIT quirk.
            await cur.execute(
                f"""
                SELECT repo, rkey, ts_ms, value_json
                FROM vertex_repo_record
                WHERE {where}
                ORDER BY ts_ms DESC
                LIMIT {int(limit)} OFFSET {int(offset)}
                """,
                params,
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("list_works query failed")
        return {"error": f"query: {exc!s}"[:300], "works": []}

    works: list[dict[str, Any]] = []
    for repo, rkey, ts_ms, value_json_text in rows:
        works.append({
            "uri": f"at://{repo}/com.etzhayyim.animeka.work/{rkey}",
            "rkey": rkey,
            "ownerDid": repo,
            "tsMs": int(ts_ms or 0),
            "raw": (value_json_text or "")[:1000],   # cap envelope
        })

    return {"works": works, "total": len(works)}


async def _node_emit_audit(state: _ListWorksState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.listWorks",
        object_id=f"listWorks:{int(time.time())}",
        object_type="animeka.work",
        attributes={
            "limit": int(state.get("limit") or 50),
            "offset": int(state.get("offset") or 0),
            "ownerDid": state.get("owner_did") or "*",
            "returned": int(state.get("total", 0)),
        },
    )
    return {}


def _build():
    g: StateGraph = StateGraph(_ListWorksState)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="list_works")
