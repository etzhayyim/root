"""OSS FastAPI server for lg-x (mirrors lg-shinshi pattern).

Provides the same minimal HTTP surface:
  POST /runs              → invoke a graph synchronously
  POST /runs/stream       → stream graph events as SSE
  POST /xrpc/{nsid}       → XRPC-compat shim (NSID → assistant_id mapping)
  GET  /threads/{tid}/state → fetch latest checkpoint
  GET  /ok / /health      → liveness / readiness

Auth: optional `LG_API_KEY` env enforces `x-api-key` on /runs paths.
The /xrpc/{nsid} surface is unauthenticated (trust at the cloudflared
tunnel layer, same pattern as lg-shinshi).

X NSID namespace covers ~13 task types; the initial scaffold
ports `health`, `listWorks`, `chat`. Other NSIDs return 404 until
their corresponding graph is ported (P3+).
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

from lg_x.checkpointer import build_checkpointer
from lg_x.cron import start_cron, stop_cron
from lg_x.graphs.agent_chat import GRAPH as AGENT_CHAT
from lg_x.graphs.compose_tweet import GRAPH as COMPOSE_TWEET
from lg_x.graphs.health import GRAPH as HEALTH

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":     HEALTH,
    "compose_tweet": COMPOSE_TWEET,
    "agent_chat":    AGENT_CHAT,
    "agent_chat": AGENT_CHAT,
}

_API_KEY = os.environ.get("LG_API_KEY", "").strip()


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    cp_ctx = build_checkpointer()
    cp = await cp_ctx.__aenter__()
    app.state.checkpointer = cp
    app.state.cp_ctx = cp_ctx

    bound: dict[str, Any] = {}
    for name, g in GRAPHS.items():
        try:
            bound[name] = g.with_config({"checkpointer": cp})
        except Exception:  # noqa: BLE001
            try:
                g.checkpointer = cp
            except Exception:
                pass
            bound[name] = g
    app.state.graphs = bound

    scheduler = start_cron(bound)
    app.state.scheduler = scheduler

    _log.info("lg-x server up: graphs=%s crons=%s",
              list(bound), bool(scheduler))
    try:
        yield
    finally:
        await stop_cron(scheduler)
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-x OSS server", version="0.1.0", lifespan=_lifespan)


def _require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="invalid x-api-key")


@app.get("/ok")
async def ok() -> dict[str, Any]:
    return {"ok": True, "graphs": list(GRAPHS.keys()), "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, Any]:
    cp_ok = hasattr(app.state, "checkpointer") and app.state.checkpointer is not None
    return {"ok": cp_ok, "checkpointer": cp_ok}


@app.post("/runs", dependencies=[Depends(_require_api_key)])
async def create_run(body: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(body.get("assistant_id") or "")
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")
    graph = app.state.graphs[assistant_id]
    input_data = body.get("input") or {}
    config = body.get("config") or {}

    started = time.monotonic()
    try:
        result = await graph.ainvoke(input_data, config=config)
        return {
            "ok": True, "result": result, "assistantId": assistant_id,
            "latencyMs": int((time.monotonic() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        _log.exception("graph %s failed", assistant_id)
        return {
            "ok": False, "error": str(exc)[:500],
            "errorType": type(exc).__name__, "assistantId": assistant_id,
            "latencyMs": int((time.monotonic() - started) * 1000),
        }


@app.post("/runs/stream", dependencies=[Depends(_require_api_key)])
async def stream_run(body: dict[str, Any]) -> StreamingResponse:
    assistant_id = str(body.get("assistant_id") or "")
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")
    graph = app.state.graphs[assistant_id]
    input_data = body.get("input") or {}
    config = body.get("config") or {}
    stream_mode = body.get("stream_mode") or "values"

    async def _gen() -> AsyncIterator[bytes]:
        try:
            async for chunk in graph.astream(input_data, config=config, stream_mode=stream_mode):
                yield f"data: {json.dumps({'event':'values','data':_safe_json(chunk)})}\n\n".encode()
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'event':'error','data':str(exc)[:500]})}\n\n".encode()

    return StreamingResponse(_gen(), media_type="text/event-stream")


# ── XRPC-compat surface (NSID → assistant_id) ──────────────────────────

_NSID_TO_ASSISTANT: dict[str, str] = {
    "com.etzhayyim.apps.x.health":        "health",
    "com.etzhayyim.apps.x.composeTweet": "compose_tweet",
    "com.etzhayyim.apps.x.chat":          "agent_chat",
    "com.etzhayyim.apps.x.agentChat":     "agent_chat",
}


def _camel_to_snake(s: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(s):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _xrpc_input_to_graph_input(_nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    return {_camel_to_snake(k): v for k, v in (body or {}).items()}


@app.post("/xrpc/{nsid}")
async def xrpc_compat(nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if not assistant_id:
        raise HTTPException(status_code=404, detail=f"unknown NSID: {nsid}")
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=503, detail=f"graph not loaded: {assistant_id}")

    graph = app.state.graphs[assistant_id]
    graph_input = _xrpc_input_to_graph_input(nsid, body)
    bucket = int(time.time()) // 1800
    thread_id = f"xrpc:{nsid.split('.')[-1]}:{bucket}"
    config = {"configurable": {"thread_id": thread_id}}

    started = time.monotonic()
    try:
        result = await graph.ainvoke(graph_input, config=config)
    except Exception as exc:  # noqa: BLE001
        _log.exception("xrpc graph %s failed", assistant_id)
        return {
            "error": f"lg-x {type(exc).__name__}",
            "errorDetail": str(exc)[:300],
            "assistantId": assistant_id,
            "latencyMs": int((time.monotonic() - started) * 1000),
        }

    if isinstance(result, dict):
        out = dict(result)
    else:
        out = {"result": _safe_json(result)}
    out["latencyMs"] = int((time.monotonic() - started) * 1000)
    out["assistantId"] = assistant_id
    return out


@app.get("/threads/{thread_id}/state", dependencies=[Depends(_require_api_key)])
async def get_thread_state(thread_id: str, assistant_id: str) -> dict[str, Any]:
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")
    graph = app.state.graphs[assistant_id]
    snap = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    return {
        "values": _safe_json(snap.values),
        "next": list(snap.next),
        "tasks": [
            {"id": t.id, "name": t.name, "error": str(t.error) if t.error else None}
            for t in (snap.tasks or [])
        ],
    }


# ── helpers ────────────────────────────────────────────────────────────


def _safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}B>"
    return repr(value)[:200]
