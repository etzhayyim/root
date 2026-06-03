"""FastAPI server for lg-calendar.

Surfaces the canonical calendar XRPC methods that the atproto actor-worker
pipethrough forwards to (``calendar.gftd.ai/xrpc/... → lg-calendar:8000/xrpc/...``):

  GET  /health /ok
  POST /xrpc/ai.gftd.apps.calendar.createEvent
  GET  /xrpc/ai.gftd.apps.calendar.getEvent
  GET  /xrpc/ai.gftd.apps.calendar.listEvents
  POST /xrpc/ai.gftd.apps.calendar.updateEvent
  POST /xrpc/ai.gftd.apps.calendar.deleteEvent
  POST /xrpc/ai.gftd.apps.calendar.rsvp
  GET  /xrpc/ai.gftd.apps.calendar.listCalendars

Persistence = kotoba datomic (graph ``calendar-v1``). One shared httpx client +
KotobaDatomic wrapper per process. Auth: optional ``LG_CALENDAR_API_KEY``; the
edge actor-worker (x-internal-trust) is the real trust boundary.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request

from . import handlers
from .kotoba_datomic import KotobaDatomic
from .store import KotobaCalendarStore

app = FastAPI(
    title="lg-calendar",
    description="Google Calendar v3 + Microsoft Graph compatible calendar API over kotoba datomic (ADR-2606010500).",
    version="0.1.0",
)

_client: httpx.AsyncClient | None = None


def _store() -> KotobaCalendarStore:
    assert _client is not None, "httpx client not initialized"
    return KotobaCalendarStore(KotobaDatomic(_client))


@app.on_event("startup")
async def _startup() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=30.0)


@app.on_event("shutdown")
async def _shutdown() -> None:
    if _client is not None:
        await _client.aclose()


def _enforce_auth(x_api_key: str | None) -> None:
    expected = os.environ.get("LG_CALENDAR_API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {"ok": True, "app": "lg-calendar", "ts": int(time.time() * 1000)}


# ── procedures (POST) ─────────────────────────────────────────────────────────


@app.post("/xrpc/ai.gftd.apps.calendar.createEvent")
async def _create_event(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.create_event(_store(), body)


@app.post("/xrpc/ai.gftd.apps.calendar.updateEvent")
async def _update_event(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.update_event(_store(), body)


@app.post("/xrpc/ai.gftd.apps.calendar.deleteEvent")
async def _delete_event(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.delete_event(_store(), body)


@app.post("/xrpc/ai.gftd.apps.calendar.rsvp")
async def _rsvp(body: dict[str, Any], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.rsvp(_store(), body)


# ── queries (GET) ─────────────────────────────────────────────────────────────


@app.get("/xrpc/ai.gftd.apps.calendar.getEvent")
async def _get_event(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.get_event(_store(), dict(request.query_params))


@app.get("/xrpc/ai.gftd.apps.calendar.listEvents")
async def _list_events(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.list_events(_store(), dict(request.query_params))


@app.get("/xrpc/ai.gftd.apps.calendar.listCalendars")
async def _list_calendars(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, Any]:
    _enforce_auth(x_api_key)
    return await handlers.list_calendars(_store(), dict(request.query_params))
