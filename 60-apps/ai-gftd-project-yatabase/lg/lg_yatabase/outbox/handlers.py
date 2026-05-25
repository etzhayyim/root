"""FastAPI router for the yatabase outbox-review XRPC surface.

Mirrors lg_yatabase/leads/handlers.py: x-internal-trust HMAC verify
(or raw shared-secret fallback). The yatabase Worker gates this on
the operator side with x-yata-admin-key BEFORE forwarding — the pod
sees only trusted traffic.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.outbox import repository
from lg_yatabase.outbox.models import (
    OutboxApproveInput,
    OutboxListInput,
    OutboxRejectInput,
)

_log = logging.getLogger(__name__)
router = APIRouter()


async def _verify_trust(request: Request, x_internal_trust: str | None) -> bytes:
    body = await request.body()
    secret = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if not secret:
        return body
    if not x_internal_trust:
        raise HTTPException(status_code=401, detail="missing x-internal-trust")
    if hmac.compare_digest(x_internal_trust, secret):
        return body
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(mac, x_internal_trust):
        return body
    raise HTTPException(status_code=401, detail="x-internal-trust mismatch")


@router.post("/xrpc/app.etzhayyim.apps.yata.outboxList")
async def outbox_list(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        payload = OutboxListInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:                                       # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad input: {e}") from e
    result = await repository.list_outbox(
        status=payload.status, kind=payload.kind, limit=payload.limit,
    )
    return JSONResponse(content=result)


@router.post("/xrpc/app.etzhayyim.apps.yata.outboxApprove")
async def outbox_approve(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        payload = OutboxApproveInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:                                       # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad input: {e}") from e
    result = await repository.approve_outbox(payload.model_dump(exclude_none=True))
    return JSONResponse(content=result)


@router.post("/xrpc/app.etzhayyim.apps.yata.outboxReject")
async def outbox_reject(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        payload = OutboxRejectInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:                                       # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad input: {e}") from e
    result = await repository.reject_outbox(payload.model_dump(exclude_none=True))
    return JSONResponse(content=result)
