"""mangaka `record_op_log` — append a change-history entry as kind=opLog in
vertex_mangaka, plus link it to the parent document via edge_mangaka_emits_op.

Pregel-style 2-step:
  1. build_row — assign rkey + parent + props from input
  2. write_row — INSERT vertex_mangaka kind=opLog + INSERT edge_mangaka_emits_op

opLog row shape:
  vertex_id     at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mangaka.opLog/{rkey}
  rkey          op-{docRkey}-{tsMs}-{nidShort}
  parent_rkey   docRkey
  kind          opLog
  name          {op} {nodeType} {nidShort}
  created_at    ISO timestamp
  props         { op, nid, nodeType, before, after, actor, docId }

Edge: edge_mangaka_emits_op  (src=document, dst=opLog)

Input (snake_case after server.py shim):
    doc_id      str  — Genko docId (e.g. doc-gh-arc0-1-origin)
    op          str  — move | edit | delete | add | other
    nid         str  — overlay _nid
    node_type   str  — panel | fukidashi | text | ai-image | ...
    before      str  — JSON-stringified previous state
    after       str  — JSON-stringified new state
    actor_did   str  — caller DID (default = mangaka app DID)
    org_did     str
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL", "")
_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.etzhayyim.com")
_DEFAULT_ORG_DID = os.environ.get("MANGAKA_DEFAULT_ORG_DID", "did:erc725:gftd:260425:gftd-japan")


class _State(TypedDict, total=False):
    doc_id:    str
    op:        str
    nid:       str
    node_type: str
    before:    str
    after:     str
    actor_did: str
    org_did:   str
    # super-step output:
    row:       dict
    status:    str
    rkey:      str
    error:     str | None


def _short_nid(nid: str) -> str:
    nid = (nid or "").lstrip("nN")
    return nid[:10] or "anon"


async def _step_build_row(state: _State) -> dict[str, Any]:
    doc_id = (state.get("doc_id") or "").strip()
    if not doc_id:
        return {"status": "error", "error": "docId required"}
    op = (state.get("op") or "other").strip()
    nid = (state.get("nid") or "").strip()
    node_type = (state.get("node_type") or "").strip()
    ts_ms = int(time.time() * 1000)
    rkey = f"op-{doc_id}-{ts_ms}-{_short_nid(nid)}"
    doc_rkey = doc_id  # rkey of the kind=document row
    name = f"{op} {node_type} {_short_nid(nid)}".strip()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    actor_did = (state.get("actor_did") or _APP_DID).strip()
    org_did = (state.get("org_did") or _DEFAULT_ORG_DID).strip()
    props = {
        "op": op,
        "nid": nid,
        "nodeType": node_type,
        "before": state.get("before") or "",
        "after": state.get("after") or "",
        "actor": actor_did,
        "docId": doc_id,
        "ts": ts_ms,
    }
    row = {
        "vid": f"at://{_APP_DID}/com.etzhayyim.mangaka.opLog/{rkey}",
        "rkey": rkey, "parent_rkey": doc_rkey, "name": name, "now_iso": now_iso,
        "props": props, "actor_did": actor_did, "org_did": org_did,
        "doc_vid": f"at://{_APP_DID}/com.etzhayyim.mangaka.document/{doc_rkey}",
    }
    return {"row": row}


async def _step_write_row(state: _State) -> dict[str, Any]:
    row = state.get("row") or {}
    if not row:
        return {"status": "error", "error": state.get("error") or "row missing"}
    if not _RW_URL: return {"status": "error", "error": "RW_URL not configured"}
    import psycopg
    try:
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # 1. vertex_mangaka opLog row
            await cur.execute(
                "DELETE FROM vertex_mangaka WHERE vertex_id = %s", (row["vid"],))
            await cur.execute(
                """INSERT INTO vertex_mangaka (vertex_id, created_date, sensitivity_ord, owner_did,
                    rkey, repo, did, collection, label, title, name, display_name,
                    kind, status, created_at, props, parent_rkey, actor_did, org_did
                ) VALUES (%s, %s, 0, %s, %s, %s, %s, %s, 'opLog', %s, %s, %s, 'opLog', 'recorded', %s, %s, %s, %s, %s)""",
                (row["vid"], row["now_iso"][:10], _APP_DID, row["rkey"], _APP_DID, _APP_DID,
                 "com.etzhayyim.mangaka.opLog", row["name"], row["name"], row["name"],
                 row["now_iso"], json.dumps(row["props"], ensure_ascii=False), row["parent_rkey"],
                 row["actor_did"], row["org_did"]))
            # 2. edge_mangaka_emits_op (document → opLog)
            eid = f"emits_op:{row['parent_rkey']}:{row['rkey']}"
            await cur.execute(
                "DELETE FROM edge_mangaka_emits_op WHERE edge_id = %s", (eid,))
            await cur.execute(
                """INSERT INTO edge_mangaka_emits_op (edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord, owner_did)
                   VALUES (%s, %s, %s, 0, %s, 0, %s)""",
                (eid, row["doc_vid"], row["vid"], row["now_iso"][:10], _APP_DID))
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("record_op_log failed (docId=%s op=%s)", state.get("doc_id"), state.get("op"))
        return {"status": "error", "error": f"{type(exc).__name__}: {exc!s}"[:300]}
    return {"status": "recorded", "rkey": row["rkey"], "error": None}


def _build():
    g: StateGraph = StateGraph(_State)
    g.add_node("build_row", _step_build_row)
    g.add_node("write_row", _step_write_row, retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START, "build_row")
    g.add_edge("build_row", "write_row")
    g.add_edge("write_row", END)
    return g


GRAPH = _build().compile(name="record_op_log")
