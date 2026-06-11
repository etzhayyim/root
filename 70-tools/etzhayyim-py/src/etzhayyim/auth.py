"""Auth helpers — token resolution, header construction.

Priority: etzhayyim_TOKEN env > macOS Keychain api_key > ~/.etzhayyim/auth.json
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

_KEYCHAIN_SERVICE = "etzhayyim.auth"
_AUTH_FILE = Path.home() / ".etzhayyim" / "auth.json"
_DEFAULT_PDS = "https://atproto.etzhayyim.com"


def _read_keychain(account: str) -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", _KEYCHAIN_SERVICE, "-a", account, "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _load_auth_file() -> dict:
    try:
        return json.loads(_AUTH_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def resolve_token() -> str | None:
    if tok := os.environ.get("etzhayyim_TOKEN"):
        return tok
    if key := _read_keychain("api_key"):
        return key
    store = _load_auth_file()
    # prefer api_key > id_token > access_token
    return store.get("api_key") or store.get("id_token") or store.get("access_token")


def resolve_active_did() -> str | None:
    store = _load_auth_file()
    return store.get("active_did") or store.get("sub")


def resolve_pds() -> str:
    return os.environ.get("etzhayyim_PDS_URL", _DEFAULT_PDS).rstrip("/")


def resolve_org_hint() -> str | None:
    if org := os.environ.get("etzhayyim_ORG_ID"):
        return org
    did = resolve_active_did()
    if did and did.startswith("did:plc:"):
        return did
    return None


def auth_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    if tok := resolve_token():
        headers["Authorization"] = f"Bearer {tok}"
    if did := resolve_active_did():
        headers["X-Active-DID"] = did
    if org := resolve_org_hint():
        headers["X-etzhayyim-Org-Id"] = org
    return headers


# ── Scoped-JWT auto-wrap (port of scoped_auth.go) ─────────────────────────────

_SERVICE_AUTH_NSID = "com.atproto.server.getServiceAuth"
_SCOPED_JWT_TTL = 300
_SCOPED_JWT_SKEW = 10

_scoped_jwt_cache: dict[str, tuple[str, float]] = {}
_scoped_jwt_lock = threading.Lock()


def _scoped_cache_key(base_token: str, nsid: str) -> str:
    return hashlib.sha256(base_token.encode()).hexdigest()[:16] + ":" + nsid


def _scoped_auth_enabled() -> bool:
    v = os.environ.get("etzhayyim_SCOPED_AUTH", "").lower().strip()
    return v not in ("off", "0", "false")


def mint_scoped_jwt(base_token: str, nsid: str) -> str:
    """Mint a short-lived scoped JWT for the given NSID via com.atproto.server.getServiceAuth.

    Returns "" on any failure (graceful degradation to base token).
    Caches tokens for 290s (TTL 300s minus 10s skew).
    Skip conditions: empty token/nsid, nsid is the bootstrap NSID itself, or etzhayyim_SCOPED_AUTH=off.
    """
    if not base_token or not nsid or nsid == _SERVICE_AUTH_NSID:
        return ""
    if not _scoped_auth_enabled():
        return ""

    cache_key = _scoped_cache_key(base_token, nsid)
    now = time.time()
    with _scoped_jwt_lock:
        if cache_key in _scoped_jwt_cache:
            token, exp = _scoped_jwt_cache[cache_key]
            if now < exp:
                return token

    pds_url = resolve_pds()
    hostname = urlparse(pds_url).hostname or ""
    audience = f"did:web:{hostname}" if hostname else ""
    exp_unix = int(now) + _SCOPED_JWT_TTL

    try:
        import httpx
        resp = httpx.post(
            f"{pds_url}/xrpc/{_SERVICE_AUTH_NSID}",
            json={"aud": audience, "lxm": nsid, "exp": exp_unix},
            headers={"Authorization": f"Bearer {base_token}"},
            timeout=8,
        )
        if resp.status_code >= 400:
            return ""
        token = resp.json().get("token", "")
        if not token:
            return ""
    except Exception:
        return ""

    with _scoped_jwt_lock:
        _scoped_jwt_cache[cache_key] = (token, now + _SCOPED_JWT_TTL - _SCOPED_JWT_SKEW)
    return token


def scoped_auth_headers(nsid: str) -> dict[str, str]:
    """Build auth headers, upgrading to a scoped JWT for the given NSID when possible."""
    headers = auth_headers()
    base_tok = resolve_token() or ""
    scoped = mint_scoped_jwt(base_tok, nsid)
    if scoped:
        headers["Authorization"] = f"Bearer {scoped}"
    return headers
