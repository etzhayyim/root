"""LangGraph OSS FastAPI server — lg-legal-entity.

16 tasks from kotodama.primitives.legal_entity:
  - gleif: fetchPages (async), registerDids (sync → asyncio.to_thread)
  - edgar: collectUsa, ingestSecDisclosure
  - registry: collectJpn/Gbr/Fra/Nor/Dnk/Fin/Est/Cze/Nzl/Che/Nld/Isr

Build:
  docker buildx build --platform linux/amd64 \\
    --build-context py=../../../40-engine/kotoba/crates/kotoba-kotodama/py \\
    -t ghcr.io/etzhayyim/lg-legal-entity:0.1.0-amd64 --push .
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from kotodama.primitives.legal_entity import (
    _make_registry_task,
    task_edgar_collect_usa,
    task_edgar_ingest_sec_disclosure,
    task_gleif_fetch_pages,
    task_gleif_register_dids,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class _State(TypedDict, total=False):
    input: dict
    result: dict | None
    error: str | None


# ---------------------------------------------------------------------------
# Graph factories
# ---------------------------------------------------------------------------

def _make_single_node_graph(handler: Any, name: str):
    """Handles both async and sync handlers."""
    is_coro = inspect.iscoroutinefunction(handler)

    async def _node(state: _State) -> dict:
        kwargs = state.get("input") or {}
        try:
            if is_coro:
                result = await handler(**kwargs)
            else:
                result = await asyncio.to_thread(handler, **kwargs)
            return {"result": result}
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
        return {"result": {"status": "ok", "service": "lg-legal-entity"}}

    g = StateGraph(_State)
    g.add_node("ping", _node)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g.compile(name="health")


# ---------------------------------------------------------------------------
# TASKS: NSID → handler
# task type legalEntity.X.Y → com.etzhayyim.legalEntity.XY
# ---------------------------------------------------------------------------

_REGISTRY_SUFFIXES = ["Jpn", "Gbr", "Fra", "Nor", "Dnk", "Fin", "Est", "Cze", "Nzl", "Che", "Nld", "Isr"]

TASKS: dict[str, Any] = {
    "com.etzhayyim.legalEntity.gleifFetchPages":         task_gleif_fetch_pages,
    "com.etzhayyim.legalEntity.gleifRegisterDids":       task_gleif_register_dids,
    "com.etzhayyim.legalEntity.edgarCollectUsa":         task_edgar_collect_usa,
    "com.etzhayyim.legalEntity.edgarIngestSecDisclosure": task_edgar_ingest_sec_disclosure,
    **{
        f"com.etzhayyim.legalEntity.registryCollect{s}": _make_registry_task(s)
        for s in _REGISTRY_SUFFIXES
    },
}

# ---------------------------------------------------------------------------
# GRAPHS dict + NSID → assistant map
# ---------------------------------------------------------------------------

GRAPHS: dict[str, Any] = {"health": _make_health_graph()}
GRAPHS.update({
    nsid.rsplit(".", 1)[-1]: _make_single_node_graph(handler, nsid.rsplit(".", 1)[-1])
    for nsid, handler in TASKS.items()
})

_NSID_TO_ASSISTANT: dict[str, str] = {"com.etzhayyim.legalEntity.health": "health"}
for _nsid in TASKS:
    _NSID_TO_ASSISTANT[_nsid] = _nsid.rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    log.info("lg-legal-entity startup — %d graphs loaded", len(GRAPHS))
    yield
    log.info("lg-legal-entity shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="lg-legal-entity", lifespan=_lifespan)


@app.get("/ok")
async def ok():
    return {"ok": True}


@app.get("/health")
async def health():
    state = await GRAPHS["health"].ainvoke({"input": {}})
    return JSONResponse(state.get("result") or {"status": "ok"})


# ---------------------------------------------------------------------------
# /runs
# ---------------------------------------------------------------------------

@app.post("/runs")
async def runs(request: Request):
    body = await request.json()
    assistant_id: str = body.get("assistant_id", "health")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    graph_input = {"input": body.get("input") or {}}

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
# /xrpc/{nsid}
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
    body = await request.json() if "application/json" in ct else {}

    graph_input = {"input": body or {}}

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

    graph_input = {"input": dict(request.query_params)}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})
