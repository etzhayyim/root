"""FastAPI / Granian ASGI server for the SES LangGraph (ADR-2605120000).

Surface:
  POST /runs                → invoke ses_ingest graph synchronously
  POST /mcp                 → JSON-RPC 2.0 MCP (tools/list, tools/call)
  POST /cron/outlook-pull   → manual Outlook differential pull trigger
  GET  /health              → liveness
  GET  /ok                  → liveness alias
  GET  /graphs              → list graph IDs

MCP tools exposed:
  ai.gftd.apps.ses.listAnken  → list 案件 with optional jokyo filter
  ai.gftd.apps.ses.getAnken   → 案件 detail + jokyo log
  ai.gftd.apps.ses.listJokyo  → jokyo transition log for an anken

Auth: optional LG_SES_API_KEY env enforces x-api-key on /runs and /mcp.

External access requires a Cloudflare Tunnel ingress rule:
  hostname: ses-api.gftd.ai → http://ses-langgraph.mitama-udf.svc.cluster.local:8000
  (add DNS CNAME ses-api.gftd.ai → <tunnel-uuid>.cfargotunnel.com)
"""

from __future__ import annotations

import asyncio
import json as json_lib
import logging
import os
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from pymagatama.ses.graph import build_graph
from pymagatama.ses.state import RunStatus, SourceKind

_log = logging.getLogger(__name__)


def _resolve_checkpointer() -> Any:
    """Return RisingWaveCheckpointSaver when SES_CHECKPOINTER=on, else None."""
    if os.environ.get("SES_CHECKPOINTER", "off").strip().lower() != "on":
        return None
    try:
        from pymagatama.langgraph_checkpoint_rw import RisingWaveCheckpointSaver
        return RisingWaveCheckpointSaver()
    except Exception:
        _log.warning("[lg-ses] checkpointer unavailable — falling back to in-process only")
        return None


_CHECKPOINTER = _resolve_checkpointer()
_GRAPH = build_graph(checkpointer=_CHECKPOINTER)
GRAPHS: dict[str, Any] = {"ses_ingest": _GRAPH}

app = FastAPI(
    title="lg-ses",
    description="LangGraph Server: SES 案件・状況 ingest pipeline (ADR-2605120000).",
    version="0.3.0",
)


def _enforce_auth(x_api_key: str | None) -> None:
    expected = os.environ.get("LG_SES_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-ses",
        "phase": os.environ.get("SES_PHASE", "3"),
        "ts": int(time.time() * 1000),
        "graphs": list(GRAPHS.keys()),
        "checkpointer": "rw" if _CHECKPOINTER is not None else "off",
        "m365_creds_configured": all(
            os.environ.get(k) for k in ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET")
        ),
    }


@app.get("/graphs")
def _list_graphs() -> dict[str, Any]:
    return {"graphs": list(GRAPHS.keys())}


