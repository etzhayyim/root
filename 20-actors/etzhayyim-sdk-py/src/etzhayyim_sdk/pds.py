"""pds — AT Protocol PDS XRPC client (real impl, M3).

Provides async XRPC wrappers over com.atproto.repo.{putRecord, getRecord,
listRecords, deleteRecord}.  All writes route through this module; direct
use of @atproto/api or httpx from app code is prohibited
(ADR-2605172000 substrate boundary).

Configuration (env vars):
  ETZHAYYIM_PDS_URL         — PDS base URL (default: https://atproto.etzhayyim.com)
  ETZHAYYIM_PDS_AUTH_TOKEN  — DID-bound JWT for authenticated XRPC calls
  ETZHAYYIM_PDS_DEFAULT_REPO — default repo DID/handle (used when did=None)

ADR references:
  ADR-2605172000 — RW-free substrate hard rule (this is the ONLY seam for PDS writes)
  ADR-2605173000 — PDS endpoint https://atproto.etzhayyim.com
  ADR-2605171800 — LangGraph MST → IPFS → Base L2 anchor pipeline (Stage 1-2)
  ADR-2605215200 — shinka cells use put_record for shinkaHeartbeat
  ADR-2605215300 — yoro functions use put_record for feed.post / actor.profile / translationLink

Lexicon wire shapes (read 00-contracts/lexicons/com/atproto/repo/):
  putRecord    — POST /xrpc/com.atproto.repo.putRecord
  getRecord    — GET  /xrpc/com.atproto.repo.getRecord
  listRecords  — GET  /xrpc/com.atproto.repo.listRecords
  deleteRecord — POST /xrpc/com.atproto.repo.deleteRecord
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator
from urllib.parse import urljoin

import httpx

from etzhayyim_sdk.errors import (
    PdsAuthError,
    PdsNetworkError,
    PdsNotFoundError,
    PdsServerError,
)

# ---------------------------------------------------------------------------
# Module-level singleton client (lazy init, connection pooling)
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return the module-level singleton httpx.AsyncClient, creating it lazily."""
    global _client
    if _client is None or _client.is_closed:
        _client = _build_client()
    return _client


def _build_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    """Construct a new AsyncClient.  Exposed so tests can inject MockTransport."""
    pds_url = os.environ.get("ETZHAYYIM_PDS_URL", "https://atproto.etzhayyim.com")
    auth_token = os.environ.get("ETZHAYYIM_PDS_AUTH_TOKEN", "")
    headers: dict[str, str] = {
        "content-type": "application/json",
        "accept": "application/json",
    }
    if auth_token:
        headers["authorization"] = f"Bearer {auth_token}"
    kwargs: dict[str, Any] = {
        "base_url": pds_url,
        "headers": headers,
        "timeout": httpx.Timeout(30.0, connect=10.0),
    }
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.AsyncClient(**kwargs)


def _inject_transport(transport: httpx.AsyncBaseTransport) -> None:
    """Replace the module singleton with a client backed by *transport*.

    Called from tests to inject httpx.MockTransport without touching env vars.
    """
    global _client
    _client = _build_client(transport=transport)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_XRPC_BASE = "/xrpc/"


def _xrpc_url(nsid: str) -> str:
    return _XRPC_BASE + nsid


def _default_repo() -> str:
    return os.environ.get("ETZHAYYIM_PDS_DEFAULT_REPO", "did:web:etzhayyim.com")


def _parse_at_uri(uri: str) -> tuple[str, str, str]:
    """Parse an AT URI ``at://repo/collection/rkey`` into its three components.

    Returns (repo, collection, rkey).  Raises ValueError on malformed input.
    """
    if not uri.startswith("at://"):
        raise ValueError(f"Not an AT URI: {uri!r}")
    rest = uri[5:]
    parts = rest.split("/", 2)
    if len(parts) != 3:
        raise ValueError(f"AT URI must have repo/collection/rkey: {uri!r}")
    return parts[0], parts[1], parts[2]


async def _check_response(resp: httpx.Response) -> None:
    """Raise a typed PdsError for non-2xx responses."""
    if resp.status_code in (401, 403):
        raise PdsAuthError(
            f"PDS auth error {resp.status_code}: {resp.text!r}"
        )
    if resp.status_code == 404:
        raise PdsNotFoundError(f"PDS 404: {resp.text!r}")
    if resp.status_code >= 500:
        raise PdsServerError(resp.status_code, resp.text)
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def put_record(
    collection: str,
    record: dict[str, Any],
    *,
    rkey: str | None = None,
    did: str | None = None,
) -> str:
    """Write an AT record to the PDS via com.atproto.repo.putRecord.

    Maps vendor pattern:
      INSERT INTO vertex_* → PDS putRecord → MST commit

    Args:
        collection: NSID of the record collection (e.g. ``app.bsky.feed.post``).
        record:     Record body dict. Should include ``$type`` matching *collection*.
        rkey:       Record key.  Defaults to ``"self"`` when None.
        did:        Repo DID/handle.  Defaults to ``ETZHAYYIM_PDS_DEFAULT_REPO``
                    env var or ``did:web:etzhayyim.com``.

    Returns:
        AT URI of the created/updated record (e.g. ``at://did:web:…/collection/rkey``).

    Raises:
        PdsAuthError:    HTTP 401/403.
        PdsNotFoundError: HTTP 404.
        PdsServerError:  HTTP 5xx.
        PdsNetworkError: Transport / connection error.

    ADR-2605171800 Stage 1-2: MST commit is the primary write.
    IPFS pin (Stage 3) and Base L2 anchor (Stage 4) are triggered
    downstream by the anchor-cron job, not inline here.
    ADR-2605215200 §1 ShinkaHeartbeatCell: uses this for shinkaHeartbeat.
    ADR-2605215300 §3: yoro calls pds.put_record for feed.post / translationLink.
    """
    repo = did or _default_repo()
    effective_rkey = rkey or "self"

    payload: dict[str, Any] = {
        "repo": repo,
        "collection": collection,
        "rkey": effective_rkey,
        "record": record,
    }

    client = _get_client()
    try:
        resp = await client.post(_xrpc_url("com.atproto.repo.putRecord"), json=payload)
    except httpx.RequestError as exc:
        raise PdsNetworkError(exc) from exc

    await _check_response(resp)
    data = resp.json()
    return data["uri"]


