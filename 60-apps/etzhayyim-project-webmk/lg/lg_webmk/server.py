"""OSS FastAPI server for lg-webmk (mirrors lg-jukyu pattern).

Endpoints:
  POST /runs                  → invoke a graph synchronously
  POST /runs/stream           → stream graph events as SSE
  POST /xrpc/{nsid}           → XRPC-compat shim (NSID → assistant_id)
  GET  /threads/{tid}/state   → fetch latest checkpoint
  GET  /ok / /health          → liveness / readiness

NSID surface (4 webmk endpoints):
  com.etzhayyim.apps.webmk.createProposal    → create_proposal
  com.etzhayyim.apps.webmk.deliverProposal   → deliver_proposal
  com.etzhayyim.apps.webmk.getProposal       → get_proposal
  com.etzhayyim.apps.webmk.listProposals     → list_proposals
  com.etzhayyim.apps.webmk.health            → health
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Header, HTTPException, Path as FPath
from fastapi.responses import StreamingResponse

from lg_webmk.checkpointer import build_checkpointer
from lg_webmk.graphs.create_proposal import GRAPH as CREATE_PROPOSAL
from lg_webmk.graphs.deliver_proposal import GRAPH as DELIVER_PROPOSAL
from lg_webmk.graphs.get_proposal import GRAPH as GET_PROPOSAL
from lg_webmk.graphs.health import GRAPH as HEALTH
from lg_webmk.graphs.list_proposals import GRAPH as LIST_PROPOSALS

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":           HEALTH,
    "create_proposal":  CREATE_PROPOSAL,
    "deliver_proposal": DELIVER_PROPOSAL,
    "get_proposal":     GET_PROPOSAL,
    "list_proposals":   LIST_PROPOSALS,
}

# NSID → assistant_id mapping
_NSID_MAP: dict[str, str] = {
    "com.etzhayyim.apps.webmk.health":           "health",
    "com.etzhayyim.apps.webmk.createProposal":   "create_proposal",
    "com.etzhayyim.apps.webmk.deliverProposal":  "deliver_proposal",
    "com.etzhayyim.apps.webmk.getProposal":      "get_proposal",
    "com.etzhayyim.apps.webmk.listProposals":    "list_proposals",
}

_QUERY_NSIDS = {"com.etzhayyim.apps.webmk.health", "com.etzhayyim.apps.webmk.getProposal", "com.etzhayyim.apps.webmk.listProposals"}

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
    _log.info("lg-webmk server up: graphs=%s", list(bound))
    try:
        yield
    finally:
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-webmk OSS server", version="0.1.0", lifespan=_lifespan)


def _require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/ok")
@app.get("/health")
async def liveness() -> dict[str, Any]:
    return {"ok": True, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


@app.post("/runs")
async def run_graph(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _require_api_key(x_api_key)
    assistant_id = body.get("assistant_id", "")
    graphs: dict[str, Any] = app.state.graphs
    g = graphs.get(assistant_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")
    inputs = body.get("input", {})
    config = body.get("config", {})
    config.setdefault("configurable", {}).setdefault("thread_id", f"run-{int(time.time_ns())}")
    try:
        result = await g.ainvoke(inputs, config=config)
        return {"ok": True, "output": result}
    except Exception as exc:  # noqa: BLE001
        _log.error("run_graph failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/runs/stream")
async def stream_graph(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> StreamingResponse:
    _require_api_key(x_api_key)
    assistant_id = body.get("assistant_id", "")
    graphs: dict[str, Any] = app.state.graphs
    g = graphs.get(assistant_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")
    inputs = body.get("input", {})
    config = body.get("config", {})
    config.setdefault("configurable", {}).setdefault("thread_id", f"stream-{int(time.time_ns())}")

    async def _gen():
        async for event in g.astream(inputs, config=config, stream_mode="updates"):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@app.post("/xrpc/{nsid:path}")
@app.get("/xrpc/{nsid:path}")
async def xrpc(nsid: str = FPath(...), body: dict[str, Any] | None = None) -> dict[str, Any]:
    if body is None:
        body = {}
    assistant_id = _NSID_MAP.get(nsid)
    if not assistant_id:
        raise HTTPException(status_code=404, detail=f"NSID '{nsid}' not mapped")
    graphs: dict[str, Any] = app.state.graphs
    g = graphs[assistant_id]
    config = {"configurable": {"thread_id": f"xrpc-{int(time.time_ns())}"}}
    try:
        result = await g.ainvoke(body, config=config)
        # For query NSIDs return 200 verbatim; for procedures wrap if needed
        return result
    except Exception as exc:  # noqa: BLE001
        _log.error("xrpc failed nsid=%s: %s", nsid, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str = FPath(...)) -> dict[str, Any]:
    cp = app.state.checkpointer
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await cp.aget(config)
        if not state:
            raise HTTPException(status_code=404, detail="thread not found")
        return {"thread_id": thread_id, "checkpoint_id": state.config["configurable"].get("checkpoint_id"), "values": state.values}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
