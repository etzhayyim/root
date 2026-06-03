"""LangGraph OSS FastAPI server — open-jpn-mynumber.

Wraps all 17 task handlers from open_jpn_mynumber_worker.TASKS plus a health
graph.  Handlers use snake_case parameter names; XRPC inputs arrive in
camelCase, so _camel_to_snake is applied before unpacking into the graph.

No postgres checkpointer — stateless request-response graphs only.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

# ---------------------------------------------------------------------------
# Worker import (resolved via PYTHONPATH=/opt/open_jpn_mynumber_worker)
# ---------------------------------------------------------------------------
from open_jpn_mynumber_worker import TASKS  # noqa: E402

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State schema — single `input` channel so LangGraph does not drop kwargs
# ---------------------------------------------------------------------------

class _State(TypedDict, total=False):
    input: dict
    result: dict | None
    error: str | None


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def _make_single_node_graph(handler: Any, name: str):
    async def _node(state: _State) -> dict:
        kwargs = state.get("input") or {}
        try:
            return {"result": await handler(**kwargs)}
        except Exception as exc:  # noqa: BLE001
            log.exception("graph %s node error", name)
            return {"error": str(exc)[:300]}

    g = StateGraph(_State)
    g.add_node("execute", _node)
    g.add_edge(START, "execute")
    g.add_edge("execute", END)
    return g.compile(name=name)


def _make_health_graph():
    async def _node(state: _State) -> dict:
        return {"result": {"status": "ok", "service": "lg-open-jpn-mynumber"}}

    g = StateGraph(_State)
    g.add_node("ping", _node)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g.compile(name="health")


# ---------------------------------------------------------------------------
# Build GRAPHS dict: health + one graph per NSID tail
# ---------------------------------------------------------------------------

GRAPHS: dict[str, Any] = {"health": _make_health_graph()}
GRAPHS.update(
    {
        nsid.rsplit(".", 1)[-1]: _make_single_node_graph(handler, nsid.rsplit(".", 1)[-1])
        for nsid, handler in TASKS.items()
    }
)

# NSID → assistant_id map
_NSID_TO_ASSISTANT: dict[str, str] = {
    "com.etzhayyim.apps.openJpnMynumber.health": "health",
}
for _nsid in TASKS:
    _NSID_TO_ASSISTANT[_nsid] = _nsid.rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _camel_to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def _safe_json(obj: Any) -> Any:
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    log.info("lg-open-jpn-mynumber startup — %d graphs loaded", len(GRAPHS))
    yield
    log.info("lg-open-jpn-mynumber shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="lg-open-jpn-mynumber", lifespan=_lifespan)


@app.get("/ok")
async def ok():
    return {"ok": True}


@app.get("/health")
async def health():
    state = await GRAPHS["health"].ainvoke({"input": {}})
    return JSONResponse(state.get("result") or {"status": "ok"})


# ---------------------------------------------------------------------------
# /runs — invoke a graph by assistant_id
# ---------------------------------------------------------------------------

@app.post("/runs")
async def runs(request: Request):
    body = await request.json()
    assistant_id: str = body.get("assistant_id", "health")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    raw_input: dict = body.get("input") or {}
    # Handlers use snake_case; convert camelCase keys from callers
    snake_input = {_camel_to_snake(k): v for k, v in raw_input.items()}
    graph_input = {"input": snake_input}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


# ---------------------------------------------------------------------------
# /xrpc/{nsid} — AT Protocol / bpmn-dispatcher entry point
# ---------------------------------------------------------------------------

@app.post("/xrpc/{nsid:path}")
async def xrpc_post(nsid: str, request: Request):
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if assistant_id is None:
        raise HTTPException(status_code=501, detail=f"NSID not mapped: {nsid}")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    ct = request.headers.get("content-type", "")
    if "application/json" in ct:
        body = await request.json()
    else:
        body = {}

    # Handlers use snake_case; convert camelCase XRPC input keys
    snake_input = {_camel_to_snake(k): v for k, v in (body or {}).items()}
    graph_input = {"input": snake_input}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


@app.get("/xrpc/{nsid:path}")
async def xrpc_get(nsid: str, request: Request):
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if assistant_id is None:
        raise HTTPException(status_code=501, detail=f"NSID not mapped: {nsid}")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    params = dict(request.query_params)
    snake_input = {_camel_to_snake(k): v for k, v in params.items()}
    graph_input = {"input": snake_input}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})
