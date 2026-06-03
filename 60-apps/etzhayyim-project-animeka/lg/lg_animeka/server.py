"""OSS FastAPI server for lg-animeka (mirrors lg-shinshi pattern).

Provides the same minimal HTTP surface:
  POST /runs              → invoke a graph synchronously
  POST /runs/stream       → stream graph events as SSE
  POST /xrpc/{nsid}       → XRPC-compat shim (NSID → assistant_id mapping)
  GET  /threads/{tid}/state → fetch latest checkpoint
  GET  /ok / /health      → liveness / readiness

Auth: optional `LG_API_KEY` env enforces `x-api-key` on /runs paths.
The /xrpc/{nsid} surface is unauthenticated (trust at the cloudflared
tunnel layer, same pattern as lg-shinshi).

Animeka NSID namespace: 27 graphs live (publishEpisode added 2026-05-15).
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

from lg_animeka.checkpointer import build_checkpointer
from lg_animeka.cron import start_cron, stop_cron
from lg_animeka.nats_consumer import CONSUMER_GRAPHS, NatsConsumerManager
from lg_animeka.graphs.add_cut import GRAPH as ADD_CUT
from lg_animeka.graphs.add_episode import GRAPH as ADD_EPISODE
from lg_animeka.graphs.agent_chat import GRAPH as AGENT_CHAT
from lg_animeka.graphs.auto_trace_cut import GRAPH as AUTO_TRACE_CUT
from lg_animeka.graphs.autopilot import GRAPH as AUTOPILOT
from lg_animeka.graphs.breakdown_scene import GRAPH as BREAKDOWN_SCENE
from lg_animeka.graphs.create_work import GRAPH as CREATE_WORK
from lg_animeka.graphs.cut_runner import GRAPH as CUT_RUNNER
from lg_animeka.graphs.design_color_model import GRAPH as DESIGN_COLOR_MODEL
from lg_animeka.graphs.assemble_episode import GRAPH as ASSEMBLE_EPISODE
from lg_animeka.graphs.generate_audio import GRAPH as GENERATE_AUDIO
from lg_animeka.graphs.generate_background import GRAPH as GENERATE_BACKGROUND
from lg_animeka.graphs.publish_episode import GRAPH as PUBLISH_EPISODE
from lg_animeka.graphs.generate_inbetween import GRAPH as GENERATE_INBETWEEN
from lg_animeka.graphs.generate_keyframe import GRAPH as GENERATE_KEYFRAME
from lg_animeka.graphs.generate_layout import GRAPH as GENERATE_LAYOUT
from lg_animeka.graphs.generate_script import GRAPH as GENERATE_SCRIPT
from lg_animeka.graphs.generate_storyboard import GRAPH as GENERATE_STORYBOARD
from lg_animeka.graphs.get_cut import GRAPH as GET_CUT
from lg_animeka.graphs.health import GRAPH as HEALTH
from lg_animeka.graphs.list_cuts import GRAPH as LIST_CUTS
from lg_animeka.graphs.list_episodes import GRAPH as LIST_EPISODES
from lg_animeka.graphs.list_retakes import GRAPH as LIST_RETAKES
from lg_animeka.graphs.list_works import GRAPH as LIST_WORKS
from lg_animeka.graphs.resolve_retake import GRAPH as RESOLVE_RETAKE
from lg_animeka.graphs.submit_retake import GRAPH as SUBMIT_RETAKE
from lg_animeka.graphs.update_cut_stage import GRAPH as UPDATE_CUT_STAGE

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":             HEALTH,
    "list_works":         LIST_WORKS,
    "agent_chat":         AGENT_CHAT,
    "get_cut":            GET_CUT,
    "list_cuts":          LIST_CUTS,
    "list_episodes":      LIST_EPISODES,
    "list_retakes":       LIST_RETAKES,
    "create_work":        CREATE_WORK,
    "add_episode":        ADD_EPISODE,
    "add_cut":            ADD_CUT,
    "update_cut_stage":   UPDATE_CUT_STAGE,
    "submit_retake":      SUBMIT_RETAKE,
    "resolve_retake":     RESOLVE_RETAKE,
    "generate_script":      GENERATE_SCRIPT,
    "generate_storyboard":  GENERATE_STORYBOARD,
    "generate_layout":      GENERATE_LAYOUT,
    "generate_keyframe":    GENERATE_KEYFRAME,
    "generate_inbetween":   GENERATE_INBETWEEN,
    "generate_background":  GENERATE_BACKGROUND,
    "design_color_model":   DESIGN_COLOR_MODEL,
    "autopilot":            AUTOPILOT,
    "cut_runner":           CUT_RUNNER,
    "auto_trace_cut":       AUTO_TRACE_CUT,
    "breakdown_scene":      BREAKDOWN_SCENE,
    "generate_audio":       GENERATE_AUDIO,
    "assemble_episode":     ASSEMBLE_EPISODE,
    "publish_episode":      PUBLISH_EPISODE,
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

    # NATS JetStream consumers (autopilot / cutRunner / autoTraceCut / breakdownScene)
    consumer_graphs = {k: v for k, v in bound.items() if k in CONSUMER_GRAPHS}
    nats_mgr = NatsConsumerManager(consumer_graphs)
    await nats_mgr.start()
    app.state.nats_mgr = nats_mgr

    _log.info("lg-animeka server up: graphs=%s crons=%s nats=%s",
              list(bound), bool(scheduler), bool(consumer_graphs))
    try:
        yield
    finally:
        await nats_mgr.stop()
        await stop_cron(scheduler)
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-animeka OSS server", version="0.1.0", lifespan=_lifespan)


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
    "com.etzhayyim.animeka.health":            "health",
    "com.etzhayyim.animeka.listWorks":         "list_works",
    "com.etzhayyim.animeka.chat":              "agent_chat",
    "com.etzhayyim.animeka.getCut":            "get_cut",
    "com.etzhayyim.animeka.listCuts":          "list_cuts",
    "com.etzhayyim.animeka.listEpisodes":      "list_episodes",
    "com.etzhayyim.animeka.listRetakes":       "list_retakes",
    "com.etzhayyim.animeka.createWork":        "create_work",
    "com.etzhayyim.animeka.addEpisode":        "add_episode",
    "com.etzhayyim.animeka.addCut":            "add_cut",
    "com.etzhayyim.animeka.updateCutStage":    "update_cut_stage",
    "com.etzhayyim.animeka.submitRetake":      "submit_retake",
    "com.etzhayyim.animeka.resolveRetake":     "resolve_retake",
    "com.etzhayyim.animeka.generateScript":      "generate_script",
    "com.etzhayyim.animeka.generateStoryboard":  "generate_storyboard",
    "com.etzhayyim.animeka.generateLayout":      "generate_layout",
    "com.etzhayyim.animeka.generateKeyframe":    "generate_keyframe",
    "com.etzhayyim.animeka.generateInbetween":   "generate_inbetween",
    "com.etzhayyim.animeka.generateBackground":  "generate_background",
    "com.etzhayyim.animeka.designColorModel":    "design_color_model",
    "com.etzhayyim.animeka.autopilot":           "autopilot",
    "com.etzhayyim.animeka.cutRunner":           "cut_runner",
    "com.etzhayyim.animeka.autoTraceCut":        "auto_trace_cut",
    "com.etzhayyim.animeka.breakdownScene":      "breakdown_scene",
    "com.etzhayyim.animeka.generateAudio":       "generate_audio",
    "com.etzhayyim.animeka.assembleEpisode":     "assemble_episode",
    "com.etzhayyim.animeka.publishEpisode":      "publish_episode",
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
            "error": f"lg-animeka {type(exc).__name__}",
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


@app.get("/nats/status")
async def nats_status() -> dict[str, Any]:
    """NATS JetStream consumer status — readable by LLM / MCP tools."""
    mgr: NatsConsumerManager | None = getattr(app.state, "nats_mgr", None)
    if not mgr:
        return {"enabled": False, "error": "nats manager not initialized"}
    return await mgr.status()


@app.post("/nats/publish")
async def nats_publish(body: dict[str, Any]) -> dict[str, Any]:
    """Enqueue a graph invocation via NATS JetStream.

    Body: {"assistant_id": "autopilot", "input": {}}
    Equivalent to: nats pub com.etzhayyim.animeka.autopilot '{}'
    """
    assistant_id = str(body.get("assistant_id") or "")
    if assistant_id not in CONSUMER_GRAPHS:
        raise HTTPException(
            status_code=400,
            detail=f"not a queue-eligible graph: {assistant_id!r}. "
                   f"eligible: {sorted(CONSUMER_GRAPHS)}",
        )
    mgr: NatsConsumerManager | None = getattr(app.state, "nats_mgr", None)
    if not mgr:
        raise HTTPException(status_code=503, detail="NATS manager not initialized")
    payload = body.get("input") or {}
    return await mgr.publish(assistant_id, payload)


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
