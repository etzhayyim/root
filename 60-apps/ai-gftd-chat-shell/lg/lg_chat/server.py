"""OSS FastAPI server for lg-chat (chat.gftd.ai general-purpose assistant).

Mirrors lg_shinshi/server.py pattern. Exposes a minimal LangGraph-Cloud-
compatible HTTP surface:

  POST /runs              → invoke agent_chat synchronously
  POST /runs/stream       → stream graph events as SSE (ChatPanel target)
  GET  /ok                → liveness
  GET  /health            → readiness

Sprint 1 (2026-05-23): ephemeral-only — all sessions use checkpointer=None.
History lives in browser IndexedDB (ADR-2605230000). The RW checkpointer
will be wired in Sprint 2 when Pro-tier persistent threads are needed.
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Union

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import Response, StreamingResponse

_log = logging.getLogger(__name__)

_API_KEY = os.environ.get("LG_API_KEY", "").strip()
_RW_URL = os.environ.get("RW_URL", "")


def _require_api_key(x_api_key: str | None = Header(default=None, alias="x-api-key")) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="invalid x-api-key")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from lg_chat.graphs.agent_chat import GRAPH as AGENT_CHAT
    from lg_chat.graphs.sodai_submit import GRAPH as SODAI_SUBMIT

    # Sprint 1: no checkpointer (all sessions are ephemeral).
    # Sprint 2: wire RW _RwAsyncPostgresSaver here for Pro-tier threads.
    app.state.graphs = {"agent_chat": AGENT_CHAT, "sodai_submit": SODAI_SUBMIT}
    app.state.graph = AGENT_CHAT  # backward-compat default
    _log.info("lg-chat server up — graphs loaded: %s (ephemeral-only)",
              list(app.state.graphs.keys()))
    yield


app = FastAPI(title="lg-chat OSS server", version="0.1.0", lifespan=_lifespan)

_BOOT_TS = time.time()


@app.get("/ok")
async def ok() -> dict[str, Any]:
    graphs = list(getattr(app.state, "graphs", {}).keys()) or ["agent_chat"]
    return {"ok": True, "graphs": graphs, "version": "0.1.0"}


def _resolve_graph(assistant_id: str) -> Any:
    """Look up the compiled graph for an assistant_id (empty → agent_chat)."""
    graphs = getattr(app.state, "graphs", {})
    key = assistant_id or "agent_chat"
    graph = graphs.get(key)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"unknown graph: {assistant_id}")
    return graph


@app.get("/health")
async def health() -> dict[str, Any]:
    ready = hasattr(app.state, "graph") and app.state.graph is not None
    return {"ok": ready}


@app.get("/health/deep", response_model=None)
async def health_deep() -> Union[dict[str, Any], Response]:
    from fastapi import Response

    checks: dict[str, Any] = {"graph": False, "rw_roundtrip_ms": None, "rw_ok": False}
    checks["graph"] = hasattr(app.state, "graph") and app.state.graph is not None

    started = time.monotonic()
    try:
        if _RW_URL:
            import psycopg
            conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True, connect_timeout=15)
            try:
                cur = conn.cursor()
                await cur.execute("SELECT 1")
                await cur.fetchone()
                checks["rw_ok"] = True
            finally:
                await conn.close()
        checks["rw_roundtrip_ms"] = int((time.monotonic() - started) * 1000)
    except Exception as exc:  # noqa: BLE001
        checks["rw_roundtrip_ms"] = int((time.monotonic() - started) * 1000)
        checks["warnings"] = [f"rw: {type(exc).__name__}: {str(exc)[:120]}"]

    hard_ok = bool(checks["graph"])
    body: dict[str, Any] = {"ok": hard_ok, "uptimeSec": int(time.time() - _BOOT_TS), **checks}
    if not hard_ok:
        return Response(content=json.dumps(body), media_type="application/json", status_code=503)
    return body


def _sanitize(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<bytes:{len(value)}B>"  # type: ignore[arg-type]
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


@app.post("/runs", dependencies=[Depends(_require_api_key)])
async def create_run(body: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(body.get("assistant_id") or "")
    graph = _resolve_graph(assistant_id)
    input_data = body.get("input") or {}
    config = body.get("config") or {}
    if config.get("configurable", {}).get("ephemeral"):
        graph = graph.with_config({"checkpointer": None})
    started = time.monotonic()
    try:
        result = await graph.ainvoke(input_data, config=config)
        return {"ok": True, "result": _sanitize(result),
                "latencyMs": int((time.monotonic() - started) * 1000)}
    except Exception as exc:  # noqa: BLE001
        _log.exception("agent_chat failed")
        return {"ok": False, "error": str(exc)[:500], "errorType": type(exc).__name__,
                "latencyMs": int((time.monotonic() - started) * 1000)}


@app.post("/runs/stream", dependencies=[Depends(_require_api_key)])
async def stream_run(body: dict[str, Any]) -> StreamingResponse:
    assistant_id = str(body.get("assistant_id") or "")
    graph = _resolve_graph(assistant_id)
    input_data = body.get("input") or {}
    config = body.get("config") or {}
    stream_mode = body.get("stream_mode") or "values"
    if config.get("configurable", {}).get("ephemeral"):
        graph = graph.with_config({"checkpointer": None})

    async def _gen() -> AsyncIterator[bytes]:
        try:
            async for chunk in graph.astream(input_data, config=config, stream_mode=stream_mode):
                payload = {"event": "values", "data": _sanitize(chunk)}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()
        except Exception as exc:  # noqa: BLE001
            _log.exception("stream error")
            yield f"data: {json.dumps({'event': 'error', 'data': str(exc)[:500]})}\n\n".encode()
        finally:
            yield b"data: {\"event\": \"done\"}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")
