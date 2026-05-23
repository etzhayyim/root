"""mangaka `derive_chapter_incidents` — create kind=incident rows from
incidents.jsonld grouping and inject cross-refs into chapter rows' props.

incidents.jsonld structure:
    { gh:episodes: [
        { gh:arc, gh:episodes:[1,6,10], gh:episodeIds:[episode:...,...],
          gh:industry, gh:mainCharacter, gh:supportingCharacters:[],
          gh:description }, ... ] }

Pregel-style 4-step:
  1. parse_incidents       — input.incidents → list of grouped incidents
  2. create_incident_rows  — INSERT/upsert kind=incident rows (parent=work)
  3. link_chapters         — for each chapter rkey in incident.episodeIds,
                             merge { incidentRkey: <list> } into chapter.props
  4. write_back            — apply all upserts

Input:
    incidents list   — gh:episodes array verbatim
    work_rkey  str   — parent work rkey (default "gh-work-ghost-hacker")
    dry_run    bool
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL", "")
_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.etzhayyim.com")
_DEFAULT_ORG_DID = os.environ.get("MANGAKA_DEFAULT_ORG_DID", "did:erc725:gftd:260425:gftd-japan")


class _State(TypedDict, total=False):
    incidents:  list
    work_rkey:  str
    dry_run:    bool
    parsed:     list   # [{rkey, data, episodeRkeys}]
    chap_refs:  dict   # chapter_rkey -> [incident_rkey, ...]
    status:     str
    counts:     dict
    error:      str | None


def _slug(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"


async def _step_parse_incidents(state: _State) -> dict[str, Any]:
    incs = state.get("incidents") or []
    parsed = []
    for i, it in enumerate(incs):
        arc = it.get("gh:arc") or it.get("arc") or ""
        # rkey: gh-inc-{arc-slug}-{index}
        rkey = f"gh-inc-{_slug(arc)}-{i+1}"
        ep_ids = it.get("gh:episodeIds") or it.get("episodeIds") or []
        ep_rkeys = [f"gh-chap-{e}" for e in ep_ids]
        parsed.append({"rkey": rkey, "data": it, "episodeRkeys": ep_rkeys})
    return {"parsed": parsed}


async def _step_link_chapters(state: _State) -> dict[str, Any]:
    chap_refs: dict[str, list[str]] = {}
    for inc in state.get("parsed") or []:
        for cr in inc["episodeRkeys"]:
            chap_refs.setdefault(cr, []).append(inc["rkey"])
    return {"chap_refs": chap_refs}


async def _step_write_back(state: _State) -> dict[str, Any]:
    parsed = state.get("parsed") or []
    chap_refs = state.get("chap_refs") or {}
    if state.get("dry_run"):
        return {"status": "derived", "counts": {
            "incidents": len(parsed),
            "chapters_linked": len(chap_refs),
        }, "error": None}
    if not _RW_URL: return {"status": "error", "error": "RW_URL not configured"}

    import psycopg
    work_rkey = state.get("work_rkey") or "gh-work-ghost-hacker"
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    now_date = now_iso[:10]
    inc_count, chap_count = 0, 0
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        # 1. Upsert incident rows
        for inc in parsed:
            rkey = inc["rkey"]
            data = inc["data"]
            name = data.get("gh:description") or rkey
            title = (data.get("gh:arc") or "") + " — " + (data.get("gh:industry") or "")
            vid = f"at://{_APP_DID}/ai.gftd.mangaka.incident/{rkey}"
            props = {
                "arc": data.get("gh:arc") or "",
                "industry": data.get("gh:industry") or "",
                "mainCharacter": data.get("gh:mainCharacter") or "",
                "supportingCharacters": data.get("gh:supportingCharacters") or [],
                "description": data.get("gh:description") or "",
                "episodes": data.get("gh:episodes") or [],
                "episodeIds": data.get("gh:episodeIds") or [],
                "episodeRkeys": inc["episodeRkeys"],
            }
            await cur.execute("DELETE FROM vertex_mangaka WHERE vertex_id = %s", (vid,))
            await cur.execute(
                """INSERT INTO vertex_mangaka (vertex_id, created_date, sensitivity_ord, owner_did,
                    rkey, repo, did, collection, label, title, name, display_name,
                    kind, status, created_at, props, parent_rkey, actor_did, org_did
                ) VALUES (%s, %s, 0, %s, %s, %s, %s, %s, 'incident', %s, %s, %s, 'incident', 'saved', %s, %s, %s, %s, %s)""",
                (vid, now_date, _APP_DID, rkey, _APP_DID, _APP_DID,
                 "ai.gftd.mangaka.incident", title.strip(" —"), name, name,
                 now_iso, json.dumps(props, ensure_ascii=False), work_rkey,
                 _APP_DID, _DEFAULT_ORG_DID))
            inc_count += 1

        # 2. Merge chap_refs into existing chapter rows' props.incidents
        for chap_rkey, inc_rkeys in chap_refs.items():
            await cur.execute(
                "SELECT vertex_id, props FROM vertex_mangaka WHERE rkey = %s AND kind='chapter' LIMIT 1",
                (chap_rkey,))
            row = await cur.fetchone()
            if not row: continue
            vid, props_str = row
            try: p = json.loads(props_str or "{}")
            except Exception: p = {}
            p["incidents"] = inc_rkeys
            await _reinsert(cur, vid, p)
            chap_count += 1
    finally:
        await conn.close()
    return {"status": "derived", "counts": {"incidents": inc_count, "chapters_linked": chap_count}, "error": None}


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
    g.add_node("parse_incidents", _step_parse_incidents)
    g.add_node("link_chapters",   _step_link_chapters)
    g.add_node("write_back",      _step_write_back, retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START, "parse_incidents")
    g.add_edge("parse_incidents", "link_chapters")
    g.add_edge("link_chapters", "write_back")
    g.add_edge("write_back", END)
    return g


GRAPH = _build().compile(name="derive_chapter_incidents")
