"""FastAPI server for lg-drive.

Surfaces the canonical drive XRPC methods the atproto actor-worker pipethrough
forwards to (``drive.etzhayyim.com/xrpc/... → lg-drive:8000/xrpc/...``):

  GET  /health /ok
  POST /xrpc/ai.etzhayyim.apps.drive.filesCreate
  GET  /xrpc/ai.etzhayyim.apps.drive.filesGet
  GET  /xrpc/ai.etzhayyim.apps.drive.filesList
  POST /xrpc/ai.etzhayyim.apps.drive.filesUpdate
  POST /xrpc/ai.etzhayyim.apps.drive.filesDelete
  GET  /xrpc/ai.etzhayyim.apps.drive.about
  GET  /xrpc/ai.etzhayyim.apps.drive.changes

Persistence = kotoba datomic (graph ``drive-v1``).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from . import handlers
from .kotoba_datomic import KotobaDatomic
from .store import KotobaDriveStore

app = FastAPI(
    title="lg-drive",
    description="Google Drive v3 + Microsoft Graph (OneDrive) compatible drive API over kotoba datomic (ADR-2606010500).",
    version="0.1.0",
)

_client: httpx.AsyncClient | None = None


def _store() -> KotobaDriveStore:
    assert _client is not None, "httpx client not initialized"
    return KotobaDriveStore(KotobaDatomic(_client))


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _client is not None:
        await _client.aclose()


def _enforce_auth(x_api_key: str | None) -> None:
    expected = os.environ.get("LG_DRIVE_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {"ok": True, "app": "lg-drive", "ts": int(time.time() * 1000)}


@app.post("/xrpc/ai.etzhayyim.apps.drive.filesCreate")
async def _files_create(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.files_create(_store(), body)


@app.post("/xrpc/ai.etzhayyim.apps.drive.filesUpdate")
async def _files_update(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.files_update(_store(), body)


@app.post("/xrpc/ai.etzhayyim.apps.drive.filesDelete")
async def _files_delete(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.files_delete(_store(), body)


@app.get("/xrpc/ai.etzhayyim.apps.drive.filesGet")
async def _files_get(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.files_get(_store(), dict(request.query_params))


@app.get("/xrpc/ai.etzhayyim.apps.drive.filesList")
async def _files_list(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.files_list(_store(), dict(request.query_params))


@app.get("/xrpc/ai.etzhayyim.apps.drive.about")
async def _about(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.about(_store(), dict(request.query_params))


@app.get("/xrpc/ai.etzhayyim.apps.drive.changes")
async def _changes(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.changes(_store(), dict(request.query_params))
