"""FastAPI server for lg-kenkyusha (Science OS / EACN3-style research loop).

Surface (LangGraph-compatible):

  GET  /health /ok                       → liveness
  GET  /graphs                           → list graph IDs
  POST /runs                             → invoke kenkyusha-research-loop synchronously
  POST /frontiers/publish                → publish a new research problem (Science OS Step 1)
  GET  /frontiers/{id}/state             → fetch frontier + top hypothesis snapshot
  GET  /frontiers                        → list active frontiers (Science OS use-case view)

Auth: optional `LG_KENKYUSHA_API_KEY` env enforces `x-api-key` on all
non-health endpoints. Cron path (x-cron=1) is allowed anonymously
(tunnel-layer trust).

The graph itself lives in ``kotodama.kenkyusha.graph`` so the same code
runs under (a) the LangGraph cron declared in langgraph.json and (b) the
bpmn-dispatcher /runs invocation.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import asyncpg
from fastapi import FastAPI, Header, HTTPException

from kotodama.kenkyusha.graph import build_graph as _build_kenkyusha

_log = logging.getLogger(__name__)


_DB_URL = os.getenv(
    "DATABASE_URL",
    "REDACTED_USE_DATABASE_URL_ENV",
)

GRAPHS: dict[str, Any] = {
    "kenkyusha_research_loop": _build_kenkyusha(),
}

app = FastAPI(
    title="lg-kenkyusha",
    description="LangGraph Server: kenkyusha co-scientist research-frontier Pregel loop.",
    version="0.0.1",
)


def _enforce_auth(
    x_api_key: str | None,
    *,
    exempt: bool = False,
    internal_token: str | None = None,
) -> None:
    """Authenticate a request.

    Three accepted paths:
      1. ``exempt=True``                        — cron sidechannel
      2. ``X-Kotodama-Internal-Token`` matches  — MCP-adapter Worker proxy
                                                  (atproto.etzhayyim.com/mcp)
      3. ``x-api-key`` matches LG_KENKYUSHA_API_KEY — yoro / dispatcher
    """
    if exempt:
        return
    expected_internal = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if internal_token and expected_internal and internal_token == expected_internal:
        return
    expected = os.environ.get("LG_KENKYUSHA_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-kenkyusha",
        "ts": int(time.time() * 1000),
        "graphs": list(GRAPHS.keys()),
    }


@app.get("/graphs")
def _list_graphs() -> dict[str, Any]:
    return {"graphs": list(GRAPHS.keys())}


@app.post("/runs")
async def _runs(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_cron: str | None = Header(default=None, alias="x-cron"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    _enforce_auth(
        x_api_key,
        exempt=(x_cron == "1"),
        internal_token=x_kotodama_internal_token,
    )
    graph_id = body.get("graph") or body.get("assistant_id", "kenkyusha_research_loop")
    if graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail=f"unknown graph: {graph_id}")
    inp = body.get("input", {})
    config = body.get("config", {})
    t0 = time.time()
    try:
        result = await GRAPHS[graph_id].ainvoke(inp, config=config)
    except Exception as e:
        _log.exception("[lg-kenkyusha][runs] graph=%s failed", graph_id)
        raise HTTPException(status_code=500, detail=str(e)[:300])
    return {
        "ok": True,
        "graph": graph_id,
        "duration_ms": int((time.time() - t0) * 1000),
        "result": result,
    }


# ── Science OS / EACN3-style endpoints ────────────────────────────────────────


@app.post("/frontiers/publish")
async def _publish_frontier(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> dict[str, Any]:
    """Science OS Step 1: a human (or initiating agent) publishes a research
    problem with title + primary discipline. The Pregel loop then runs the
    full 6-role super-step pipeline and returns the result envelope.

    Body: { "title": "...", "primaryDiscipline": "0613", "maxHypotheses": 4 }
    """
    _enforce_auth(x_api_key)
    title = str(body.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    discipline = str(body.get("primaryDiscipline") or "0613")
    max_h = max(2, min(int(body.get("maxHypotheses") or 4), 8))

    t0 = time.time()
    try:
        result = await GRAPHS["kenkyusha_research_loop"].ainvoke({
            "frontierTitle": title,
            "primaryDiscipline": discipline,
            "maxHypotheses": max_h,
        })
    except Exception as e:
        _log.exception("[lg-kenkyusha][publish] failed")
        raise HTTPException(status_code=500, detail=str(e)[:300])

    return {
        "ok": True,
        "duration_ms": int((time.time() - t0) * 1000),
        "frontier_id": result.get("frontier_id", ""),
        "frontier_did": result.get("frontier_did", ""),
        "winner_hypothesis_id": result.get("winner_hypothesis_id", ""),
        "consensus_level": result.get("consensus_level", "none"),
        "next_action": result.get("next_action", "iterate"),
        "result": result,
    }


@app.get("/frontiers/{frontier_id}/state")
async def _frontier_state(
    frontier_id: str,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key, internal_token=x_kotodama_internal_token)
    try:
        conn = await asyncpg.connect(_DB_URL)
        try:
            frontier = await conn.fetchrow(
                """
                SELECT frontier_id, did, title, detection_method,
                       primary_discipline, urgency, evidence_level,
                       consensus_level, status,
                       hypothesis_count, evidence_count,
                       detected_at, last_analyzed_at
                FROM graphar.vertex_kenkyusha_frontier
                WHERE frontier_id = $1
                """,
                frontier_id,
            )
            if frontier is None:
                raise HTTPException(status_code=404, detail="frontier not found")
            top = await conn.fetchrow(
                """
                SELECT hypothesis_id, statement, rationale,
                       confidence_score, elo_rating,
                       supporting_evidence, contradicting_evidence,
                       super_step, parent_hypothesis_id, mutation_kind, status
                FROM graphar.vertex_kenkyusha_hypothesis
                WHERE frontier_id = $1
                ORDER BY elo_rating DESC
                LIMIT 1
                """,
                frontier_id,
            )
            evidence_rows = await conn.fetch(
                """
                SELECT evidence_id, hypothesis_id, source_type, source_did,
                       source_title, evidence_type, relevance_score,
                       extracted_claim
                FROM graphar.vertex_kenkyusha_evidence
                WHERE frontier_id = $1
                ORDER BY relevance_score DESC
                LIMIT 20
                """,
                frontier_id,
            )
        finally:
            await conn.close()
    except HTTPException:
        raise
    except Exception as e:
        _log.exception("[lg-kenkyusha][state] failed")
        raise HTTPException(status_code=500, detail=str(e)[:300])

    return {
        "frontier": dict(frontier),
        "top_hypothesis": dict(top) if top else None,
        "evidence": [dict(r) for r in evidence_rows],
    }


@app.get("/frontiers")
async def _list_frontiers(
    limit: int = 50,
    status: str | None = None,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key, internal_token=x_kotodama_internal_token)
    # RisingWave rejects parameterised LIMIT ("expects an integer or expression
    # that can be evaluated to an integer after LIMIT, but found non-const
    # expression"). Inline the int literal — `limit` is already validated.
    limit = max(1, min(int(limit), 500))
    where = "status = $1" if status else "1=1"
    args: list[Any] = [status] if status else []
    try:
        conn = await asyncpg.connect(_DB_URL)
        try:
            rows = await conn.fetch(
                f"""
                SELECT frontier_id, did, title, detection_method,
                       primary_discipline, urgency,
                       evidence_level, consensus_level, status,
                       hypothesis_count, evidence_count,
                       detected_at, last_analyzed_at
                FROM graphar.vertex_kenkyusha_frontier
                WHERE {where}
                ORDER BY last_analyzed_at DESC
                LIMIT {limit}
                """,
                *args,
            )
        finally:
            await conn.close()
    except Exception as e:
        _log.exception("[lg-kenkyusha][list] failed")
        raise HTTPException(status_code=500, detail=str(e)[:300])
    return {
        "frontiers": [dict(r) for r in rows],
        "limit": limit,
        "offset": 0,
        "total": len(rows),
    }


# ── XRPC NSID surface (Phase 2A MCP facade) ──────────────────────────────────
#
# atproto.etzhayyim.com/mcp tools/call dispatches to
# https://kenkyusha.etzhayyim.com/xrpc/com.etzhayyim.apps.kenkyusha.<method>. The pod
# (this server) is the canonical owner of vertex_kenkyusha_* (ADR-2605111200),
# so these routes are NSID-style aliases for /frontiers/* with input shape
# matching 00-contracts/lexicons/com/etzhayyim/apps/kenkyusha/<method>.json.
#
# Auth: X-Kotodama-Internal-Token from app-worker-proxy.ts is accepted in lieu
# of x-api-key (see _enforce_auth).

_NSID_PUBLISH = "/xrpc/com.etzhayyim.apps.kenkyusha.publishFrontier"
_NSID_GET     = "/xrpc/com.etzhayyim.apps.kenkyusha.getFrontier"
_NSID_LIST    = "/xrpc/com.etzhayyim.apps.kenkyusha.listFrontiers"


@app.post(_NSID_PUBLISH)
async def _xrpc_publish_frontier(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    return await _publish_frontier(
        body=body,
        x_api_key=x_api_key,
        x_kotodama_internal_token=x_kotodama_internal_token,
    )


@app.post(_NSID_GET)
async def _xrpc_get_frontier(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    fid = str(body.get("frontier_id") or "").strip()
    if not fid:
        raise HTTPException(status_code=400, detail="frontier_id required")
    return await _frontier_state(
        frontier_id=fid,
        x_api_key=x_api_key,
        x_kotodama_internal_token=x_kotodama_internal_token,
    )


@app.post(_NSID_LIST)
async def _xrpc_list_frontiers(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_kotodama_internal_token: str | None = Header(default=None, alias="X-Kotodama-Internal-Token"),
) -> dict[str, Any]:
    limit = int(body.get("limit") or 50)
    status_v = body.get("status")
    status = str(status_v) if isinstance(status_v, str) and status_v else None
    return await _list_frontiers(
        limit=limit,
        status=status,
        x_api_key=x_api_key,
        x_kotodama_internal_token=x_kotodama_internal_token,
    )
