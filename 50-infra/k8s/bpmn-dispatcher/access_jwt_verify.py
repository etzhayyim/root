"""Stage-E internal-trust verifier — Cloudflare Access JWT (asymmetric), with a
dual-accept bridge to the legacy HMAC during cutover.

Design: 50-infra/k8s/bpmn-dispatcher/STAGE-E-HMAC-DISSOLUTION.md
Anchor: ADR-2605231525 (no-server-key). The end state holds **no signing secret**
in the operated pod — it verifies a Cloudflare-Access-issued RS256 JWT against
Cloudflare's PUBLIC JWKS. The apex Worker is authenticated by a CF Access
service token (trust anchor at Cloudflare, not a server-held HMAC key).

This module is import-safe and side-effect-free. It is the code the dispatcher's
strict-mode auth should call; wiring instructions are in the design doc. It is
NOT yet embedded in the live configmaps (that is the operator's gated cutover).

Dependency: PyJWT[crypto] (the dispatcher image currently imports only `hmac`;
add `pyjwt[crypto]` to requirements as part of the cutover).
"""

from __future__ import annotations

import hmac as _hmac
import time
from typing import Any, Callable, Mapping, Optional

import jwt  # PyJWT
from jwt.algorithms import RSAAlgorithm

# Cloudflare Access conventions.
ACCESS_JWT_HEADER = "cf-access-jwt-assertion"  # header is case-insensitive
ACCESS_COOKIE = "CF_Authorization"
LEGACY_HMAC_HEADER = "x-internal-trust"


def access_issuer(team_domain: str) -> str:
    """`https://<team>.cloudflareaccess.com` — the JWT `iss` Access mints."""
    return f"https://{team_domain}.cloudflareaccess.com"


def access_jwks_url(team_domain: str) -> str:
    """Public JWKS endpoint. The pod fetches+caches this; it holds no secret."""
    return f"{access_issuer(team_domain)}/cdn-cgi/access/certs"


def verify_access_jwt(
    token: str,
    *,
    team_domain: str,
    expected_aud: str,
    jwks: Mapping[str, Any],
    leeway: int = 60,
    now: Optional[int] = None,
) -> dict[str, Any]:
    """Verify a Cloudflare Access RS256 JWT against the team's PUBLIC JWKS.

    Returns the decoded claims on success; raises jwt.InvalidTokenError (or a
    subclass) on any failure (bad signature / aud / iss / exp / unknown kid).

    `jwks` is the parsed JSON from access_jwks_url() — the caller is responsible
    for fetching + caching it (no secret material is involved).
    """
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key_obj = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key_obj = RSAAlgorithm.from_jwk(_dumps(k))
            break
    if key_obj is None:
        raise jwt.InvalidTokenError(f"no JWKS key for kid={kid!r}")
    options = {"require": ["exp", "aud", "iss"]}
    # `now` lets tests pin the clock; PyJWT reads it via leeway/exp otherwise.
    kwargs: dict[str, Any] = {}
    if now is not None:
        # PyJWT 2.x doesn't take an explicit `now`; emulate by adjusting leeway
        # is brittle, so tests pass tokens with a future exp instead.
        pass
    return jwt.decode(
        token,
        key=key_obj,
        algorithms=["RS256"],
        audience=expected_aud,
        issuer=access_issuer(team_domain),
        leeway=leeway,
        options=options,
        **kwargs,
    )


def _dumps(obj: Any) -> str:
    import json

    return json.dumps(obj)


def authorize_request(
    headers: Mapping[str, str],
    *,
    mode: str = "strict",
    # Cloudflare Access (the target keyless mechanism)
    access_team_domain: Optional[str] = None,
    access_aud: Optional[str] = None,
    get_jwks: Optional[Callable[[], Mapping[str, Any]]] = None,
    # Legacy HMAC (accepted in parallel during cutover; removed at the end)
    internal_secret: Optional[str] = None,
) -> tuple[bool, str]:
    """Dual-accept request authorization for the dispatcher's strict mode.

    Order (Stage-E cutover):
      1. mode == "off"  → allow (dev only).
      2. A valid Cloudflare Access JWT  → allow (the keyless end state).
      3. A valid legacy HMAC `x-internal-trust` header  → allow (bridge; remove
         once the Worker no longer sends it).
      4. otherwise → deny.

    Returns (ok, reason). The pod holds NO signing secret for path 2 — only the
    public JWKS via get_jwks(). Path 3 exists only so the cutover is zero-downtime;
    delete `internal_secret` + DISPATCHER_INTERNAL_SECRET to complete Stage E.
    """
    if mode == "off":
        return True, "auth-off"

    if mode != "strict":
        return False, f"unknown DISPATCHER_AUTH_MODE={mode!r} (expected off|strict)"

    lower = {k.lower(): v for k, v in headers.items()}

    # 2) Cloudflare Access JWT (keyless — preferred).
    if access_team_domain and access_aud and get_jwks is not None:
        token = lower.get(ACCESS_JWT_HEADER) or _cookie(lower.get("cookie", ""), ACCESS_COOKIE)
        if token:
            try:
                verify_access_jwt(
                    token,
                    team_domain=access_team_domain,
                    expected_aud=access_aud,
                    jwks=get_jwks(),
                )
                return True, "access-jwt"
            except jwt.InvalidTokenError as e:
                return False, f"invalid Cloudflare Access JWT: {e}"

    # 3) Legacy HMAC shared secret (bridge — constant-time compare).
    if internal_secret:
        provided = lower.get(LEGACY_HMAC_HEADER, "")
        if provided and _hmac.compare_digest(provided, internal_secret):
            return True, "legacy-hmac"
        return False, f"missing or invalid {LEGACY_HMAC_HEADER} header"

    # No Access config and no HMAC secret → strict mode cannot authorize.
    return False, "strict mode: no Cloudflare Access config and no internal secret"


def _cookie(cookie_header: str, name: str) -> str:
    for part in cookie_header.split(";"):
        k, _, v = part.strip().partition("=")
        if k == name:
            return v
    return ""
