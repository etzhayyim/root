"""mangaka `enrich_characters` — merge per-character profile metadata
(gh:appearance / age / role / slug) into existing kind=character rows.

Pregel-style 3-step:
  1. load_targets   — SELECT kind=character rows that need enrichment
  2. merge_profiles — per-entity merge of input profiles into row.props
  3. write_back     — delete-then-insert per row with enriched props

Input (snake_case after server.py shim):
    profiles dict[rkey, profileDict]   — e.g. { "gh-char-Yuto": { name, schema_age, gh_appearance, ... } }
    dry_run  bool                       — skip write
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL", "")


class _State(TypedDict, total=False):
    profiles: dict
    dry_run: bool
    targets: list      # [{rkey, vid, props}]
    merged:  list      # [{vid, new_props}]
    status:  str
    counts:  dict
    error:   str | None


async def _step_load_targets(state: _State) -> dict[str, Any]:
    if not _RW_URL: return {"status": "error", "error": "RW_URL not configured"}
    profiles = state.get("profiles") or {}
    if not profiles: return {"targets": []}
    rkeys = list(profiles.keys())
    import psycopg
    rows = []
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        # Use parametrized IN clause
        placeholders = ",".join(["%s"] * len(rkeys))
        await cur.execute(
            f"SELECT vertex_id, rkey, props FROM vertex_mangaka WHERE kind='character' AND rkey IN ({placeholders})",
            tuple(rkeys))
        async for r in cur:
            try: p = json.loads(r[2] or "{}")
            except Exception: p = {}
            rows.append({"vid": r[0], "rkey": r[1], "props": p})
    finally:
        await conn.close()
    return {"targets": rows}


async def _step_merge_profiles(state: _State) -> dict[str, Any]:
    profiles = state.get("profiles") or {}
    targets = state.get("targets") or []
    merged = []
    for t in targets:
        prof = profiles.get(t["rkey"]) or {}
        new_props = dict(t["props"] or {})
        new_props["profile"] = prof
        merged.append({"vid": t["vid"], "new_props": new_props})
    return {"merged": merged}


async def _step_write_back(state: _State) -> dict[str, Any]:
    merged = state.get("merged") or []
    if state.get("dry_run"):
        return {"status": "enriched", "counts": {"updated": len(merged)}, "error": None}
    import psycopg
    written = 0
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        for m in merged:
            await _reinsert(cur, m["vid"], m["new_props"])
            written += 1
    finally:
        await conn.close()
    return {"status": "enriched", "counts": {"updated": written}, "error": None}


async def _reinsert(cur, vid: str, new_props: dict) -> None:
    await cur.execute(
        "SELECT created_date, sensitivity_ord, owner_did, rkey, repo, did, collection, "
        "label, title, name, display_name, description, parent_rkey, page_number, "
        "panel_number, asset_type, mime_type, cid, status, created_at, kind, actor_did, org_did "
        "FROM vertex_mangaka WHERE vertex_id = %s LIMIT 1", (vid,))
    r = await cur.fetchone()
    if not r: return
    (cd, s, o, rk, rp, dd, c, lb, ti, nm, dn, ds, pr, pgn, pln, at, mt, ci, st, ca, kd, ad, od) = r
    await cur.execute("DELETE FROM vertex_mangaka WHERE vertex_id = %s", (vid,))
    await cur.execute(
        """INSERT INTO vertex_mangaka (vertex_id, created_date, sensitivity_ord, owner_did,
            rkey, repo, did, collection, label, title, name, display_name, description, parent_rkey,
            page_number, panel_number, asset_type, mime_type, cid, status, created_at, props, kind, actor_did, org_did
        ) VALUES (%s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s)""",
        (vid, cd, s, o, rk, rp, dd, c, lb, ti, nm, dn, ds, pr, pgn, pln, at, mt, ci, st, ca,
         json.dumps(new_props, ensure_ascii=False), kd, ad, od))


def _build():
    g: StateGraph = StateGraph(_State)
    g.add_node("load_targets",   _step_load_targets,   retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("merge_profiles", _step_merge_profiles)
    g.add_node("write_back",     _step_write_back,     retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START, "load_targets")
    g.add_edge("load_targets", "merge_profiles")
    g.add_edge("merge_profiles", "write_back")
    g.add_edge("write_back", END)
    return g


GRAPH = _build().compile(name="enrich_characters")
