"""lg-open-patent OSS FastAPI server.

HTTP surface:
  POST /runs              → invoke graph synchronously
  POST /runs/stream       → stream graph events as SSE
  POST /xrpc/{nsid}       → XRPC shim (NSID → graph mapping)
  GET  /threads/{tid}/state → fetch latest checkpoint
  GET  /ok / /health      → liveness / readiness

NSID namespace: com.etzhayyim.apps.openPatent.*
Auth: optional LG_API_KEY env enforces x-api-key on /runs.
      /xrpc/{nsid} is unauthenticated (trust at cloudflared tunnel layer).
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

from lg_open_patent.checkpointer import build_checkpointer
from lg_open_patent.cron import start_cron, stop_cron
from lg_open_patent.graphs.health import GRAPH as HEALTH
from lg_open_patent.graphs.ingest_multi import GRAPH as INGEST_MULTI
from lg_open_patent.graphs.synthesize_invention import GRAPH as SYNTHESIZE_INVENTION

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":               HEALTH,
    "ingest_multi":         INGEST_MULTI,
    "synthesize_invention": SYNTHESIZE_INVENTION,
}

NSID_MAP: dict[str, str] = {
    "com.etzhayyim.apps.openPatent.ingestMulti":         "ingest_multi",
    "com.etzhayyim.apps.openPatent.synthesizeInvention":  "synthesize_invention",
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
        except Exception:
            try:
                g.checkpointer = cp
            except Exception:
                pass
            bound[name] = g
    app.state.graphs = bound

    scheduler = start_cron(bound)
    app.state.scheduler = scheduler

    _log.info("lg-open-patent up: graphs=%s", list(bound))
    try:
        yield
    finally:
        await stop_cron(scheduler)
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-open-patent OSS server", version="0.1.0", lifespan=_lifespan)


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

    g = app.state.graphs[assistant_id]
    thread_id = str(body.get("thread_id") or f"run-{int(time.time())}")
    input_data = body.get("input") or {}

    try:
        result = await g.ainvoke(
            input_data,
            config={"configurable": {"thread_id": thread_id}},
        )
        return {"thread_id": thread_id, "status": "success", "output": result}
    except Exception as exc:
        _log.exception("graph %s failed: %s", assistant_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/runs/stream", dependencies=[Depends(_require_api_key)])
async def stream_run(body: dict[str, Any]) -> StreamingResponse:
    assistant_id = str(body.get("assistant_id") or "")
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")

    g = app.state.graphs[assistant_id]
    thread_id = str(body.get("thread_id") or f"run-{int(time.time())}")
    input_data = body.get("input") or {}

    async def _event_stream():
        try:
            async for event in g.astream_events(
                input_data,
                config={"configurable": {"thread_id": thread_id}},
                version="v2",
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            _log.exception("stream %s failed: %s", assistant_id, exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.post("/xrpc/{nsid}")
async def xrpc_shim(nsid: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    graph_name = NSID_MAP.get(nsid)
    if not graph_name:
        raise HTTPException(status_code=404, detail=f"unknown NSID: {nsid}")

    g = app.state.graphs.get(graph_name)
    if not g:
        raise HTTPException(status_code=503, detail=f"graph not ready: {graph_name}")

    input_data = body or {}
    thread_id = str(input_data.pop("threadId", f"xrpc-{int(time.time())}"))

    try:
        result = await g.ainvoke(
            input_data,
            config={"configurable": {"thread_id": thread_id}},
        )
        return {"ok": True, "thread_id": thread_id, **result}
    except Exception as exc:
        _log.exception("xrpc %s failed: %s", nsid, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str, assistant_id: str = "ingest_multi") -> dict[str, Any]:
    g = app.state.graphs.get(assistant_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")
    try:
        state = await g.aget_state({"configurable": {"thread_id": thread_id}})
        return {"thread_id": thread_id, "values": state.values if state else {}}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
