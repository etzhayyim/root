"""mangaka `load_document` graph — SELECT for ai.gftd.mangaka.document.

Counterpart of save_document.py. Reads one row from vertex_mangaka by
docId and returns the Genko canvas JSON stored in `props`.

Input:
    docId str (required)
Output:
    docId    str
    name     str
    document str  (Genko canvas JSON)
    convoId  str
    error    str | null
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.gftd.ai")
_NSID = "ai.gftd.mangaka.document"
_RW_URL = os.environ.get("RW_URL", "")


class _LoadState(TypedDict, total=False):
    doc_id: str
    name: str
    document: str
    convo_id: str
    vertex_id: str
    docId: str
    vertexId: str
    error: str | None


async def _node_load(state: _LoadState) -> dict[str, Any]:
    doc_id = (state.get("doc_id") or state.get("docId") or "").strip()
    if not doc_id:
        return {"error": "docId required"}
    if not _RW_URL:
        return {"error": "RW_URL not configured"}

    vertex_id = f"at://{_APP_DID}/{_NSID}/{doc_id}"
    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """
                SELECT name, props, vertex_id
                FROM vertex_mangaka
                WHERE vertex_id = %s AND kind = 'document'
                LIMIT 1
                """,
                (vertex_id,),
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("load_document SELECT failed (docId=%s)", doc_id)
        return {"error": f"{type(exc).__name__}: {exc!s}"[:300]}

    if not row:
        return {"error": f"document not found: {doc_id}"}

    name, props, vid = row
    return {
        "doc_id": doc_id, "docId": doc_id,
        "name": name or doc_id,
        "document": props or "",
        "convo_id": "", "convoId": "",
        "vertex_id": vid, "vertexId": vid,
        "error": None,
    }


def _build():
    g: StateGraph = StateGraph(_LoadState)
    g.add_node("load", _node_load, retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START, "load")
    g.add_edge("load", END)
    return g


GRAPH = _build().compile(name="load_document")
