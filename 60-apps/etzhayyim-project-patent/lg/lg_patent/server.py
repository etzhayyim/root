"""lg-patent OSS FastAPI server.

HTTP surface:
  POST /runs              → invoke graph synchronously
  POST /runs/stream       → stream graph events as SSE
  POST /xrpc/{nsid}       → XRPC shim (NSID → graph mapping)
  GET  /threads/{tid}/state → fetch latest checkpoint
  GET  /ok / /health      → liveness / readiness

NSID namespace: com.etzhayyim.apps.patent.*
Auth: optional LG_API_KEY env enforces x-api-key on /runs.
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

from lg_patent.checkpointer import build_checkpointer
from lg_patent.cron import start_cron, stop_cron
from lg_patent.graphs.health import GRAPH as HEALTH
from lg_patent.graphs.blob_convert import GRAPH as BLOB_CONVERT
from lg_patent.graphs.ingest_uspto_weekly import GRAPH as INGEST_USPTO_WEEKLY

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":               HEALTH,
    "blob_convert":         BLOB_CONVERT,
    "ingest_uspto_weekly":  INGEST_USPTO_WEEKLY,
}

NSID_MAP: dict[str, str] = {
    "com.etzhayyim.apps.patent.blobConvert":        "blob_convert",
    "com.etzhayyim.apps.patent.ingestUsptoWeekly":  "ingest_uspto_weekly",
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

    _log.info("lg-patent up: graphs=%s", list(bound))
    try:
        yield
    finally:
        await stop_cron(scheduler)
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-patent OSS server", version="0.1.0", lifespan=_lifespan)


def _auth(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    if _API_KEY and (not x_api_key or x_api_key != _API_KEY):
        raise HTTPException(status_code=401, detail="invalid x-api-key")


@app.get("/health")
@app.get("/ok")
async def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-patent",
        "ts": int(time.time() * 1000),
        "graphs": list(GRAPHS),
    }


@app.get("/graphs")
async def _list_graphs() -> dict[str, Any]:
    return {"graphs": list(GRAPHS)}


@app.post("/runs", dependencies=[Depends(_auth)])
async def _runs(body: dict[str, Any]) -> dict[str, Any]:
    assistant_id: str = body.get("assistant_id", "health")
    graph_name = NSID_MAP.get(assistant_id, assistant_id)
    graphs: dict[str, Any] = app.state.graphs
    if graph_name not in graphs:
        raise HTTPException(status_code=404, detail=f"graph {graph_name!r} not found")
    thread_id: str = (body.get("config") or {}).get("configurable", {}).get("thread_id") or f"run-{int(time.time())}"
    inp: dict[str, Any] = body.get("input") or {}
    try:
        result = await graphs[graph_name].ainvoke(
            inp,
            config={"configurable": {"thread_id": thread_id}},
        )
        return {"ok": True, "result": result, "thread_id": thread_id}
    except Exception as exc:
        _log.exception("graph %s failed", graph_name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/runs/stream", dependencies=[Depends(_auth)])
async def _runs_stream(body: dict[str, Any]) -> StreamingResponse:
    assistant_id: str = body.get("assistant_id", "health")
    graph_name = NSID_MAP.get(assistant_id, assistant_id)
    graphs: dict[str, Any] = app.state.graphs
    if graph_name not in graphs:
        raise HTTPException(status_code=404, detail=f"graph {graph_name!r} not found")
    thread_id: str = (body.get("config") or {}).get("configurable", {}).get("thread_id") or f"stream-{int(time.time())}"
    inp: dict[str, Any] = body.get("input") or {}

    async def _gen() -> AsyncIterator[str]:
        async for event in graphs[graph_name].astream_events(
            inp,
            config={"configurable": {"thread_id": thread_id}},
            version="v2",
        ):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.post("/xrpc/{nsid}")
async def _xrpc(nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    graph_name = NSID_MAP.get(nsid)
    if not graph_name:
        raise HTTPException(status_code=404, detail=f"NSID {nsid!r} not mapped")
    graphs: dict[str, Any] = app.state.graphs
    thread_id = f"xrpc-{nsid}-{int(time.time())}"
    try:
        result = await graphs[graph_name].ainvoke(
            body,
            config={"configurable": {"thread_id": thread_id}},
        )
        return {"ok": True, "result": result}
    except Exception as exc:
        _log.exception("xrpc %s failed", nsid)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/threads/{thread_id}/state")
async def _thread_state(thread_id: str) -> dict[str, Any]:
    cp = app.state.checkpointer
    if cp is None:
        raise HTTPException(status_code=503, detail="no checkpointer configured")
    try:
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await GRAPHS["health"].aget_state(config)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="thread not found")
        return {"thread_id": thread_id, "values": snapshot.values, "next": list(snapshot.next)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
