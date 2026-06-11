"""lg-recap OSS FastAPI server (mirrors lg-animeka pattern).

HTTP surface:
  POST /runs              → invoke graph synchronously
  POST /xrpc/{nsid}       → XRPC shim (NSID → graph mapping)
  GET  /ok / /health      → liveness / readiness

NSID namespace: com.etzhayyim.apps.recap.*
Auth: optional LG_API_KEY env enforces x-api-key on /runs.
      /xrpc/{nsid} is unauthenticated (trust at cloudflared tunnel layer).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from lg_recap.graphs.download import GRAPH as DOWNLOAD
from lg_recap.graphs.get_info import GRAPH as GET_INFO
from lg_recap.graphs.health import GRAPH as HEALTH
from lg_recap.graphs.list_downloads import GRAPH as LIST_DOWNLOADS
from lg_recap.graphs.summarize import GRAPH as SUMMARIZE

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health":         HEALTH,
    "download":       DOWNLOAD,
    "get_info":       GET_INFO,
    "list_downloads": LIST_DOWNLOADS,
    "summarize":      SUMMARIZE,
}

# NSID → graph name mapping
NSID_MAP: dict[str, str] = {
    "com.etzhayyim.apps.recap.download":       "download",
    "com.etzhayyim.apps.recap.getInfo":         "get_info",
    "com.etzhayyim.apps.recap.listDownloads":   "list_downloads",
    "com.etzhayyim.apps.recap.summarize":       "summarize",
}

_API_KEY = os.environ.get("LG_API_KEY", "")


def _check_api_key(x_api_key: str = Header(default="")) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


app = FastAPI(title="lg-recap", version="0.1.0")


@app.get("/ok")
@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "graphs": list(GRAPHS)}


@app.post("/runs", dependencies=[Depends(_check_api_key)])
async def runs(body: dict[str, Any]) -> JSONResponse:
    assistant_id = body.get("assistant_id", "")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        return JSONResponse({"error": f"unknown graph: {assistant_id}"}, status_code=404)
    input_data = body.get("input") or body.get("inputs") or {}
    try:
        result = await graph.ainvoke(input_data)
    except Exception as exc:
        _log.exception("graph %s failed", assistant_id)
        return JSONResponse({"error": str(exc)[:300]}, status_code=500)
    return JSONResponse(_serialize(result))


@app.post("/xrpc/{nsid}")
async def xrpc(nsid: str, body: dict[str, Any]) -> JSONResponse:
    graph_name = NSID_MAP.get(nsid)
    if graph_name is None:
        return JSONResponse({"error": f"unknown nsid: {nsid}"}, status_code=404)
    graph = GRAPHS[graph_name]
    try:
        result = await graph.ainvoke(body)
    except Exception as exc:
        _log.exception("xrpc %s failed", nsid)
        return JSONResponse({"error": str(exc)[:300]}, status_code=500)
    return JSONResponse(_serialize(result))


def _serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    return obj