@app.post("/cron/outlook-pull")
async def _cron_outlook_pull(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> dict[str, Any]:
    """Manual trigger for Outlook differential pull (Phase 3, ADR-2605120000).

    Body:
      mailbox_upn: str  (required)
      actor_did:   str  (optional, defaults to SES_ACTOR_DID env)
      org_did:     str  (optional)
    """
    _enforce_auth(x_api_key)

    mailbox_upn = str(body.get("mailbox_upn", "")).strip()
    if not mailbox_upn:
        raise HTTPException(status_code=422, detail="mailbox_upn is required")

    tenant_id = os.environ.get("AZURE_TENANT_ID", "").strip()
    client_id = os.environ.get("AZURE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("AZURE_CLIENT_SECRET", "").strip()
    if not all([tenant_id, client_id, client_secret]):
        raise HTTPException(
            status_code=503,
            detail="M365 credentials not configured (AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET)",
        )

    actor_did = str(
        body.get("actor_did") or os.environ.get("SES_ACTOR_DID", "did:web:ses.gftd.ai")
    )
    org_did = str(
        body.get("org_did") or os.environ.get("SES_ORG_DID", "did:erc725:gftd:260425:anon")
    )

    from pymagatama.ses.outlook_pull import run_outlook_pull

    t0 = time.time()
    result = await run_outlook_pull(
        GRAPHS["ses_ingest"],
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        mailbox_upn=mailbox_upn,
        actor_did=actor_did,
        org_did=org_did,
    )

    return {
        "ok": result.get("ok", False),
        "duration_ms": int((time.time() - t0) * 1000),
        **result,
    }


@app.post("/runs")
async def _runs(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key)

    graph_id = body.get("graph", "ses_ingest")
    if graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail=f"unknown graph: {graph_id}")

    inp = body.get("input", {})
    config = body.get("config", {})

    # Validate required fields before invoking
    for field in ("source_kind", "raw_text", "actor_did", "org_did", "run_id"):
        if not inp.get(field):
            raise HTTPException(
                status_code=422,
                detail=f"input.{field} is required",
            )

    source_kind = inp.get("source_kind", "")
    if source_kind not in (sk.value for sk in SourceKind):
        raise HTTPException(
            status_code=422,
            detail=f"input.source_kind must be one of {[sk.value for sk in SourceKind]}",
        )

    if not inp.get("started_at"):
        inp["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    t0 = time.time()
    try:
        result = await GRAPHS[graph_id].ainvoke(inp, config=config)
    except Exception as exc:
        _log.exception("[lg-ses][runs] graph=%s failed", graph_id)
        raise HTTPException(status_code=500, detail=str(exc)[:300])

    # Serialise pydantic state object
    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
        # Convert enums to values for JSON
        for k, v in result_dict.items():
            if hasattr(v, "value"):
                result_dict[k] = v.value
    else:
        result_dict = dict(result)

    return {
        "ok": result_dict.get("status") in (
            RunStatus.COMPLETED.value, RunStatus.COMPLETED_WITH_ERROR.value
        ),
        "graph": graph_id,
        "duration_ms": int((time.time() - t0) * 1000),
        "result": result_dict,
    }


# ── MCP helpers (sync, called via asyncio.to_thread) ──────────────────────────

def _ses_mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "ai.gftd.apps.ses.listAnken",
            "description": "List SES 案件 with optional jokyo status filter.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "jokyo": {"type": "string", "description": "Comma-separated jokyo values to filter on (optional)"},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        },
        {
            "name": "ai.gftd.apps.ses.getAnken",
            "description": "Get 案件 detail with jokyo transition log.",
            "inputSchema": {
                "type": "object",
                "required": ["ankenId"],
                "properties": {
                    "ankenId": {"type": "string", "description": "vertex_id of the 案件"},
                },
            },
        },
        {
            "name": "ai.gftd.apps.ses.listJokyo",
            "description": "List jokyo transition log for a given 案件.",
            "inputSchema": {
                "type": "object",
                "required": ["ankenId"],
                "properties": {
                    "ankenId": {"type": "string"},
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0},
                },
            },
        },
    ]


