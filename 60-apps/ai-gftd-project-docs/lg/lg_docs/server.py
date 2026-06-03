"""FastAPI server for lg-docs.

  GET  /health /ok
  GET  /xrpc/ai.gftd.apps.docs.documentsGet
  POST /xrpc/ai.gftd.apps.docs.documentsCreate
  POST /xrpc/ai.gftd.apps.docs.documentsBatchUpdate

Persistence = kotoba datomic (graph ``docs-v1``).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from . import handlers
from .kotoba_datomic import KotobaDatomic
from .store import KotobaDocStore

app = FastAPI(
    title="lg-docs",
    description="Google Docs v1 + Microsoft Graph (Word) compatible document API over kotoba datomic (ADR-2606010500).",
    version="0.1.0",
)

_client: httpx.AsyncClient | None = None


def _store() -> KotobaDocStore:
    assert _client is not None, "httpx client not initialized"
    return KotobaDocStore(KotobaDatomic(_client))


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _client is not None:
        await _client.aclose()


def _enforce_auth(x_api_key: str | None) -> None:
    expected = os.environ.get("LG_DOCS_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {"ok": True, "app": "lg-docs", "ts": int(time.time() * 1000)}


@app.post("/xrpc/ai.gftd.apps.docs.documentsCreate")
async def _create(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.documents_create(_store(), body)


@app.post("/xrpc/ai.gftd.apps.docs.documentsBatchUpdate")
async def _batch(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.documents_batch_update(_store(), body)


@app.get("/xrpc/ai.gftd.apps.docs.documentsGet")
async def _get(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.documents_get(_store(), dict(request.query_params))
