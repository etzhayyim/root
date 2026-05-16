"""HTTP / JSON-RPC transport for keiei LSP (Phase 4, ADR 2605101200).

The existing stdio + Unix-socket transports remain the default for
local dev. This module adds a multi-client HTTP front-end so the same
``KeieiServer.handle()`` dispatcher can run inside a k8s Deployment
behind a Service + Ingress.

Endpoints
---------

  ``GET  /health``                  → liveness + leader identity + lease status
  ``GET  /ok``                      → liveness (alias for k8s probes)
  ``GET  /cxo/listRoles``           → cached role registry (no auth)
  ``POST /jsonrpc``                 → JSON-RPC envelope passed to KeieiServer
                                       (bearer auth enforced when KEIEI_HTTP_BEARER
                                       env is set)
  ``GET  /leader``                  → who currently holds the writer lease

Auth
----

When ``KEIEI_HTTP_BEARER`` is set, ``Authorization: Bearer <token>`` is
required on all ``/jsonrpc`` calls. A missing or mismatched token →
401. mTLS is enforced one layer up at the Ingress (see RUNBOOK).

Production run::

    granian --interface asgi pymagatama.keiei.http_server:app \
        --host 0.0.0.0 --port 8000

Per ADR-2605080600 LangGraph-server pattern, but adapted: keiei is a
JSON-RPC LSP, not a LangGraph chain, so FastAPI + a thin pass-through
dispatcher is sufficient.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

try:
    from fastapi import FastAPI, Header, HTTPException, Request
    from fastapi.responses import JSONResponse
except ModuleNotFoundError as e:                            # pragma: no cover
    raise ModuleNotFoundError(
        "fastapi is required for keiei HTTP transport — install via pip"
    ) from e

from .leader import get_leader
from .lsp_server import KeieiServer, LEDGER_PATH


_BEARER_ENV = "KEIEI_HTTP_BEARER"


def _check_bearer(authorization: str | None) -> None:
    expected = os.environ.get(_BEARER_ENV, "")
    if not expected:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="invalid bearer")


def create_app() -> FastAPI:
    app = FastAPI(
        title="keiei-lsp",
        version="0.2.0",
        description=(
            "C-suite role LSP, HTTP transport (Phase 4). "
            "JSON-RPC envelope routed to the same dispatcher used by "
            "stdio + Unix socket. Leader-gated writes; followers "
            "respond with status=not-leader and the leader identity."
        ),
    )

    # One KeieiServer per ASGI worker (granian replicates workers).
    # The dispatcher is stateless across requests (session is per-init
    # for stdio; for HTTP we re-initialise per call).
    server = KeieiServer()
    server.session.initialized = True

    @app.get("/health")
    @app.get("/ok")
    async def health() -> dict[str, Any]:
        leader = get_leader()
        return {
            "status": "ok",
            "service": "keiei-lsp",
            "version": app.version,
            "isLeader": leader.is_leader(),
            "identity": leader.identity(),
            "ledgerPath": str(LEDGER_PATH),
        }

    @app.get("/leader")
    async def leader_info() -> dict[str, Any]:
        leader = get_leader()
        return {
            "isLeader": leader.is_leader(),
            "identity": leader.identity(),
        }

    @app.get("/cxo/listRoles")
    async def list_roles_get() -> Any:
        # Convenience GET for ops / curl; no auth needed (read-only).
        return server._list_roles()                          # noqa: SLF001

    @app.post("/jsonrpc")
    async def jsonrpc(
        request: Request,
        authorization: str | None = Header(default=None),
        x_acting_as: str | None = Header(default=None, alias="X-Acting-As"),
    ) -> JSONResponse:
        _check_bearer(authorization)

        try:
            msg = await request.json()
        except Exception:                                       # noqa: BLE001
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "parse error"},
                },
            )

        # Per-call actingAs injection so HTTP clients can pass it via
        # header rather than the JSON-RPC initialize handshake (which
        # is stdio-shaped).
        if x_acting_as:
            server.session.acting_as = x_acting_as

        if not isinstance(msg, dict):
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32600, "message": "request must be JSON object"},
                },
            )

        try:
            resp = await asyncio.wait_for(server.handle(msg), timeout=25.0)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={
                    "jsonrpc": "2.0", "id": msg.get("id"),
                    "error": {"code": -32000, "message": "handler timeout (25s)"},
                },
            )
        except SystemExit:
            # `exit` method — return 204 No Content rather than killing the worker.
            return JSONResponse(status_code=204, content=None)

        if resp is None:
            # JSON-RPC notification (no id) — 204 by convention.
            return JSONResponse(status_code=204, content=None)

        # If the inner result carries status=not-leader, advertise the
        # leader identity in a response header so smart clients can retry
        # directly without re-parsing JSON.
        result_obj = (resp or {}).get("result") or {}
        if isinstance(result_obj, dict) and result_obj.get("status") == "not-leader":
            headers = {
                "X-Keiei-Leader": str(result_obj.get("leaderIdentity", "")),
                "Retry-After": "5",
            }
            return JSONResponse(status_code=503, content=resp, headers=headers)

        return JSONResponse(status_code=200, content=resp)

    return app


# Module-level app for ``granian --interface asgi pymagatama.keiei.http_server:app``.
app = create_app()
