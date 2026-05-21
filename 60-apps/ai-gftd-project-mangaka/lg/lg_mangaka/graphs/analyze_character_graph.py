"""mangaka `analyze_character_graph` — Pregel-style multi-step graph that
derives character relationship analytics from kind=panel vertices, and writes
results back to kind=character and kind=environment vertex.props.

4 super-steps (each is a LangGraph node):

  1. load_panels       — SELECT kind=panel, props from vertex_mangaka
  2. extract_refs      — parse props.characters[] / props.environment per panel
  3. compute_metrics   — aggregate co-occurrence, influence (sum of weighted
                         co-occurrence), environment affinity
  4. write_back        — UPDATE kind=character / kind=environment props

Pregel idiom: each step reads upstream channel (state field), writes its own
output channel; downstream picks it up. Single ainvoke kicks off the cascade.

Input (optional):
    workRkey   str — limit to one work (default: "gh-work-ghost-hacker")
    dryRun     bool — skip write_back (for inspection)

Output:
    status            "analyzed" | "error"
    counts            { panels, characters, environments, edges }
    topInfluence      list[ {charRkey, score, appearances} ] (top 10)
    error             str | null
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.gftd.ai")
_RW_URL = os.environ.get("RW_URL", "")
_DEFAULT_WORK = "gh-work-ghost-hacker"


class _State(TypedDict, total=False):
    work_rkey: str
    dry_run: bool
    # super-step output channels:
    panels: list             # [{ rkey, characters[], environment, page_number, panel_number }]
    char_appearances: dict   # charRkey -> [panel_rkey, ...]
    co_occur: dict           # charRkey -> { otherCharRkey: count }
    char_envs: dict          # charRkey -> { envRkey: count }
    env_panels: dict         # envRkey -> [panel_rkey, ...]
    metrics: dict            # charRkey -> { score, appearances, topCo[], topEnvs[] }
    env_metrics: dict        # envRkey -> { panelCount, topChars[] }
    # final output:
    status: str
    counts: dict
    topInfluence: list
    error: str | None


# Super-step 1: load all panels
async def _step_load_panels(state: _State) -> dict[str, Any]:
    if not _RW_URL:
        return {"status": "error", "error": "RW_URL not configured"}
    import psycopg
    work_rkey = state.get("work_rkey") or _DEFAULT_WORK
    # Filter: panels whose chapter→work parent matches.
    # vertex_mangaka.parent_rkey on panel = page rkey, page.parent_rkey = chapter, etc.
    # Simpler: filter panel rkey prefix that contains the episode pattern. Or accept all.
    # For ghosthacker, panel rkeys are like 'gh-panel-episode:...'.
    sql = (
        "SELECT rkey, page_number, panel_number, props "
        "FROM vertex_mangaka WHERE kind = 'panel' AND rkey LIKE 'gh-panel-%'"
    )
    panels: list[dict[str, Any]] = []
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        await cur.execute(sql)
        async for r in cur:
            rkey, page_n, panel_n, props_str = r
            try:
                p = json.loads(props_str or "{}")
            except Exception:
                p = {}
            panels.append({
                "rkey": rkey,
                "page_number": page_n,
                "panel_number": panel_n,
                "characters": p.get("characters") or [],
                "environment": p.get("environment"),
            })
    finally:
        await conn.close()
    _log.info("analyze_character_graph: loaded %d panels", len(panels))
    return {"panels": panels}


# Super-step 2: extract cross-refs into adjacency-style dicts
async def _step_extract_refs(state: _State) -> dict[str, Any]:
    panels = state.get("panels") or []
    char_appearances: dict[str, list[str]] = defaultdict(list)
    co_occur: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    char_envs: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    env_panels: dict[str, list[str]] = defaultdict(list)

    for p in panels:
        rkey = p["rkey"]
        chars = [c for c in (p.get("characters") or []) if c]
        env = p.get("environment")
        if env:
            env_panels[env].append(rkey)
        for c in chars:
            char_appearances[c].append(rkey)
            if env:
                char_envs[c][env] += 1
        # co-occurrence: every pair in this panel
        for i, a in enumerate(chars):
            for b in chars[i + 1:]:
                if a == b: continue
                co_occur[a][b] += 1
                co_occur[b][a] += 1

    return {
        "char_appearances": {k: v for k, v in char_appearances.items()},
        "co_occur": {k: dict(v) for k, v in co_occur.items()},
        "char_envs": {k: dict(v) for k, v in char_envs.items()},
        "env_panels": dict(env_panels),
    }


# Super-step 3: compute final per-character / per-environment metrics
async def _step_compute_metrics(state: _State) -> dict[str, Any]:
    char_appearances = state.get("char_appearances") or {}
    co_occur = state.get("co_occur") or {}
    char_envs = state.get("char_envs") or {}
    env_panels = state.get("env_panels") or {}

    metrics: dict[str, dict[str, Any]] = {}
    # Frequency-based influence: appearances × 1 + sum(co_occur counts) × 0.3
    for c, panels in char_appearances.items():
        co = co_occur.get(c, {})
        top_co = sorted(co.items(), key=lambda kv: kv[1], reverse=True)[:5]
        envs = char_envs.get(c, {})
        top_envs = sorted(envs.items(), key=lambda kv: kv[1], reverse=True)[:3]
        score = float(len(panels)) + 0.3 * float(sum(co.values()))
        metrics[c] = {
            "appearances": len(panels),
            "score": round(score, 2),
            "topCo": [{"char": k, "count": v} for k, v in top_co],
            "topEnvs": [{"env": k, "count": v} for k, v in top_envs],
        }

    env_metrics: dict[str, dict[str, Any]] = {}
    # Per-environment: panel count + top characters appearing in it
    for env, panels in env_panels.items():
        char_counts: dict[str, int] = defaultdict(int)
        for c, m in char_envs.items():
            if env in m:
                char_counts[c] = m[env]
        top_chars = sorted(char_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        env_metrics[env] = {
            "panelCount": len(panels),
            "topChars": [{"char": k, "count": v} for k, v in top_chars],
        }

    # Top-10 influence ranking for the response
    top_influence = sorted(
        ({"charRkey": k, **v} for k, v in metrics.items()),
        key=lambda x: x["score"], reverse=True,
    )[:10]

    return {
        "metrics": metrics,
        "env_metrics": env_metrics,
        "topInfluence": top_influence,
    }


# Super-step 4: write metrics back into vertex_mangaka.props
async def _step_write_back(state: _State) -> dict[str, Any]:
    if state.get("dry_run"):
        return {
            "status": "analyzed",
            "counts": {
                "panels": len(state.get("panels") or []),
                "characters": len(state.get("metrics") or {}),
                "environments": len(state.get("env_metrics") or {}),
                "edges": sum(len(v) for v in (state.get("co_occur") or {}).values()) // 2,
            },
            "error": None,
        }

    metrics = state.get("metrics") or {}
    env_metrics = state.get("env_metrics") or {}

    import psycopg
    written = {"character": 0, "environment": 0}
    conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
    try:
        cur = conn.cursor()
        # For each character: fetch existing row, merge analytics, re-insert
        for char_rkey, m in metrics.items():
            await cur.execute(
                "SELECT vertex_id, props FROM vertex_mangaka WHERE rkey = %s AND kind='character' LIMIT 1",
                (char_rkey,))
            row = await cur.fetchone()
            if not row:
                continue
            vid, props_str = row
            try:
                p = json.loads(props_str or "{}")
            except Exception:
                p = {}
            p["analytics"] = m
            # Update only the props column (delete-then-insert is RW idiom, but
            # for partial update we use UPDATE if RW supports it; otherwise
            # delete-then-reinsert all columns).
            await _reinsert_with_props(cur, vid, p)
            written["character"] += 1
        for env_rkey, m in env_metrics.items():
            await cur.execute(
                "SELECT vertex_id, props FROM vertex_mangaka WHERE rkey = %s AND kind='environment' LIMIT 1",
                (env_rkey,))
            row = await cur.fetchone()
            if not row:
                continue
            vid, props_str = row
            try:
                p = json.loads(props_str or "{}")
            except Exception:
                p = {}
            p["analytics"] = m
            await _reinsert_with_props(cur, vid, p)
            written["environment"] += 1
    finally:
        await conn.close()

    return {
        "status": "analyzed",
        "counts": {
            "panels": len(state.get("panels") or []),
            "characters": written["character"],
            "environments": written["environment"],
            "edges": sum(len(v) for v in (state.get("co_occur") or {}).values()) // 2,
        },
        "error": None,
    }


async def _reinsert_with_props(cur, vid: str, new_props: dict) -> None:
    """RW doesn't support UPDATE on streaming tables → delete-then-insert.
    We refetch the full row to preserve every column, then re-insert with new props."""
    await cur.execute(
        "SELECT created_date, sensitivity_ord, owner_did, rkey, repo, did, collection, "
        "label, title, name, display_name, description, parent_rkey, page_number, "
        "panel_number, asset_type, mime_type, cid, status, created_at, kind, actor_did, org_did "
        "FROM vertex_mangaka WHERE vertex_id = %s LIMIT 1",
        (vid,))
    r = await cur.fetchone()
    if not r:
        return
    (created_date, sens, owner, rkey, repo, did, coll,
     label, title, name, dname, desc, parent, page_n, panel_n,
     atype, mtype, cid, status_v, created_at, kind, actor_did, org_did) = r
    await cur.execute("DELETE FROM vertex_mangaka WHERE vertex_id = %s", (vid,))
    await cur.execute(
        """
        INSERT INTO vertex_mangaka (
          vertex_id, created_date, sensitivity_ord, owner_did,
          rkey, repo, did, collection,
          label, title, name, display_name, description, parent_rkey,
          page_number, panel_number, asset_type, mime_type, cid,
          status, created_at, props, kind, actor_did, org_did
        ) VALUES (
          %s, %s, %s, %s,
          %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s
        )
        """,
        (vid, created_date, sens, owner,
         rkey, repo, did, coll,
         label, title, name, dname, desc, parent,
         page_n, panel_n, atype, mtype, cid,
         status_v, created_at, json.dumps(new_props, ensure_ascii=False), kind,
         actor_did, org_did),
    )


def _build():
    g: StateGraph = StateGraph(_State)
    g.add_node("load_panels",     _step_load_panels,     retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("extract_refs",    _step_extract_refs)
    g.add_node("compute_metrics", _step_compute_metrics)
    g.add_node("write_back",      _step_write_back,      retry_policy=RetryPolicy(max_attempts=2))
    g.add_edge(START,             "load_panels")
    g.add_edge("load_panels",     "extract_refs")
    g.add_edge("extract_refs",    "compute_metrics")
    g.add_edge("compute_metrics", "write_back")
    g.add_edge("write_back",      END)
    return g


GRAPH = _build().compile(name="analyze_character_graph")
