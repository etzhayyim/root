"""FastAPI server for lg-sheets.

  GET  /health /ok
  GET  /xrpc/ai.gftd.apps.sheets.spreadsheetsGet
  POST /xrpc/ai.gftd.apps.sheets.spreadsheetsCreate
  GET  /xrpc/ai.gftd.apps.sheets.valuesGet
  POST /xrpc/ai.gftd.apps.sheets.valuesUpdate
  POST /xrpc/ai.gftd.apps.sheets.valuesBatchUpdate

Persistence = kotoba datomic (graph ``sheets-v1``).
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from . import handlers
from .kotoba_datomic import KotobaDatomic
from .store import KotobaSheetStore

app = FastAPI(
    title="lg-sheets",
    description="Google Sheets v4 + Microsoft Graph (workbook) compatible spreadsheet API over kotoba datomic (ADR-2606010500).",
    version="0.1.0",
)

_client: httpx.AsyncClient | None = None


def _store() -> KotobaSheetStore:
    assert _client is not None, "httpx client not initialized"
    return KotobaSheetStore(KotobaDatomic(_client))


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _client is not None:
        await _client.aclose()


def _enforce_auth(x_api_key: str | None) -> None:
    expected = os.environ.get("LG_SHEETS_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {"ok": True, "app": "lg-sheets", "ts": int(time.time() * 1000)}


@app.post("/xrpc/ai.gftd.apps.sheets.spreadsheetsCreate")
async def _create(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.spreadsheets_create(_store(), body)


@app.post("/xrpc/ai.gftd.apps.sheets.valuesUpdate")
async def _values_update(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.values_update(_store(), body)


@app.post("/xrpc/ai.gftd.apps.sheets.valuesBatchUpdate")
async def _values_batch(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.values_batch_update(_store(), body)


@app.get("/xrpc/ai.gftd.apps.sheets.spreadsheetsGet")
async def _get(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.spreadsheets_get(_store(), dict(request.query_params))


@app.get("/xrpc/ai.gftd.apps.sheets.valuesGet")
async def _values_get(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.values_get(_store(), dict(request.query_params))
