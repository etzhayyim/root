"""LangGraph OSS FastAPI server — public-domain-colorization (lg-pd-color).

Ten graphs:
  - health                      : liveness ping
  - videoSegmentShots           : task_pd_color_video_segment_shots
  - videoRestoreFrames          : task_pd_color_video_restore_frames
  - videoColorizeFrames         : task_pd_color_video_colorize_frames
  - videoEnhanceQuality         : task_pd_color_video_enhance_quality
  - videoEncodePackage          : task_pd_color_video_encode_package
  - videoMuxLocalizedPackages   : task_pd_color_video_mux_localized_packages
  - audioExtractTimedText       : task_pd_color_audio_extract_timed_text
  - audioGenerateDubbedAudio    : task_pd_color_audio_generate_dubbed_audio
  - localizationTranslateSubtitles: task_pd_color_localization_translate_subtitles

All handlers use camelCase parameter names; XRPC inputs are passed as-is.
No postgres checkpointer — stateless request-response graphs only.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from kotodama.zeebe_worker_main import (
    task_pd_color_audio_extract_timed_text,
    task_pd_color_audio_generate_dubbed_audio,
    task_pd_color_localization_translate_subtitles,
    task_pd_color_video_colorize_frames,
    task_pd_color_video_encode_package,
    task_pd_color_video_enhance_quality,
    task_pd_color_video_mux_localized_packages,
    task_pd_color_video_restore_frames,
    task_pd_color_video_segment_shots,
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
        return {"result": {"status": "ok", "service": "lg-pd-color"}}

    g = StateGraph(_State)
    g.add_node("ping", _node)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g.compile(name="health")


# ---------------------------------------------------------------------------
# GRAPHS dict
# ---------------------------------------------------------------------------

GRAPHS: dict[str, Any] = {
    "health": _make_health_graph(),
    "videoSegmentShots": _make_single_node_graph(
        task_pd_color_video_segment_shots, "videoSegmentShots"
    ),
    "videoRestoreFrames": _make_single_node_graph(
        task_pd_color_video_restore_frames, "videoRestoreFrames"
    ),
    "videoColorizeFrames": _make_single_node_graph(
        task_pd_color_video_colorize_frames, "videoColorizeFrames"
    ),
    "videoEnhanceQuality": _make_single_node_graph(
        task_pd_color_video_enhance_quality, "videoEnhanceQuality"
    ),
    "videoEncodePackage": _make_single_node_graph(
        task_pd_color_video_encode_package, "videoEncodePackage"
    ),
    "videoMuxLocalizedPackages": _make_single_node_graph(
        task_pd_color_video_mux_localized_packages, "videoMuxLocalizedPackages"
    ),
    "audioExtractTimedText": _make_single_node_graph(
        task_pd_color_audio_extract_timed_text, "audioExtractTimedText"
    ),
    "audioGenerateDubbedAudio": _make_single_node_graph(
        task_pd_color_audio_generate_dubbed_audio, "audioGenerateDubbedAudio"
    ),
    "localizationTranslateSubtitles": _make_single_node_graph(
        task_pd_color_localization_translate_subtitles, "localizationTranslateSubtitles"
    ),
}

_NSID_TO_ASSISTANT: dict[str, str] = {
    "com.etzhayyim.apps.pdColor.health": "health",
    "com.etzhayyim.apps.pdColor.videoSegmentShots": "videoSegmentShots",
    "com.etzhayyim.apps.pdColor.videoRestoreFrames": "videoRestoreFrames",
    "com.etzhayyim.apps.pdColor.videoColorizeFrames": "videoColorizeFrames",
    "com.etzhayyim.apps.pdColor.videoEnhanceQuality": "videoEnhanceQuality",
    "com.etzhayyim.apps.pdColor.videoEncodePackage": "videoEncodePackage",
    "com.etzhayyim.apps.pdColor.videoMuxLocalizedPackages": "videoMuxLocalizedPackages",
    "com.etzhayyim.apps.pdColor.audioExtractTimedText": "audioExtractTimedText",
    "com.etzhayyim.apps.pdColor.audioGenerateDubbedAudio": "audioGenerateDubbedAudio",
    "com.etzhayyim.apps.pdColor.localizationTranslateSubtitles": "localizationTranslateSubtitles",
}


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
    log.info("lg-pd-color startup — %d graphs loaded", len(GRAPHS))
    yield
    log.info("lg-pd-color shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="lg-pd-color", lifespan=_lifespan)


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

    # camelCase params match handler signatures directly
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
