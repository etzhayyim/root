"""Shared LangServer + Kotoba/Datomic plumbing for maps3d workers."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, Awaitable, Callable

from fastapi import FastAPI, HTTPException
import uvicorn


def _log() -> logging.Logger:
    log = logging.getLogger("maps3d")
    if not log.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        log.addHandler(h)
        log.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    return log


log = _log()


class LangServerWorker:
    def __init__(self, *, name: str) -> None:
        self.name = name
        self.handlers: dict[str, Callable[..., Awaitable[Any]]] = {}

    def task(self, *, task_type: str, **_: Any) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            self.handlers[task_type] = fn
            return fn

        return decorator


def make_worker(name: str) -> LangServerWorker:
    """Build a pod-side LangServer worker registry."""
    log.info("starting LangServer worker %s", name)
    return LangServerWorker(name=name)


def task(worker: LangServerWorker, type_: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator wrapper that logs entry/exit + duration around handlers.

    Usage:

        worker = make_worker("mapillary-fetcher")

        @task(worker, "maps3d.fetchMapillary")
        async def fetch(tileH3: str, **kwargs):
            ...
    """
    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapped(*args, **kwargs):  # type: ignore[no-untyped-def]
            import time

            t0 = time.perf_counter()
            log.info("task %s start args=%s", type_, _safe_kwargs(kwargs))
            try:
                result = await fn(*args, **kwargs)
                dur = (time.perf_counter() - t0) * 1000.0
                log.info("task %s ok %.0fms", type_, dur)
                return result
            except Exception as exc:  # noqa: BLE001
                log.exception("task %s FAILED: %s", type_, exc)
                raise

        worker.task(task_type=type_)(wrapped)
        return wrapped

    return decorator


def _safe_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Trim verbose lists/strings so log lines stay readable."""
    out: dict[str, Any] = {}
    for k, v in kwargs.items():
        if isinstance(v, list):
            out[k] = f"<list len={len(v)}>"
        elif isinstance(v, str) and len(v) > 200:
            out[k] = v[:200] + "…"
        else:
            out[k] = v
    return out


def rw_dsn() -> str:
    dsn = os.environ.get("KOTOBA_URL")
    if not dsn:
        raise RuntimeError("KOTOBA_URL env not set")
    return dsn


async def _health_handler(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Plain HTTP/1.1 200 on any request. The very fact that the
    asyncio event loop is alive enough to accept the connection and
    write a response is a strong liveness signal — a deadlocked or
    crashed worker would either close the listener (process exit) or
    fail to respond within timeoutSeconds, and k8s would restart it."""
    try:
        await reader.read(1024)  # consume request line + headers
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: 2\r\n"
            b"\r\n"
            b"ok"
        )
        await writer.drain()
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        try:
            writer.close()
        except Exception:  # noqa: BLE001
            pass


async def _start_health_server(port: int) -> asyncio.AbstractServer:
    """Bind a tiny TCP listener for k8s liveness/readiness probes.
    Lives for the rest of the event loop; never explicitly stopped."""
    server = await asyncio.start_server(_health_handler, "0.0.0.0", port)
    log.info("health probe listening on :%d", port)
    return server


async def run_forever(worker: LangServerWorker) -> None:
    """Run the LangServer HTTP worker until SIGTERM."""
    port = int(os.environ.get("PORT", os.environ.get("HEALTH_PORT", "8080")))
    agentgateway_mcp_url = os.environ.get(
        "AGENTGATEWAY_MCP_URL",
        "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
    )
    app = FastAPI(title=worker.name, version="1.0.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "ok": True,
            "runtimeKind": "k8s-langserver",
            "agentGatewayMcpUrl": agentgateway_mcp_url,
            "tools": sorted(worker.handlers),
        }

    @app.get("/tools")
    async def tools() -> dict[str, Any]:
        return {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(worker.handlers)]}

    async def invoke_tool(name: str, arguments: dict[str, Any]) -> Any:
        handler = worker.handlers.get(name)
        if handler is None:
            raise HTTPException(status_code=404, detail=f"unknown tool: {name}")
        return await handler(**arguments)

    @app.post("/invoke")
    async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name") or payload.get("tool") or "")
        arguments = payload.get("arguments") or payload.get("input") or {}
        if not isinstance(arguments, dict):
            raise HTTPException(status_code=400, detail="arguments must be an object")
        return {"ok": True, "name": name, "result": await invoke_tool(name, arguments)}

    @app.post("/runs")
    async def runs(payload: dict[str, Any]) -> dict[str, Any]:
        assistant_id = str(payload.get("assistant_id") or "")
        arguments = payload.get("input") or payload.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise HTTPException(status_code=400, detail="input must be an object")
        return {"status": "completed", "assistant_id": assistant_id, "output": await invoke_tool(assistant_id, arguments)}

    log.info("worker %s ready on :%d", worker.name, port)
    await uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")).serve()
