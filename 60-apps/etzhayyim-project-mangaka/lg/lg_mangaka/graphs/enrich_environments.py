"""mangaka `enrich_environments` — upsert kind=environment rows including
those not previously imported. Input contains BOTH the profile data AND a
flag to create-if-missing (since many env subfolders weren't imported).

Pregel-style 3-step:
  1. load_existing  — SELECT existing env rows for the supplied rkeys
  2. plan_writes    — diff existing vs profiles → list of upserts (new + merge)
  3. write_back     — delete-then-insert per row

Input:
    profiles dict[rkey, profileDict]
    dry_run  bool
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
_DEFAULT_ORG_DID = os.environ.get("MANGAKA_DEFAULT_ORG_DID", "did:erc725:etzhayyim:260425:etzhayyim-japan")


class _State(TypedDict, total=False):
    profiles: dict
    dry_run:  bool
    existing: dict   # rkey -> {vid, props}
    plans:    list   # [{rkey, vid_or_none, new_props}]
    status:   str
    counts:   dict
    error:    str | None


async def _step_load_existing(state: _State) -> dict[str, Any]:
    if not _RW_URL: return {"status": "error", "error": "RW_URL not configured"}
    profiles = state.get("profiles") or {}
    if not profiles: return {"existing": {}}
    rkeys = list(profiles.keys())
    import psycopg
    out: dict[str, dict] = {}
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        placeholders = ",".join(["%s"] * len(rkeys))
        await cur.execute(
            f"SELECT vertex_id, rkey, props FROM vertex_mangaka WHERE kind='environment' AND rkey IN ({placeholders})",
            tuple(rkeys))
        async for r in cur:
            try: p = json.loads(r[2] or "{}")
            except Exception: p = {}
            out[r[1]] = {"vid": r[0], "props": p}
    finally:
        await conn.close()
    return {"existing": out}


async def _step_plan_writes(state: _State) -> dict[str, Any]:
    profiles = state.get("profiles") or {}
    existing = state.get("existing") or {}
    plans: list[dict[str, Any]] = []
    for rkey, prof in profiles.items():
        if rkey in existing:
            new_props = dict(existing[rkey]["props"] or {})
            new_props["profile"] = prof
            plans.append({"rkey": rkey, "vid": existing[rkey]["vid"], "new_props": new_props})
        else:
            plans.append({"rkey": rkey, "vid": None, "new_props": {"profile": prof, "name": prof.get("name") or rkey}})
    return {"plans": plans}


async def _step_write_back(state: _State) -> dict[str, Any]:
    plans = state.get("plans") or []
    if state.get("dry_run"):
        n_new = sum(1 for p in plans if p["vid"] is None)
        return {"status": "enriched", "counts": {"updated": len(plans) - n_new, "created": n_new}, "error": None}
    import psycopg
    updated, created = 0, 0
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    now_date = now_iso[:10]
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        for plan in plans:
            if plan["vid"]:
                await _reinsert(cur, plan["vid"], plan["new_props"])
                updated += 1
            else:
                rkey = plan["rkey"]
                name = (plan["new_props"].get("name") or rkey)
                vid = f"at://{_APP_DID}/com.etzhayyim.mangaka.environment/{rkey}"
                await cur.execute("DELETE FROM vertex_mangaka WHERE vertex_id = %s", (vid,))
                await cur.execute(
                    """INSERT INTO vertex_mangaka (vertex_id, created_date, sensitivity_ord, owner_did,
                        rkey, repo, did, collection, label, title, name, display_name,
                        kind, status, created_at, props, actor_did, org_did
                    ) VALUES (%s, %s, 0, %s, %s, %s, %s, %s, 'environment', %s, %s, %s, 'environment', 'saved', %s, %s, %s, %s)""",
                    (vid, now_date, _APP_DID, rkey, _APP_DID, _APP_DID, "com.etzhayyim.mangaka.environment",
                     name, name, name, now_iso, json.dumps(plan["new_props"], ensure_ascii=False),
                     _APP_DID, _DEFAULT_ORG_DID))
                created += 1
    finally:
        await conn.close()
    return {"status": "enriched", "counts": {"updated": updated, "created": created}, "error": None}


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
    g.add_node("load_existing", _step_load_existing, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("plan_writes",   _step_plan_writes)
    g.add_node("write_back",    _step_write_back,    retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START, "load_existing")
    g.add_edge("load_existing", "plan_writes")
    g.add_edge("plan_writes", "write_back")
    g.add_edge("write_back", END)
    return g


GRAPH = _build().compile(name="enrich_environments")
