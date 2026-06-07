"""LangGraph OSS FastAPI server — lg-organism.

22 tasks across 7 organism workers:
  hakkou (3): createFermentRecord, llmTransform, finalizeFerment
  kabi    (1): anastomosisProbe
  ki      (4): absorb, synthesize, bloom, ring
  kinoko  (1): checkFlowThreshold
  kobo    (3): budAgent, sporulate, germinate
  koke    (5): scanRawSignals, fixSignal, classifyFixation, handoffToHakkou, handoffToSaikin
  saikin  (5): probeEnvironment, transferSignal, formColony, lyse, handoffToKi
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

from kotodama.hakkou_worker_main import (
    task_create_ferment_record,
    task_finalize_ferment,
    task_llm_transform,
)
from kotodama.kabi_worker_main import task_anastomosis_probe
from kotodama.ki_worker_main import task_absorb, task_bloom, task_ring, task_synthesize
from kotodama.kinoko_worker_main import task_check_flow_threshold
from kotodama.kobo_worker_main import task_bud_agent, task_germinate, task_sporulate
from kotodama.koke_worker_main import (
    task_classify_fixation,
    task_fix_signal,
    task_handoff_to_hakkou,
    task_handoff_to_saikin,
    task_scan_raw_signals,
)
from kotodama.saikin_worker_main import (
    task_form_colony,
    task_handoff_to_ki,
    task_lyse,
    task_probe_environment,
    task_transfer_signal,
)

log = logging.getLogger(__name__)


class _State(TypedDict, total=False):
    input: dict
    result: dict | None
    error: str | None


def _make_single_node_graph(handler: Any, name: str):
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
        return {"result": {"status": "ok", "service": "lg-organism"}}

    g = StateGraph(_State)
    g.add_node("ping", _node)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g.compile(name="health")


TASKS: dict[str, Any] = {
    # hakkou
    "com.etzhayyim.hakkou.createFermentRecord": task_create_ferment_record,
    "com.etzhayyim.hakkou.llmTransform":        task_llm_transform,
    "com.etzhayyim.hakkou.finalizeFerment":     task_finalize_ferment,
    # kabi
    "com.etzhayyim.apps.kabi.anastomosisProbe":      task_anastomosis_probe,
    # ki
    "com.etzhayyim.ki.absorb":                  task_absorb,
    "com.etzhayyim.ki.synthesize":              task_synthesize,
    "com.etzhayyim.ki.bloom":                   task_bloom,
    "com.etzhayyim.ki.ring":                    task_ring,
    # kinoko
    "com.etzhayyim.apps.kinoko.checkFlowThreshold":  task_check_flow_threshold,
    # kobo
    "com.etzhayyim.apps.kobo.budAgent":              task_bud_agent,
    "com.etzhayyim.apps.kobo.sporulate":             task_sporulate,
    "com.etzhayyim.apps.kobo.germinate":             task_germinate,
    # koke
    "com.etzhayyim.koke.scanRawSignals":        task_scan_raw_signals,
    "com.etzhayyim.koke.fixSignal":             task_fix_signal,
    "com.etzhayyim.koke.classifyFixation":      task_classify_fixation,
    "com.etzhayyim.koke.handoffToHakkou":       task_handoff_to_hakkou,
    "com.etzhayyim.koke.handoffToSaikin":       task_handoff_to_saikin,
    # saikin
    "com.etzhayyim.apps.saikin.probeEnvironment":    task_probe_environment,
    "com.etzhayyim.apps.saikin.transferSignal":      task_transfer_signal,
    "com.etzhayyim.apps.saikin.formColony":          task_form_colony,
    "com.etzhayyim.apps.saikin.lyse":               task_lyse,
    "com.etzhayyim.apps.saikin.handoffToKi":        task_handoff_to_ki,
}

GRAPHS: dict[str, Any] = {"health": _make_health_graph()}
GRAPHS.update({
    nsid.rsplit(".", 1)[-1]: _make_single_node_graph(handler, nsid.rsplit(".", 1)[-1])
    for nsid, handler in TASKS.items()
})

_NSID_TO_ASSISTANT: dict[str, str] = {"com.etzhayyim.apps.organism.health": "health"}
for _nsid in TASKS:
    _NSID_TO_ASSISTANT[_nsid] = _nsid.rsplit(".", 1)[-1]


def _safe_json(obj: Any) -> Any:
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    log.info("lg-organism startup — %d graphs loaded", len(GRAPHS))
    yield
    log.info("lg-organism shutdown")


app = FastAPI(title="lg-organism", lifespan=_lifespan)


@app.get("/ok")
async def ok():
    return {"ok": True}


@app.get("/health")
async def health():
    state = await GRAPHS["health"].ainvoke({"input": {}})
    return JSONResponse(state.get("result") or {"status": "ok"})


@app.post("/runs")
async def runs(request: Request):
    body = await request.json()
    assistant_id: str = body.get("assistant_id", "health")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    t0 = time.monotonic()
    state = await graph.ainvoke({"input": body.get("input") or {}})
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse({"error": state["error"], "elapsed_s": round(elapsed, 3)}, status_code=500)
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


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

    t0 = time.monotonic()
    state = await graph.ainvoke({"input": body or {}})
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse({"error": state["error"], "elapsed_s": round(elapsed, 3)}, status_code=500)
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


@app.get("/xrpc/{nsid:path}")
async def xrpc_get(nsid: str, request: Request):
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if assistant_id is None:
        raise HTTPException(status_code=501, detail=f"NSID not mapped: {nsid}")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    t0 = time.monotonic()
    state = await graph.ainvoke({"input": dict(request.query_params)})
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse({"error": state["error"], "elapsed_s": round(elapsed, 3)}, status_code=500)
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})
