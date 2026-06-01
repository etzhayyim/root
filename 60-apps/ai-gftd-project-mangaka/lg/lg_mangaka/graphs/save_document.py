"""mangaka `save_document` graph — persistence for app.etzhayyim.mangaka.document.

ADR-2605111200: CF Worker cannot reach Hyperdrive directly. The mangaka
edge Worker proxies `/xrpc/{nsid}` to dispatcher.etzhayyim.com or to this
LangGraph server. This graph INSERTs one row into `vertex_mangaka` with
`kind='document'` and the full Genko canvas JSON in `props`.

Input schema (matches `app.etzhayyim.mangaka.saveDocument` lexicon,
post-2026-05-12 string-ID migration):
    docId    str (required)  — e.g. "doc-gh-arc0-1-origin"
    name     str              — display title
    document str              — JSON-encoded Genko canvas body
    convoId  str              — project convoId scope (optional)
    actorDid str              — caller DID (defaults to mangaka app DID)
    orgDid   str              — RLS org_did (defaults to gftd-japan)

Output:
    status   "saved" | "error"
    docId    echoed back
    vertexId at://{app_did}/{collection}/{rkey}
    error    str | null

Idempotent: delete-then-insert (RisingWave doesn't support ON CONFLICT
for record-log shape, same as `_RwAsyncPostgresSaver` writes pattern).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_mangaka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.etzhayyim.com")
_NSID = "app.etzhayyim.mangaka.document"
_DEFAULT_ORG_DID = os.environ.get(
    "MANGAKA_DEFAULT_ORG_DID",
    "did:erc725:gftd:260425:gftd-japan",
)
_RW_URL = os.environ.get("RW_URL", "")


class _SaveState(TypedDict, total=False):
    doc_id: str
    name: str
    document: str
    convo_id: str
    actor_did: str
    org_did: str
    status: str
    vertex_id: str
    docId: str        # lexicon-camelCase echo
    vertexId: str
    error: str | None


async def _node_save(state: _SaveState) -> dict[str, Any]:
    doc_id = (state.get("doc_id") or state.get("docId") or "").strip()
    if not doc_id:
        return {"status": "error", "error": "docId required"}

    if not _RW_URL:
        return {"status": "error", "error": "RW_URL not configured"}

    name = (state.get("name") or doc_id).strip()
    document = state.get("document") or ""
    convo_id = state.get("convo_id") or state.get("convoId") or ""
    actor_did = (state.get("actor_did") or state.get("actorDid") or _APP_DID).strip()
    org_did = (state.get("org_did") or state.get("orgDid") or _DEFAULT_ORG_DID).strip()
    vertex_id = f"at://{_APP_DID}/{_NSID}/{doc_id}"
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    now_date = now_iso[:10]

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                "DELETE FROM vertex_mangaka WHERE vertex_id = %s",
                (vertex_id,),
            )
            await cur.execute(
                """
                INSERT INTO vertex_mangaka (
                    vertex_id, created_date, sensitivity_ord, owner_did,
                    rkey, repo, did, collection,
                    label, title, name, display_name,
                    kind, status, created_at, props,
                    actor_did, org_did
                ) VALUES (
                    %s, %s, 0, %s,
                    %s, %s, %s, %s,
                    'document', %s, %s, %s,
                    'document', 'saved', %s, %s,
                    %s, %s
                )
                """,
                (
                    vertex_id, now_date, _APP_DID,
                    doc_id, _APP_DID, _APP_DID, _NSID,
                    name, name, name,
                    now_iso, document,
                    actor_did, org_did,
                ),
            )
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("save_document INSERT failed (docId=%s)", doc_id)
        return {"status": "error", "error": f"{type(exc).__name__}: {exc!s}"[:300]}

    return {
        "status": "saved",
        "doc_id": doc_id, "docId": doc_id,
        "vertex_id": vertex_id, "vertexId": vertex_id,
        "error": None,
    }


async def _node_emit_audit(state: _SaveState) -> dict[str, Any]:
    emit_audit_bg(
        actor=state.get("actor_did") or state.get("actorDid") or _APP_DID,
        activity="mangaka.document.save",
        object_id=state.get("vertex_id") or state.get("vertexId") or state.get("doc_id") or state.get("docId") or "",
        object_type="mangaka.document",
        attributes={
            "docId": state.get("doc_id") or state.get("docId"),
            "ok": state.get("status") == "saved",
            "error": state.get("error"),
        },
    )
    return {}


def _build():
    g: StateGraph = StateGraph(_SaveState)
    g.add_node("save", _node_save, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "save")
    g.add_edge("save", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="save_document")