def _list_anken(args: dict[str, Any]) -> dict[str, Any]:
    from pymagatama.db_sync import sync_cursor

    limit = max(1, min(int(args.get("limit", 50)), 200))
    offset = max(0, int(args.get("offset", 0)))
    jokyo_raw = str(args.get("jokyo", "") or "").strip()
    jokyo_filter = [j.strip() for j in jokyo_raw.split(",") if j.strip()] if jokyo_raw else []

    where_clause = ""
    params: list[Any] = []
    if jokyo_filter:
        placeholders = ",".join(["%s"] * len(jokyo_filter))
        where_clause = f"""
        WHERE (
            SELECT jokyo FROM vertex_ses_jokyo
            WHERE anken_vertex_id = a.vertex_id
            ORDER BY created_at DESC LIMIT 1
        ) IN ({placeholders})
        """
        params.extend(jokyo_filter)

    sql = f"""
    SELECT
        a.vertex_id,
        a.client_name,
        a.client_company,
        a.start_month,
        a.end_month,
        a.rate_lower_yen,
        a.rate_upper_yen,
        a.work_location,
        a.remote_ok,
        a.created_at,
        (
            SELECT jokyo FROM vertex_ses_jokyo
            WHERE anken_vertex_id = a.vertex_id
            ORDER BY created_at DESC LIMIT 1
        ) AS jokyo_current
    FROM vertex_ses_anken a
    {where_clause}
    ORDER BY a.created_at DESC
    LIMIT {limit} OFFSET {offset}
    """

    count_sql = f"""
    SELECT COUNT(*) AS cnt FROM vertex_ses_anken a
    {where_clause}
    """

    with sync_cursor() as cur:
        cur.execute(count_sql, params or None)
        row = cur.fetchone()
        total = int(row[0]) if row else 0

        cur.execute(sql, params or None)
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]

    anken = []
    for r in rows:
        rec = dict(zip(cols, r))
        anken.append({
            "vertexId": rec.get("vertex_id", ""),
            "clientName": rec.get("client_name", ""),
            "clientCompany": rec.get("client_company", ""),
            "jokyoCurrent": rec.get("jokyo_current") or "",
            "startMonth": rec.get("start_month") or "",
            "endMonth": rec.get("end_month") or "",
            "rateLowerYen": rec.get("rate_lower_yen"),
            "rateUpperYen": rec.get("rate_upper_yen"),
            "workLocation": rec.get("work_location") or "",
            "remoteOk": bool(rec.get("remote_ok")),
            "createdAt": str(rec.get("created_at", "")),
        })

    return {"anken": anken, "total": total, "offset": offset, "limit": limit}


def _get_anken(args: dict[str, Any]) -> dict[str, Any]:
    from pymagatama.db_sync import sync_cursor

    anken_id = str(args.get("ankenId", "")).strip()
    if not anken_id:
        raise ValueError("ankenId is required")

    sql = """
    SELECT
        a.vertex_id, a.client_name, a.client_company,
        a.skill_reqs_json, a.start_month, a.end_month,
        a.rate_lower_yen, a.rate_upper_yen, a.work_location,
        a.remote_ok, a.notes, a.source_kind, a.created_at,
        (
            SELECT jokyo FROM vertex_ses_jokyo
            WHERE anken_vertex_id = a.vertex_id
            ORDER BY created_at DESC LIMIT 1
        ) AS jokyo_current
    FROM vertex_ses_anken a
    WHERE a.vertex_id = %s
    LIMIT 1
    """

    jokyo_sql = """
    SELECT vertex_id, jokyo, rationale, actor_did, created_at
    FROM vertex_ses_jokyo
    WHERE anken_vertex_id = %s
    ORDER BY created_at DESC
    LIMIT 100
    """

    with sync_cursor() as cur:
        cur.execute(sql, (anken_id,))
        row = cur.fetchone()
        cols = [d[0] for d in (cur.description or [])]
        if not row:
            raise ValueError(f"anken not found: {anken_id}")
        rec = dict(zip(cols, row))

        cur.execute(jokyo_sql, (anken_id,))
        jokyo_rows = cur.fetchall()
        jokyo_cols = [d[0] for d in (cur.description or [])]

    skill_csv = ""
    try:
        skill_list = json_lib.loads(rec.get("skill_reqs_json") or "[]")
        skill_csv = ",".join(str(s) for s in skill_list) if isinstance(skill_list, list) else str(skill_list)
    except Exception:
        pass

    anken = {
        "vertexId": rec.get("vertex_id", ""),
        "clientName": rec.get("client_name", ""),
        "clientCompany": rec.get("client_company", ""),
        "skillCsv": skill_csv,
        "jokyoCurrent": rec.get("jokyo_current") or "",
        "startMonth": rec.get("start_month") or "",
        "endMonth": rec.get("end_month") or "",
        "rateLowerYen": rec.get("rate_lower_yen"),
        "rateUpperYen": rec.get("rate_upper_yen"),
        "workLocation": rec.get("work_location") or "",
        "remoteOk": bool(rec.get("remote_ok")),
        "notes": rec.get("notes") or "",
        "sourceKind": rec.get("source_kind") or "",
        "sourceEmailFrom": "",
        "sourceEmailSubject": "",
        "createdAt": str(rec.get("created_at", "")),
    }

    jokyo_log = []
    for jr in jokyo_rows:
        jrec = dict(zip(jokyo_cols, jr))
        jokyo_log.append({
            "vertexId": jrec.get("vertex_id", ""),
            "jokyo": jrec.get("jokyo", ""),
            "jokyoPrev": None,
            "notes": jrec.get("rationale") or "",
            "createdAt": str(jrec.get("created_at", "")),
        })

    return {"anken": anken, "jokyoLog": jokyo_log}


