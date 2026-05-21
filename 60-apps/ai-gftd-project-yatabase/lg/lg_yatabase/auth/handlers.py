"""FastAPI router for the yatabase auth XRPC surface.

Mounted by lg_yatabase.server alongside the BMC router. All endpoints
expect the yatabase CF Worker forwarder to provide:

    x-internal-trust  = HMAC-SHA256(body, DISPATCHER_INTERNAL_SECRET)
    x-gftd-actor-did  = caller DID (anon for signup)
    x-gftd-org-did    = caller org DID (anon for signup; required for invite/revoke)
    x-gftd-trace-id   = cf-ray (optional)

NSIDs:
    ai.gftd.apps.yata.signup    (anonymous mint)
    ai.gftd.apps.yata.invite    (member key under caller org)
    ai.gftd.apps.yata.revoke    (revoke a key the caller owns)

Closes the ADR-2605111200 cutover gap on the auth surface so the CF
Worker can stop calling createKyselyDb in src/auth-signup.ts.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.auth import repository
from lg_yatabase.auth.models import (
    InviteInput,
    RevokeInput,
    SignupInput,
)
from pydantic import BaseModel as _BaseModel


class _ResolveApiKeyInput(_BaseModel):
    key_hash: str

_log = logging.getLogger(__name__)

router = APIRouter()


async def _verify_trust(request: Request, x_internal_trust: str | None) -> bytes:
    body = await request.body()
    secret = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if not secret:
        return body  # tunnel-trust dev mode
    if not x_internal_trust:
        raise HTTPException(status_code=401, detail="missing x-internal-trust")
    # Accept either raw shared-secret (Worker's dispatchYataXrpc) OR
    # HMAC-SHA256(body, secret) (bmc-forward.ts pattern). Same auth model
    # as the dispatcher's auth_middleware so traffic works whether the
    # pod is reached directly or via the dispatcher's proxy.
    if hmac.compare_digest(x_internal_trust, secret):
        return body
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if hmac.compare_digest(mac, x_internal_trust):
        return body
    raise HTTPException(status_code=401, detail="x-internal-trust mismatch")


@router.post("/xrpc/ai.gftd.apps.yata.signup")
async def yata_signup(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    # SignupInput parses email + name; both optional.
    import json as _json
    try:
        body = SignupInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad signup body: {e}")

    try:
        result = await repository.signup_anonymous(
            email=body.email or None,
            display_name=body.name or None,
        )
    except Exception as e:  # noqa: BLE001
        _log.exception("[yata-signup] insert failed")
        raise HTTPException(status_code=500, detail=f"PersistFailed: {e}")

    welcome_msg = (
        f"Welcome to Yatabase. Save your API key — we only store the SHA-256 hash. "
        f"Free tier: $0/month, 1,000 api_request/day."
    )
    if body.email:
        welcome_msg = (
            f"Welcome email queued to {body.email}. Save your API key — we only "
            f"store the SHA-256 hash. Free tier: $0/month, 1,000 api_request/day."
        )

    return JSONResponse({
        "ok": True,
        "apiKey": result["apiKey"],
        "keyId": result["keyId"],
        "orgDid": result["orgDid"],
        "tenantName": result["tenantName"],
        "awsAccessKeyId": result["awsAccessKeyId"],
        # awsSecretAccessKey intentionally returned ONCE — same as Worker shape
        "awsSecretAccessKey": result.get("awsSecretAccessKey", ""),
        "emailStatus": "queued-no-recipient" if not body.email else "pending",
        "welcome": welcome_msg,
        "next": "First Cypher call auto-provisions your tenant schema.",
        "pricing": "Free tier: $0/month. See /docs → Pricing for upgrade options.",
    })


@router.post("/xrpc/ai.gftd.apps.yata.invite")
async def yata_invite(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    if not x_gftd_org_did or x_gftd_org_did == "anon":
        raise HTTPException(status_code=401, detail="invite requires authenticated org")
    try:
        body = InviteInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad invite body: {e}")
    try:
        result = await repository.invite_member(
            inviter_org_did=x_gftd_org_did,
            member_name=body.name,
        )
    except Exception as e:  # noqa: BLE001
        _log.exception("[yata-invite] failed")
        raise HTTPException(status_code=500, detail=f"PersistFailed: {e}")
    return JSONResponse({
        "ok": True,
        "apiKey": result["apiKey"],
        "keyId": result["keyId"],
        "orgDid": result["orgDid"],
        "memberName": result["memberName"],
    })


@router.post("/xrpc/ai.gftd.apps.yata.authResolveApiKey")
async def yata_auth_resolve_api_key(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    """Resolve SHA-256(api_key) → {ownerDid, scopes, productScope}.

    Called by the PDS / yatabase Worker auth middleware in place of the
    legacy `createKyselyDb().selectFrom('vertex_api_key')...` lookup that
    ADR-2605111200 broke for CF Workers.
    """
    body_bytes = await _verify_trust(request, x_internal_trust)
    try:
        body = _ResolveApiKeyInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad resolve body: {e}")
    try:
        out = await repository.resolve_api_key_by_hash(key_hash=body.key_hash)
    except Exception as e:  # noqa: BLE001
        _log.exception("[yata-auth-resolve] lookup failed")
        raise HTTPException(status_code=500, detail=f"PersistFailed: {e}")
    if out is None:
        return JSONResponse({"ok": False, "found": False}, status_code=200)
    return JSONResponse({"ok": True, "found": True, **out})


@router.post("/xrpc/ai.gftd.apps.yata.revoke")
async def yata_revoke(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
) -> JSONResponse:
    body_bytes = await _verify_trust(request, x_internal_trust)
    if not x_gftd_org_did or x_gftd_org_did == "anon":
        raise HTTPException(status_code=401, detail="revoke requires authenticated org")
    try:
        body = RevokeInput.model_validate_json(body_bytes or b"{}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad revoke body: {e}")
    try:
        result = await repository.revoke_key(
            vertex_id=body.vertex_id,
            org_did=x_gftd_org_did,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    except Exception as e:  # noqa: BLE001
        _log.exception("[yata-revoke] failed")
        raise HTTPException(status_code=500, detail=f"PersistFailed: {e}")
    return JSONResponse({"ok": True, **result})
