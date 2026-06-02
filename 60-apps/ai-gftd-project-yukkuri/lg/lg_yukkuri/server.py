"""OSS FastAPI server for lg-yukkuri (mirrors lg-animeka pattern).

Provides:
  POST /runs              → invoke a graph synchronously
  POST /runs/stream       → stream graph events as SSE
  POST /xrpc/{nsid}       → XRPC-compat shim (NSID → assistant_id)
  GET  /threads/{tid}/state → fetch latest checkpoint
  GET  /ok / /health      → liveness / readiness

Auth: optional `LG_API_KEY` env enforces `x-api-key` on /runs paths.
/xrpc/{nsid} is unauthenticated (trust at the cloudflared tunnel layer).

Pipeline: compose → generate_script → [synthesize_voice + generate_visual +
generate_bgm] (parallel via CF Worker onCommit) → render_video → review_video
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

from lg_yukkuri.checkpointer import build_checkpointer
from lg_yukkuri.cron import start_cron, stop_cron
from lg_yukkuri.graphs.compose import GRAPH as COMPOSE
from lg_yukkuri.graphs.generate_bgm import GRAPH as GENERATE_BGM
from lg_yukkuri.graphs.generate_script import GRAPH as GENERATE_SCRIPT
from lg_yukkuri.graphs.generate_visual import GRAPH as GENERATE_VISUAL
from lg_yukkuri.graphs.get_video import GRAPH as GET_VIDEO
from lg_yukkuri.graphs.health import GRAPH as HEALTH
from lg_yukkuri.graphs.list_videos import GRAPH as LIST_VIDEOS
from lg_yukkuri.graphs.render_video import GRAPH as RENDER_VIDEO
from lg_yukkuri.graphs.review_video import GRAPH as REVIEW_VIDEO
from lg_yukkuri.graphs.synthesize_voice import GRAPH as SYNTHESIZE_VOICE

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":           HEALTH,
    "list_videos":      LIST_VIDEOS,
    "get_video":        GET_VIDEO,
    "compose":          COMPOSE,
    "generate_script":  GENERATE_SCRIPT,
    "synthesize_voice": SYNTHESIZE_VOICE,
    "generate_visual":  GENERATE_VISUAL,
    "generate_bgm":     GENERATE_BGM,
    "render_video":     RENDER_VIDEO,
    "review_video":     REVIEW_VIDEO,
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

    _log.info("lg-yukkuri server up: graphs=%s crons=%s", list(bound), bool(scheduler))
    try:
        yield
    finally:
        await stop_cron(scheduler)
        await cp_ctx.__aexit__(None, None, None)


app = FastAPI(title="lg-yukkuri OSS server", version="0.1.0", lifespan=_lifespan)


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


# ── XRPC-compat surface ────────────────────────────────────────────────

_NSID_TO_ASSISTANT: dict[str, str] = {
    "com.etzhayyim.apps.yukkuri.health":           "health",
    "com.etzhayyim.apps.yukkuri.listVideos":       "list_videos",
    "com.etzhayyim.apps.yukkuri.getVideo":         "get_video",
    "com.etzhayyim.apps.yukkuri.compose":          "compose",
    "com.etzhayyim.apps.yukkuri.generateScript":   "generate_script",
    "com.etzhayyim.apps.yukkuri.synthesizeVoice":  "synthesize_voice",
    "com.etzhayyim.apps.yukkuri.generateVisual":   "generate_visual",
    "com.etzhayyim.apps.yukkuri.generateBgm":      "generate_bgm",
    "com.etzhayyim.apps.yukkuri.renderVideo":      "render_video",
    "com.etzhayyim.apps.yukkuri.reviewVideo":      "review_video",
}


def _camel_to_snake(s: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(s):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


@app.post("/xrpc/{nsid}")
async def xrpc_compat(nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if not assistant_id:
        raise HTTPException(status_code=404, detail=f"unknown NSID: {nsid}")
    if assistant_id not in app.state.graphs:
        raise HTTPException(status_code=503, detail=f"graph not loaded: {assistant_id}")

    graph = app.state.graphs[assistant_id]
    graph_input = {_camel_to_snake(k): v for k, v in (body or {}).items()}
    bucket = int(time.time()) // 1800
    thread_id = f"xrpc:{nsid.split('.')[-1]}:{bucket}"
    config = {"configurable": {"thread_id": thread_id}}

    started = time.monotonic()
    try:
        result = await graph.ainvoke(graph_input, config=config)
    except Exception as exc:  # noqa: BLE001
        _log.exception("xrpc graph %s failed", assistant_id)
        return {
            "error": f"lg-yukkuri {type(exc).__name__}",
            "errorDetail": str(exc)[:300],
            "assistantId": assistant_id,
            "latencyMs": int((time.monotonic() - started) * 1000),
        }

    out = dict(result) if isinstance(result, dict) else {"result": _safe_json(result)}
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