async def dispatch(
    collection: str,
    record: dict[str, Any],
    *,
    did: str | None = None,
) -> str:
    """Alias for put_record (matches existing yoro pds.dispatch() call convention).

    Used by yoro social primitives that call ``pds.dispatch(collection=…, record=…)``.
    Delegates to :func:`put_record`; the distinction is convention only.

    See :func:`put_record` for full argument/error documentation.
    ADR-2605215300 §3 substrate write-path mapping.
    """
    return await put_record(collection, record, did=did)


async def get_record(uri: str) -> dict[str, Any]:
    """Read a single AT record from the PDS via com.atproto.repo.getRecord.

    Maps vendor pattern:
      SELECT FROM vertex_repo_record WHERE uri=… → getRecord(repo, collection, rkey)

    Args:
        uri: AT URI of the record (``at://repo/collection/rkey``).

    Returns:
        The raw AT record dict ``{uri, cid, value}``.

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.
        ValueError: if *uri* is malformed.

    ADR-2605215300 §3 (SELECT mapping row #10).
    """
    repo, collection, rkey = _parse_at_uri(uri)
    params: dict[str, str] = {
        "repo": repo,
        "collection": collection,
        "rkey": rkey,
    }

    client = _get_client()
    try:
        resp = await client.get(_xrpc_url("com.atproto.repo.getRecord"), params=params)
    except httpx.RequestError as exc:
        raise PdsNetworkError(exc) from exc

    await _check_response(resp)
    return resp.json()


async def list_records(
    repo: str,
    collection: str,
    *,
    limit: int = 100,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List AT records from the PDS via com.atproto.repo.listRecords.

    Maps vendor pattern:
      SELECT FROM vertex_repo_record WHERE repo=… LIMIT N

    Args:
        repo:       Handle or DID of the repo.
        collection: NSID of the record collection.
        limit:      Max records to return (1–100, default 100).
        cursor:     Pagination cursor from a previous call.

    Returns:
        ``{"records": [...], "cursor": str | None}``

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.

    ADR-2605215300 §3 (SELECT mapping rows #11/#14).
    """
    params: dict[str, Any] = {
        "repo": repo,
        "collection": collection,
        "limit": min(max(limit, 1), 100),
    }
    if cursor is not None:
        params["cursor"] = cursor

    client = _get_client()
    try:
        resp = await client.get(_xrpc_url("com.atproto.repo.listRecords"), params=params)
    except httpx.RequestError as exc:
        raise PdsNetworkError(exc) from exc

    await _check_response(resp)
    data = resp.json()
    return {
        "records": data.get("records", []),
        "cursor": data.get("cursor"),
    }


async def delete_record(uri: str) -> None:
    """Delete an AT record from the PDS via com.atproto.repo.deleteRecord.

    Args:
        uri: AT URI of the record (``at://repo/collection/rkey``).

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.
        ValueError: if *uri* is malformed.
    """
    repo, collection, rkey = _parse_at_uri(uri)
    payload: dict[str, Any] = {
        "repo": repo,
        "collection": collection,
        "rkey": rkey,
    }

    client = _get_client()
    try:
        resp = await client.post(_xrpc_url("com.atproto.repo.deleteRecord"), json=payload)
    except httpx.RequestError as exc:
        raise PdsNetworkError(exc) from exc

    await _check_response(resp)


# ---------------------------------------------------------------------------
# Firehose subscribe (WebSocket stub — M4 deadline)
# ---------------------------------------------------------------------------


async def subscribe(
    collections: list[str],
    *,
    since_cursor: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Subscribe to the AT firehose for the given collections.

    Yields commit events as dicts ``{collection, rkey, record, did, cursor}``.

    Note:
        WebSocket implementation deferred.  Raises ``NotImplementedError``
        until the WebSocket client is wired (M4 deliverable; requires a
        separate ADR for the ``com.atproto.sync.subscribeRepos`` wire protocol
        and reconnect semantics).

    ADR-2605215200 §1 KarmaHegemonObservationCell listens on
    ``app.etzhayyim.shinka.kyumeiSignal`` via this subscription.
    """
    raise NotImplementedError(
        "pds.subscribe — M4 deadline.  WebSocket impl requires separate ADR "
        "for com.atproto.sync.subscribeRepos reconnect semantics."
    )
    yield {}  # type: ignore[misc]  # unreachable; satisfies AsyncIterator type


# ---------------------------------------------------------------------------
# Legacy compat shim (old keyword-only signature used by existing callers)
# ---------------------------------------------------------------------------


async def firehose_subscribe(
    collections: list[str],
) -> AsyncIterator[dict[str, Any]]:
    """Deprecated alias for :func:`subscribe`.

    ADR-2605215200 §1 KarmaHegemonObservationCell trigger.
    """
    async for event in subscribe(collections):
        yield event
