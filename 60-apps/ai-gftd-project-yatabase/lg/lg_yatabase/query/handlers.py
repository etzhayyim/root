"""FastAPI router for deploy-first query XRPC handlers.

NSIDs:
  ai.gftd.apps.yata.deployQuery
  ai.gftd.apps.yata.executeDeployedQuery
  ai.gftd.apps.yata.listDeployedQueries
  ai.gftd.apps.yata.deleteDeployedQuery

Auth: x-internal-trust HMAC (same pattern as bmc/handlers.py).
The CF Worker validates quota before forwarding here.
The pod connects to RisingWave via asyncpg for both DDL and queries.

TODO(substrate-boundary): replace RW query execution (db_execute, fetch via asyncpg)
with AT Protocol storage per ADR-2605172000. Query registry: MST collection
'ai.gftd.apps.yata.deployedQuery', results cached on IPFS. Update after schema finalized.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.bmc.db import execute as db_execute, fetch
import lg_yatabase.query.compiler as compiler
import lg_yatabase.query.repository as repository
from lg_yatabase.query.models import (
    DeleteQueryInput,
    DeployQueryInput,
    ExecuteQueryInput,
    PatternSpec,
    Step,
    VertexStep,
    EdgeStep,
)

_log = logging.getLogger(__name__)

router = APIRouter()

_MV_LIMIT_DEFAULT = 5  # Free plan floor; Worker passes x-gftd-mv-limit header


async def _verify_trust(request: Request, x_internal_trust: str | None) -> bytes:
    body = await request.body()
    secret = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if not secret:
        return body
    if not x_internal_trust:
        raise HTTPException(status_code=401, detail="missing x-internal-trust")
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, x_internal_trust):
        raise HTTPException(status_code=401, detail="x-internal-trust mismatch")
    return body


def _identity(actor_did: str | None, org_did: str | None) -> tuple[str, str]:
    return (actor_did or "anon"), (org_did or "anon")


def _parse_steps(steps_json: str) -> list[Step]:
    raw = json.loads(steps_json)
    steps: list[Step] = []
    for item in raw:
        if item.get("kind") == "vertex":
            steps.append(VertexStep(**item))
        elif item.get("kind") == "edge":
            steps.append(EdgeStep(**item))
        else:
            raise ValueError(f"unknown step kind: {item!r}")
    return steps


# ── deployQuery ────────────────────────────────────────────────────────


@router.post("/xrpc/ai.gftd.apps.yata.deployQuery")
async def deploy_query(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_gftd_mv_limit: str | None = Header(default=None, alias="x-gftd-mv-limit"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    actor_did, org_did = _identity(x_gftd_actor_did, x_gftd_org_did)
    mv_limit = int(x_gftd_mv_limit or _MV_LIMIT_DEFAULT)

    body_bytes = await request.body()
    inp = DeployQueryInput.model_validate_json(body_bytes)

    # Check idempotency
    existing = await repository.get_deployed_query(org_did, inp.queryId)
    if existing:
        return JSONResponse({
            "ok": True,
            "queryId": inp.queryId,
            "mvName": existing["mv_name"],
            "mvSlotsUsed": await repository.count_deployed_queries(org_did),
            "mvSlotsLimit": mv_limit,
            "alreadyDeployed": True,
            "translatedDdl": existing["translated_ddl"],
        })

    # Quota check (secondary guard; primary is in Worker)
    used = await repository.count_deployed_queries(org_did)
    if used >= mv_limit:
        return JSONResponse(
            {"ok": False, "error": f"MV quota exceeded ({used}/{mv_limit})"},
            status_code=429,
        )

    # Parse + validate pattern
    try:
        steps = _parse_steps(inp.stepsJson)
        select = json.loads(inp.selectJson) if inp.selectJson else []
        index_on = json.loads(inp.indexOnJson) if inp.indexOnJson else []
        static_where = json.loads(inp.staticWhereJson) if inp.staticWhereJson else None
        spec = PatternSpec(steps=steps, select=select, index_on=index_on, static_where=static_where)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"invalid pattern: {e}"}, status_code=400)

    mv = compiler.mv_name(org_did, inp.stepsJson, inp.selectJson)

    try:
        ddl = compiler.compile_ddl(spec, mv, static_where)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"compile error: {e}"}, status_code=400)

    # Execute DDL (each statement separately — RW requires single statement per exec)
    t0 = time.time()
    try:
        for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
            await db_execute(stmt + ";")
    except Exception as e:
        _log.exception("[deployQuery] DDL failed for org=%s query=%s", org_did, inp.queryId)
        return JSONResponse(
            {"ok": False, "queryId": inp.queryId, "error": str(e)[:500]},
            status_code=500,
        )

    build_ms = int((time.time() - t0) * 1000)

    # Record
    await repository.insert_deployed_query(
        org_did=org_did,
        actor_did=actor_did,
        query_id=inp.queryId,
        mv_name=mv,
        steps_json=inp.stepsJson,
        select_json=inp.selectJson,
        index_on_json=inp.indexOnJson,
        static_where_json=inp.staticWhereJson,
        translated_ddl=ddl,
    )

    return JSONResponse({
        "ok": True,
        "queryId": inp.queryId,
        "mvName": mv,
        "mvSlotsUsed": used + 1,
        "mvSlotsLimit": mv_limit,
        "alreadyDeployed": False,
        "translatedDdl": ddl,
        "buildMs": build_ms,
    })


# ── executeDeployedQuery ────────────────────────────────────────────────


@router.post("/xrpc/ai.gftd.apps.yata.executeDeployedQuery")
async def execute_deployed_query(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org_did = _identity(x_gftd_actor_did, x_gftd_org_did)

    body_bytes = await request.body()
    inp = ExecuteQueryInput.model_validate_json(body_bytes)

    row = await repository.get_deployed_query(org_did, inp.queryId)
    if not row:
        return JSONResponse(
            {"ok": False, "error": f"queryId not found: {inp.queryId}"},
            status_code=404,
        )

    mv = row["mv_name"]
    bind = json.loads(inp.bindJson) if inp.bindJson else {}

    # Build WHERE from bind params (all index lookups)
    where_parts: list[str] = []
    params: list[Any] = []
    for col, val in bind.items():
        params.append(val)
        where_parts.append(f"{col} = ${len(params)}")

    where_clause = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    params += [inp.limit, inp.offset]
    limit_clause = f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"

    sql = f"SELECT * FROM {mv} {where_clause} {limit_clause}"

    t0 = time.time()
    try:
        rows = await fetch(sql, *params)
    except Exception as e:
        _log.exception("[executeDeployedQuery] query failed mv=%s", mv)
        return JSONResponse({"ok": False, "error": str(e)[:500]}, status_code=500)

    elapsed = int((time.time() - t0) * 1000)
    if not rows:
        return JSONResponse({
            "ok": True,
            "queryId": inp.queryId,
            "rowCount": 0,
            "columnsJson": "[]",
            "rowsJson": "[]",
            "elapsedMs": elapsed,
        })

    cols = list(rows[0].keys())
    data = [list(r.values()) for r in rows]

    return JSONResponse({
        "ok": True,
        "queryId": inp.queryId,
        "rowCount": len(data),
        "columnsJson": json.dumps(cols),
        "rowsJson": json.dumps(data, default=str),
        "elapsedMs": elapsed,
    })


# ── listDeployedQueries ────────────────────────────────────────────────


@router.get("/xrpc/ai.gftd.apps.yata.listDeployedQueries")
async def list_deployed_queries(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_gftd_mv_limit: str | None = Header(default=None, alias="x-gftd-mv-limit"),
    limit: int = 50,
    cursor: str | None = None,
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org_did = _identity(None, x_gftd_org_did)
    mv_limit = int(x_gftd_mv_limit or _MV_LIMIT_DEFAULT)

    rows = await repository.list_deployed_queries(org_did, limit=limit, cursor=cursor)
    used = await repository.count_deployed_queries(org_did)

    next_cursor = str(rows[-1]["created_at"]) if len(rows) == limit else None

    return JSONResponse({
        "ok": True,
        "queriesJson": json.dumps(rows, default=str),
        "mvSlotsUsed": used,
        "mvSlotsLimit": mv_limit,
        "cursor": next_cursor,
    })


# ── deleteDeployedQuery ────────────────────────────────────────────────


@router.post("/xrpc/ai.gftd.apps.yata.deleteDeployedQuery")
async def delete_deployed_query(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org_did = _identity(x_gftd_actor_did, x_gftd_org_did)

    body_bytes = await request.body()
    inp = DeleteQueryInput.model_validate_json(body_bytes)

    row = await repository.get_deployed_query(org_did, inp.queryId)
    if not row:
        return JSONResponse(
            {"ok": False, "error": f"queryId not found: {inp.queryId}"},
            status_code=404,
        )

    mv = row["mv_name"]

    # Drop MV (indexes are dropped automatically with the MV in RisingWave)
    try:
        await db_execute(f"DROP MATERIALIZED VIEW IF EXISTS {mv};")
    except Exception as e:
        _log.exception("[deleteDeployedQuery] DROP MV failed mv=%s", mv)
        return JSONResponse({"ok": False, "error": str(e)[:500]}, status_code=500)

    await repository.delete_deployed_query(org_did, inp.queryId)

    used = await repository.count_deployed_queries(org_did)
    return JSONResponse({"ok": True, "mvSlotsUsed": used})
