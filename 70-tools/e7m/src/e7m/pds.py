"""PDS / XRPC operator surface.

Read-only and read/write helpers for probing the etzhayyim substrate from
the CLI or MCP. Mirrors the manual `curl` debugging the operator was
doing by hand (timeline failures, identity lookups, account seeding).

Per ADR-2605192100 §1.6 substrate boundary, this is the *only* sanctioned
external HTTP touchpoint for ad-hoc PDS introspection — agents and
operators alike route through here so audit hooks can land in one spot.

Hosts:
    atproto = https://atproto.etzhayyim.com   (live PDS used by yoro frontend)
    pds     = https://pds.etzhayyim.com       (xrpc-adapter ACTOR_DID backend)
    yoro    = https://yoro.etzhayyim.com      (yoro static + xrpc routes)
    apex    = https://etzhayyim.com           (did-web proxy → yoro)
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx


HOSTS: dict[str, str] = {
    "atproto": "https://atproto.etzhayyim.com",
    "pds":     "https://pds.etzhayyim.com",
    "yoro":    "https://yoro.etzhayyim.com",
    "apex":    "https://etzhayyim.com",
}

# Read-only NSIDs we deliberately allow through the generic xrpc helper.
# Writes (createAccount, createRecord) must use the dedicated functions so
# the operator/agent is explicit about side effects.
_SAFE_NSID_PREFIXES = (
    "com.atproto.server.describeServer",
    "com.atproto.repo.describeRepo",
    "com.atproto.repo.listRecords",
    "com.atproto.repo.getRecord",
    "com.atproto.identity.resolveHandle",
    "com.atproto.sync.listRepos",
    "com.atproto.sync.getLatestCommit",
    "com.atproto.server.getSession",
    "app.bsky.",
    "com.etzhayyim.yoro.",
)


def _resolve_host(host: str) -> str:
    """Accept either a short alias (atproto/pds/yoro/apex) or a raw URL."""
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    if host in HOSTS:
        return HOSTS[host]
    raise ValueError(
        f"unknown host '{host}' — pass an alias ({'/'.join(HOSTS)}) or a full URL"
    )


def _xrpc_url(host: str, nsid: str) -> str:
    return f"{_resolve_host(host)}/xrpc/{nsid}"


def _err(message: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "error": message}
    out.update(extra)
    return out


def _try_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return resp.text[:2000]


# ── read-only introspection ──────────────────────────────────────────────

def describe_server(host: str = "atproto") -> dict[str, Any]:
    """GET com.atproto.server.describeServer — server identity + policy."""
    try:
        r = httpx.get(_xrpc_url(host, "com.atproto.server.describeServer"), timeout=10.0)
    except httpx.HTTPError as exc:
        return _err(f"network error: {exc}", host=host)
    body = _try_json(r)
    return {
        "ok": r.is_success,
        "host": _resolve_host(host),
        "status": r.status_code,
        "server": body,
    }


def list_repos(host: str = "atproto", limit: int = 20, cursor: str | None = None) -> dict[str, Any]:
    """GET com.atproto.sync.listRepos — what DIDs the PDS knows about."""
    params: dict[str, Any] = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    url = _xrpc_url(host, "com.atproto.sync.listRepos") + "?" + urlencode(params)
    try:
        r = httpx.get(url, timeout=15.0)
    except httpx.HTTPError as exc:
        return _err(f"network error: {exc}", host=host)
    body = _try_json(r)
    repos = body.get("repos", []) if isinstance(body, dict) else []
    return {
        "ok": r.is_success,
        "host": _resolve_host(host),
        "status": r.status_code,
        "count": len(repos),
        "cursor": body.get("cursor") if isinstance(body, dict) else None,
        "repos": repos,
    }


def describe_repo(did: str, host: str = "atproto") -> dict[str, Any]:
    """GET com.atproto.repo.describeRepo — is this DID known to the PDS?"""
    url = _xrpc_url(host, "com.atproto.repo.describeRepo") + "?" + urlencode({"repo": did})
    try:
        r = httpx.get(url, timeout=10.0)
    except httpx.HTTPError as exc:
        return _err(f"network error: {exc}", host=host)
    body = _try_json(r)
    exists = bool(
        isinstance(body, dict)
        and body.get("did")
        and body.get("did") != "did:web:"
        and not body.get("error")
    )
    return {
        "ok": r.is_success,
        "host": _resolve_host(host),
        "status": r.status_code,
        "did": did,
        "exists": exists,
        "repo": body,
    }


def resolve_handle(handle: str, host: str = "atproto") -> dict[str, Any]:
    """GET com.atproto.identity.resolveHandle — handle → DID."""
    url = _xrpc_url(host, "com.atproto.identity.resolveHandle") + "?" + urlencode({"handle": handle})
    try:
        r = httpx.get(url, timeout=10.0)
    except httpx.HTTPError as exc:
        return _err(f"network error: {exc}", host=host)
    return {
        "ok": r.is_success,
        "host": _resolve_host(host),
        "status": r.status_code,
        "handle": handle,
        "body": _try_json(r),
    }


def xrpc(
    nsid: str,
    *,
    method: str = "GET",
    host: str = "apex",
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    bearer: str | None = None,
    allow_write: bool = False,
) -> dict[str, Any]:
    """Generic XRPC call.

    Defaults to GET against the apex (etzhayyim.com), which mirrors the
    yoro frontend's request shape. Write methods (POST + non-safelisted
    NSID) require `allow_write=True` so an operator can't accidentally
    mutate state.
    """
    method = method.upper()
    if method not in {"GET", "POST"}:
        return _err(f"unsupported HTTP method: {method}")
    is_safe = nsid.startswith(_SAFE_NSID_PREFIXES)
    if method == "POST" and not is_safe and not allow_write:
        return _err(
            "refusing POST to a non-read NSID without allow_write=True",
            nsid=nsid,
        )
    url = _xrpc_url(host, nsid)
    headers: dict[str, str] = {}
    if bearer:
        headers["authorization"] = f"Bearer {bearer}"
    if method == "POST":
        headers["content-type"] = "application/json"
    try:
        if method == "GET":
            r = httpx.get(url, params=params or {}, headers=headers, timeout=15.0)
        else:
            r = httpx.post(url, params=params or {}, json=body or {}, headers=headers, timeout=15.0)
    except httpx.HTTPError as exc:
        return _err(f"network error: {exc}", host=host, nsid=nsid)
    return {
        "ok": r.is_success,
        "host": _resolve_host(host),
        "method": method,
        "nsid": nsid,
        "status": r.status_code,
        "body": _try_json(r),
    }


# ── yoro deployment probe (composite) ────────────────────────────────────

def yoro_probe() -> dict[str, Any]:
    """Snapshot the yoro deployment: bundle entrypoint + feed endpoints.

    Replays the diagnostic curl/browser session that surfaced the
    POST→GET atQuery bug and the `Could not find repo` xrpc-adapter
    error. Idempotent and read-only.
    """
    out: dict[str, Any] = {"ok": True, "checks": {}}

    # 1. Apex serves yoro HTML with a bundle entrypoint
    try:
        r = httpx.get(HOSTS["apex"] + "/", timeout=10.0)
        html = r.text
        import re
        m = re.search(r'/assets/(index-[A-Za-z0-9_-]+\.js)', html)
        entry = m.group(1) if m else None
        out["checks"]["apex_index"] = {
            "ok": r.is_success and entry is not None,
            "status": r.status_code,
            "proxied_by": r.headers.get("x-proxied-by"),
            "proxied_upstream": r.headers.get("x-proxied-upstream"),
            "entry_bundle": entry,
        }
    except httpx.HTTPError as exc:
        out["checks"]["apex_index"] = _err(f"network error: {exc}")
        entry = None

    # 2. Bundle's atQuery uses GET (the POST→GET fix is deployed)
    if entry:
        try:
            r = httpx.get(f"{HOSTS['apex']}/assets/{entry}", timeout=20.0)
            src = r.text
            uses_get = ('Rf("GET",t,void 0,a,o)' in src) or ('"GET",t,void 0,a,o' in src)
            uses_post = ('Rf("POST",t,a,void 0,o)' in src) and not uses_get
            out["checks"]["bundle_atquery"] = {
                "ok": uses_get,
                "uses_get": uses_get,
                "uses_post_bug": uses_post,
                "size_bytes": len(src),
            }
        except httpx.HTTPError as exc:
            out["checks"]["bundle_atquery"] = _err(f"network error: {exc}")

    # 3. Feed endpoints answer through the apex → xrpc-adapter dispatch
    feed_checks: dict[str, Any] = {}
    for nsid in ("app.bsky.feed.getSuggestedFeeds", "app.bsky.feed.getDiscoverFeed", "app.bsky.feed.getTimeline"):
        try:
            r = httpx.get(f"{HOSTS['apex']}/xrpc/{nsid}", params={"limit": 5}, timeout=10.0)
            body = _try_json(r)
            feed_checks[nsid] = {
                "ok": r.is_success,
                "status": r.status_code,
                "feed_len": len(body.get("feed", [])) if isinstance(body, dict) else None,
                "error": body.get("error") if isinstance(body, dict) else None,
                "message": body.get("message") if isinstance(body, dict) else None,
            }
        except httpx.HTTPError as exc:
            feed_checks[nsid] = _err(f"network error: {exc}")
    out["checks"]["feed_endpoints"] = feed_checks

    # Roll up
    failing = [name for name, c in out["checks"].items() if isinstance(c, dict) and not c.get("ok", True)]
    if isinstance(out["checks"].get("feed_endpoints"), dict):
        for nsid, c in out["checks"]["feed_endpoints"].items():
            if not c.get("ok"):
                failing.append(f"feed_endpoints.{nsid}")
    out["ok"] = len(failing) == 0
    out["failing"] = failing
    return out


# ── account / repo mutations (explicit, no defaults) ─────────────────────

def create_account(
    *,
    host: str,
    handle: str,
    did: str | None = None,
    email: str | None = None,
    invite_code: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """POST com.atproto.server.createAccount.

    Requires *explicit* host + handle. Pass invite_code if the PDS demands
    one (see describe_server first). The caller is responsible for storing
    the returned accessJwt / refreshJwt — this function never persists.
    """
    payload: dict[str, Any] = {"handle": handle}
    if did:
        payload["did"] = did
    if email:
        payload["email"] = email
    if invite_code:
        payload["inviteCode"] = invite_code
    if password:
        payload["password"] = password
    return xrpc(
        "com.atproto.server.createAccount",
        method="POST",
        host=host,
        body=payload,
        allow_write=True,
    )
