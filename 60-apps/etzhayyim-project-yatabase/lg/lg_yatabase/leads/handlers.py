"""FastAPI router for the yatabase lead-CRM XRPC surface.

Mirrors lg_yatabase/auth/handlers.py: x-internal-trust HMAC verify,
identity headers from the Worker forwarder. All writes are scoped to
vertex_lead which is global operator-state, so no per-org gating yet
(adminKey on the Worker side is the access control).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.leads import repository
from lg_yatabase.leads.models import (
    LeadIngestInput,
    MarkDraftedInput,
    SetContactEmailInput,
    SetEnrichmentInput,
    SetOutreachStatusInput,
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
    # Accept either raw shared-secret (yatabase Worker's dispatchYataXrpc
    # sends this) OR HMAC-SHA256(body, secret) (P59 bmc-forward.ts /
    # leads-forward.ts pattern). Matches the dispatcher's auth_middleware
    # so the same Worker traffic works whether it lands on bpmn-dispatcher
    # directly or gets proxied here by _proxy_to_lg_yatabase.
    if hmac.compare_digest(x_internal_trust, secret):
        return body
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(mac, x_internal_trust):
        return body
    raise HTTPException(status_code=401, detail="x-internal-trust mismatch")


@router.post("/xrpc/com.etzhayyim.apps.yata.leadIngest")
async def lead_ingest(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = LeadIngestInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad ingest body: {e}")
    try:
        result = await repository.ingest_lead(body.model_dump())
    except Exception as e:  # noqa: BLE001
        _log.exception("[lead-ingest] failed")
        raise HTTPException(status_code=500, detail=f"PersistFailed: {e}")
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)


async def _read_query_params(request: Request, body_bytes: bytes) -> dict:
    """Merge URL query params + JSON body (for callers that POST). The
    yatabase Worker forwards every XRPC call as POST with a JSON body via
    dispatchYataXrpc, so query-method handlers need to look at both."""
    params: dict = dict(request.query_params)
    if body_bytes:
        import json as _json
        try:
            data = _json.loads(body_bytes)
            if isinstance(data, dict):
                for k, v in data.items():
                    if k not in params:
                        params[k] = v
        except Exception:  # noqa: BLE001
            pass
    return params


@router.api_route("/xrpc/com.etzhayyim.apps.yata.leadList", methods=["GET", "POST"])
async def lead_list(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    params = await _read_query_params(request, body_bytes)
    status = params.get("status") or None
    domain = params.get("domain") or None
    limit_raw = params.get("limit")
    try:
        limit = int(limit_raw) if limit_raw is not None else 50
    except (TypeError, ValueError):
        limit = 50
    out = await repository.list_leads(status=status, domain=domain, limit=limit)
    return JSONResponse(out)


@router.api_route("/xrpc/com.etzhayyim.apps.yata.leadGet", methods=["GET", "POST"])
async def lead_get(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    params = await _read_query_params(request, body_bytes)
    vertex_id = params.get("vertex_id")
    if not vertex_id:
        raise HTTPException(status_code=400, detail="vertex_id required")
    row = await repository.get_lead_by_vertex_id(str(vertex_id))
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return JSONResponse(row)


@router.post("/xrpc/com.etzhayyim.apps.yata.leadSetOutreachStatus")
async def lead_set_status(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = SetOutreachStatusInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad body: {e}")
    out = await repository.set_outreach_status(vertex_id=body.vertex_id, status=body.status)
    return JSONResponse(out)


@router.post("/xrpc/com.etzhayyim.apps.yata.leadSetContactEmail")
async def lead_set_email(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = SetContactEmailInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad body: {e}")
    out = await repository.set_contact_email(vertex_id=body.vertex_id, email=body.email)
    return JSONResponse(out, status_code=200 if out.get("ok") else 400)


@router.post("/xrpc/com.etzhayyim.apps.yata.leadSetEnrichment")
async def lead_set_enrichment(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = SetEnrichmentInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad body: {e}")
    out = await repository.set_enrichment(
        vertex_id=body.vertex_id,
        contact_email=body.contact_email,
        tech_stack=body.tech_stack,
    )
    return JSONResponse(out)


@router.post("/xrpc/com.etzhayyim.apps.yata.leadMarkDrafted")
async def lead_mark_drafted(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = MarkDraftedInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad body: {e}")
    out = await repository.mark_drafted(vertex_id=body.vertex_id, outbox_id=body.outbox_id)
    return JSONResponse(out)


@router.api_route("/xrpc/com.etzhayyim.apps.yata.leadReady", methods=["GET", "POST"])
async def lead_ready(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    params = await _read_query_params(request, body_bytes)
    try:
        limit = int(params.get("limit", 10))
    except (TypeError, ValueError):
        limit = 10
    out = await repository.leads_ready_for_outreach(limit=limit)
    return JSONResponse(out)


@router.api_route("/xrpc/com.etzhayyim.apps.yata.leadSendable", methods=["GET", "POST"])
async def lead_sendable(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    params = await _read_query_params(request, body_bytes)
    try:
        limit = int(params.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50
    out = await repository.leads_sendable(limit=limit)
    return JSONResponse(out)


@router.api_route("/xrpc/com.etzhayyim.apps.yata.leadNeedsEnrichment", methods=["GET", "POST"])
async def lead_needs_enrichment(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    params = await _read_query_params(request, body_bytes)
    try:
        limit = int(params.get("limit", 10))
    except (TypeError, ValueError):
        limit = 10
    out = await repository.leads_needing_enrichment(limit=limit)
    return JSONResponse(out)