def _list_jokyo(args: dict[str, Any]) -> dict[str, Any]:
    from pymagatama.db_sync import sync_cursor

    anken_id = str(args.get("ankenId", "")).strip()
    if not anken_id:
        raise ValueError("ankenId is required")

    limit = max(1, min(int(args.get("limit", 50)), 200))
    offset = max(0, int(args.get("offset", 0)))

    count_sql = "SELECT COUNT(*) FROM vertex_ses_jokyo WHERE anken_vertex_id = %s"

    sql = f"""
    SELECT vertex_id, jokyo, rationale, actor_did, created_at
    FROM vertex_ses_jokyo
    WHERE anken_vertex_id = %s
    ORDER BY created_at DESC
    LIMIT {limit} OFFSET {offset}
    """

    with sync_cursor() as cur:
        cur.execute(count_sql, (anken_id,))
        cnt_row = cur.fetchone()
        total = int(cnt_row[0]) if cnt_row else 0

        cur.execute(sql, (anken_id,))
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]

    jokyo = []
    for r in rows:
        rec = dict(zip(cols, r))
        jokyo.append({
            "vertexId": rec.get("vertex_id", ""),
            "jokyo": rec.get("jokyo", ""),
            "jokyoPrev": None,
            "changedByDid": rec.get("actor_did") or "",
            "notes": rec.get("rationale") or "",
            "createdAt": str(rec.get("created_at", "")),
        })

    return {"jokyo": jokyo, "total": total, "offset": offset, "limit": limit}


def _call_ses_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "ai.gftd.apps.ses.listAnken":
        return _list_anken(args)
    if name == "ai.gftd.apps.ses.getAnken":
        return _get_anken(args)
    if name == "ai.gftd.apps.ses.listJokyo":
        return _list_jokyo(args)
    raise ValueError(f"unknown tool: {name}")


@app.post("/mcp")
async def _mcp(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
) -> JSONResponse:
    _enforce_auth(x_api_key)

    body = await request.json()
    rpc_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params") or {}

    if method in ("initialize", "ping"):
        return JSONResponse({"jsonrpc": "2.0", "id": rpc_id, "result": {}})

    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {"tools": _ses_mcp_tools()},
        })

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}
        try:
            result = await asyncio.to_thread(_call_ses_tool, tool_name, tool_args)
        except ValueError as exc:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": str(exc)}},
                status_code=400,
            )
        except Exception as exc:
            _log.exception("[lg-ses][mcp] tool=%s failed", tool_name)
            return JSONResponse(
                {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32000, "message": str(exc)[:300]}},
                status_code=500,
            )
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "content": [{"type": "text", "text": json_lib.dumps(result, ensure_ascii=False)}],
                "structuredContent": result,
            },
        })

    return JSONResponse(
        {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"Method not found: {method}"}},
        status_code=404,
    )
