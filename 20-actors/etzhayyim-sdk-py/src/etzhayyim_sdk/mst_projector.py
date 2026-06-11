"""mst-projector SDK client — wraps the 4 XRPC endpoints in typed async functions.

Per ADR-2605215500 §5 M5 milestone. Used by yoro / shinka / joucho cells to query
indexed views instead of client-side filtering against the 100-record cap from
pds.list_records.

Configuration:
  ETZHAYYIM_MST_PROJECTOR_URL — base URL of the mst-projector query_api server.
                                 Default: http://simeon.local:8765

Usage::

    from etzhayyim_sdk import mst_projector

    result = await mst_projector.query_by_collection(
        "com.etzhayyim.shinka.heartbeat", limit=100
    )
    for record in result["records"]:
        ...

    # SDK-only test override
    from etzhayyim_sdk.mst_projector import _inject_transport
    _inject_transport(httpx.MockTransport(handler))
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .errors import EtzhayyimSdkError


class MstProjectorError(EtzhayyimSdkError):
    """Base error for mst-projector client failures."""


class MstProjectorNetworkError(MstProjectorError):
    """Raised when the HTTP request to mst-projector fails at the transport layer."""


class MstProjectorServerError(MstProjectorError):
    """Raised when mst-projector returns an HTTP 5xx response."""


# ── Singleton client ────────────────────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def _inject_transport(transport: httpx.MockTransport) -> None:
    """Replace the singleton client with one backed by *transport*.

    Used exclusively in tests to avoid real network calls.

    Args:
        transport: An ``httpx.MockTransport`` instance.
    """
    global _client
    _client = httpx.AsyncClient(transport=transport, timeout=30.0)


def _base_url() -> str:
    """Return the mst-projector server base URL from env or default."""
    return os.environ.get(
        "ETZHAYYIM_MST_PROJECTOR_URL", "http://simeon.local:8765"
    )


# ── Internal XRPC call helper ──────────────────────────────────────────────────


async def _call(nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    """POST to ``/xrpc/<nsid>`` with JSON *body*, return parsed response.

    Args:
        nsid: NSID of the endpoint (e.g. ``com.etzhayyim.mstProjector.queryByCollection``).
        body: Request payload that matches the lexicon input schema.

    Returns:
        Parsed JSON response dict.

    Raises:
        MstProjectorNetworkError: transport-level failure (connection refused, timeout…).
        MstProjectorServerError:  server returned HTTP 5xx.
        MstProjectorError:        server returned HTTP 4xx (bad request, unknown collection…).
    """
    url = f"{_base_url()}/xrpc/{nsid}"
    client = _get_client()
    try:
        resp = await client.post(url, json=body)
    except httpx.HTTPError as exc:
        raise MstProjectorNetworkError(
            f"network error calling {nsid}: {exc}"
        ) from exc
    if resp.status_code >= 500:
        raise MstProjectorServerError(
            f"{nsid} HTTP {resp.status_code}: {resp.text[:200]}"
        )
    if resp.status_code >= 400:
        try:
            body_json = resp.json()
        except Exception:
            body_json = {"raw": resp.text[:200]}
        raise MstProjectorError(f"{nsid} HTTP {resp.status_code}: {body_json}")
    return resp.json()


# ── Public API ─────────────────────────────────────────────────────────────────


async def query_by_collection(
    collection: str,
    *,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Query all records in *collection*.

    Args:
        collection: AT Protocol collection NSID (e.g. ``com.etzhayyim.shinka.heartbeat``).
        limit:      Maximum records to return per page (1–1000, default 50).
        cursor:     Opaque pagination cursor returned by a previous call; omit
                    for the first page.

    Returns:
        ``{"records": [...], "cursor": str | None}``

    Raises:
        MstProjectorNetworkError, MstProjectorServerError, MstProjectorError.
    """
    payload: dict[str, Any] = {"collection": collection, "limit": limit}
    if cursor is not None:
        payload["cursor"] = cursor
    return await _call("com.etzhayyim.mstProjector.queryByCollection", payload)


async def query_by_did(
    did: str,
    *,
    collection: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Query records authored by *did*, optionally filtered to *collection*.

    Args:
        did:        DID of the authoring repo (e.g. ``did:plc:abc123``).
        collection: AT Protocol collection NSID; omit to search all indexed
                    collections (slower cross-collection path).
        limit:      Maximum records per page (default 50).
        cursor:     Opaque pagination cursor from a previous call.

    Returns:
        ``{"records": [...], "cursor": str | None}``
    """
    payload: dict[str, Any] = {"did": did, "limit": limit}
    if collection:
        payload["collection"] = collection
    if cursor is not None:
        payload["cursor"] = cursor
    return await _call("com.etzhayyim.mstProjector.queryByDid", payload)


async def query_by_field(
    collection: str,
    field_name: str,
    field_value: str,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    """Query records in *collection* where ``field_name == field_value``.

    Args:
        collection:  AT Protocol collection NSID.
        field_name:  Top-level record field to filter on.  Must match
                     ``[A-Za-z_][A-Za-z0-9_]*`` (server enforces this).
        field_value: Value to match (exact string equality).
        limit:       Maximum records to return (default 50).

    Returns:
        ``{"records": [...]}``
    """
    return await _call(
        "com.etzhayyim.mstProjector.queryByField",
        {
            "collection": collection,
            "fieldName": field_name,
            "fieldValue": field_value,
            "limit": limit,
        },
    )


async def count_by_collection(collection: str) -> dict[str, Any]:
    """Return the total record count for *collection*.

    Args:
        collection: AT Protocol collection NSID.

    Returns:
        ``{"count": int, "asOf": str}`` — asOf is an ISO 8601 UTC timestamp.
    """
    return await _call(
        "com.etzhayyim.mstProjector.countByCollection",
        {"collection": collection},
    )
