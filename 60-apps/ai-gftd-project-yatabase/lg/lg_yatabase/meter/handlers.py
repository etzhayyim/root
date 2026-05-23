"""FastAPI router exposing the meterEvent XRPC endpoint.

NSID: ai.gftd.apps.yata.meterEvent

Called fire-and-forget from the yatabase CF Worker's executionCtx.waitUntil()
when emitMeter() fires. The Worker can no longer write to RisingWave directly
(ADR-2605111200), so this pod-side handler owns vertex_billing_event writes
and keeps vertex_api_key growth columns in sync.

Auth: x-internal-trust shared-secret (same as leads/auth handlers).

TODO(substrate-boundary): replace RW billing event writes (execute INSERT into
vertex_billing_event) with AT Protocol MST writes per ADR-2605172000. Billing events
collection: 'ai.gftd.apps.yata.billing.events', rkey=timestamp_event_id. Immutable
event log ensures audit trail integrity.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import uuid
from datetime import datetime, timezone
import time

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.bmc.db import execute

_log = logging.getLogger(__name__)
router = APIRouter()

_VALID_METRICS = {"api_request", "mcp_call", "node_write", "node_read"}


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


@router.post("/xrpc/ai.gftd.apps.yata.meterEvent")
async def meter_event(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)

    body: dict = await request.json()
    org_did: str = body.get("orgDid") or x_gftd_org_did or ""
    metric: str = body.get("metric", "")
    qty: int = int(body.get("qty", 1))
    ref_resource: str = body.get("refResource", "")

    if not org_did:
        raise HTTPException(status_code=400, detail="orgDid required")
    if metric not in _VALID_METRICS:
        raise HTTPException(status_code=400, detail=f"unknown metric: {metric}")
    if qty < 1:
        qty = 1

    now = datetime.now(timezone.utc)
    vid = str(uuid.uuid4())
    ts_ms = int(time.time() * 1000)

    try:
        await execute(
            """
            INSERT INTO vertex_billing_event
              (vertex_id, org_did, metric, qty, ref_resource, ts_ms, created_at, created_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            vid,
            org_did,
            metric,
            float(qty),
            ref_resource,
            ts_ms,
            now,
            now.date(),
        )
    except Exception as e:
        _log.warning("[meter] billing_event insert failed org=%s metric=%s: %s", org_did[:32], metric, e)
        raise HTTPException(status_code=500, detail=str(e)[:200])

    # Update vertex_api_key growth columns (best-effort; don't fail the request)
    try:
        if metric == "api_request":
            await execute(
                """
                UPDATE vertex_api_key
                SET query_count    = COALESCE(query_count, 0) + $2,
                    last_query_at  = $3
                WHERE owner_did = $1
                """,
                org_did, qty, now,
            )
        elif metric == "mcp_call":
            await execute(
                """
                UPDATE vertex_api_key
                SET mcp_calls_month = COALESCE(mcp_calls_month, 0) + $2,
                    last_query_at   = $3
                WHERE owner_did = $1
                """,
                org_did, qty, now,
            )
        elif metric == "node_write":
            await execute(
                """
                UPDATE vertex_api_key
                SET node_count    = COALESCE(node_count, 0) + $2,
                    last_query_at = $3
                WHERE owner_did = $1
                """,
                org_did, qty, now,
            )
    except Exception as e:
        _log.warning("[meter] api_key update failed org=%s: %s", org_did[:32], e)

    _log.info("[meter] org=%s metric=%s qty=%d", org_did[:32], metric, qty)
    return JSONResponse({"ok": True, "vertex_id": vid})
