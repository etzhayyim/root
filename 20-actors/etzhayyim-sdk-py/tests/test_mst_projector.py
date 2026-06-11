"""Tests for etzhayyim_sdk.mst_projector — SDK client wrapper (M5).

All tests use httpx.MockTransport injected via mst_projector._inject_transport()
— no real network calls are made.

Coverage:
  test_query_by_collection_happy     — 200 → records + cursor propagated
  test_query_by_did_with_filter      — 200 → records filtered by DID
  test_query_by_field_happy          — 200 → records list returned
  test_count_by_collection_happy     — 200 → count + asOf returned
  test_network_error_raises          — ConnectError → MstProjectorNetworkError
  test_server_error_500              — HTTP 500 → MstProjectorServerError
  test_400_error                     — HTTP 400 → MstProjectorError (not server error)
  test_base_url_env_var_override     — ETZHAYYIM_MST_PROJECTOR_URL env used in request URL

Per ADR-2605215500 §5 M5 milestone.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))


# ── Transport helpers ──────────────────────────────────────────────────────────


def _json_handler(
    status_code: int = 200,
    body: dict[str, Any] | None = None,
) -> httpx.MockTransport:
    """Return a MockTransport that always responds with *status_code* and JSON *body*."""

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            headers={"content-type": "application/json"},
            content=json.dumps(body or {}).encode(),
        )

    return httpx.MockTransport(_handler)


def _error_handler() -> httpx.MockTransport:
    """Return a MockTransport that raises ConnectError on every request."""

    def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    return httpx.MockTransport(_handler)


def _capturing_handler(
    responses: list[dict[str, Any]],
    captured_urls: list[str] | None = None,
    captured_bodies: list[dict[str, Any]] | None = None,
) -> httpx.MockTransport:
    """MockTransport that returns responses in order and records request info."""
    idx = {"i": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        if captured_urls is not None:
            captured_urls.append(str(request.url))
        if captured_bodies is not None:
            captured_bodies.append(json.loads(request.content))
        resp = responses[min(idx["i"], len(responses) - 1)]
        idx["i"] += 1
        return httpx.Response(
            status_code=resp.get("status_code", 200),
            headers={"content-type": "application/json"},
            content=json.dumps(resp.get("body", {})).encode(),
        )

    return httpx.MockTransport(_handler)


def _inject(transport: httpx.MockTransport) -> None:
    from etzhayyim_sdk import mst_projector

    mst_projector._inject_transport(transport)


# ── query_by_collection ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_by_collection_happy() -> None:
    """Returns records list and cursor from server response."""
    from etzhayyim_sdk import mst_projector

    server_body = {
        "records": [
            {"did": "did:plc:aaa", "rkey": "r1"},
            {"did": "did:plc:bbb", "rkey": "r2"},
        ],
        "cursor": "2",
    }
    _inject(_json_handler(200, server_body))
    result = await mst_projector.query_by_collection(
        "com.etzhayyim.test.record", limit=10
    )
    assert len(result["records"]) == 2
    assert result["cursor"] == "2"
    assert result["records"][0]["did"] == "did:plc:aaa"


@pytest.mark.asyncio
async def test_query_by_collection_no_cursor() -> None:
    """cursor=None is preserved when server returns null."""
    from etzhayyim_sdk import mst_projector

    _inject(_json_handler(200, {"records": [], "cursor": None}))
    result = await mst_projector.query_by_collection("com.etzhayyim.test.record")
    assert result["records"] == []
    assert result["cursor"] is None


# ── query_by_did ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_by_did_with_filter() -> None:
    """Sends collection in payload when specified; returns filtered records."""
    from etzhayyim_sdk import mst_projector

    captured_bodies: list[dict[str, Any]] = []
    server_body = {
        "records": [{"did": "did:plc:alice", "rkey": "r1"}],
        "cursor": None,
    }
    _inject(
        _capturing_handler(
            [{"status_code": 200, "body": server_body}],
            captured_bodies=captured_bodies,
        )
    )
    result = await mst_projector.query_by_did(
        "did:plc:alice",
        collection="com.etzhayyim.test.record",
        limit=20,
    )
    assert len(result["records"]) == 1
    assert result["records"][0]["did"] == "did:plc:alice"
    # Verify request payload has collection field
    assert captured_bodies[0]["collection"] == "com.etzhayyim.test.record"
    assert captured_bodies[0]["did"] == "did:plc:alice"
    assert captured_bodies[0]["limit"] == 20


@pytest.mark.asyncio
async def test_query_by_did_without_collection() -> None:
    """Omits collection from payload when not specified."""
    from etzhayyim_sdk import mst_projector

    captured_bodies: list[dict[str, Any]] = []
    _inject(
        _capturing_handler(
            [{"status_code": 200, "body": {"records": [], "cursor": None}}],
            captured_bodies=captured_bodies,
        )
    )
    await mst_projector.query_by_did("did:plc:bob")
    assert "collection" not in captured_bodies[0]
    assert captured_bodies[0]["did"] == "did:plc:bob"


# ── query_by_field ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_by_field_happy() -> None:
    """Sends camelCase fieldName and fieldValue; returns records list."""
    from etzhayyim_sdk import mst_projector

    captured_bodies: list[dict[str, Any]] = []
    server_body = {
        "records": [
            {"did": "did:plc:a", "rkey": "r1", "status": "published"},
            {"did": "did:plc:b", "rkey": "r2", "status": "published"},
        ]
    }
    _inject(
        _capturing_handler(
            [{"status_code": 200, "body": server_body}],
            captured_bodies=captured_bodies,
        )
    )
    result = await mst_projector.query_by_field(
        "com.etzhayyim.test.record", "status", "published", limit=5
    )
    assert len(result["records"]) == 2
    # Verify wire format uses camelCase
    assert captured_bodies[0]["fieldName"] == "status"
    assert captured_bodies[0]["fieldValue"] == "published"
    assert captured_bodies[0]["limit"] == 5


# ── count_by_collection ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_count_by_collection_happy() -> None:
    """Returns count and asOf from server response."""
    from etzhayyim_sdk import mst_projector

    server_body = {"count": 42, "asOf": "2026-05-21T00:00:00Z"}
    _inject(_json_handler(200, server_body))
    result = await mst_projector.count_by_collection("com.etzhayyim.test.record")
    assert result["count"] == 42
    assert result["asOf"] == "2026-05-21T00:00:00Z"


# ── Error handling ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_network_error_raises() -> None:
    """ConnectError from transport is wrapped as MstProjectorNetworkError."""
    from etzhayyim_sdk import mst_projector
    from etzhayyim_sdk.mst_projector import MstProjectorNetworkError

    _inject(_error_handler())
    with pytest.raises(MstProjectorNetworkError, match="network error"):
        await mst_projector.query_by_collection("com.etzhayyim.test.record")


@pytest.mark.asyncio
async def test_server_error_500() -> None:
    """HTTP 500 response raises MstProjectorServerError."""
    from etzhayyim_sdk import mst_projector
    from etzhayyim_sdk.mst_projector import MstProjectorServerError

    _inject(_json_handler(500, {"error": "InternalError", "message": "oops"}))
    with pytest.raises(MstProjectorServerError, match="HTTP 500"):
        await mst_projector.query_by_collection("com.etzhayyim.test.record")


@pytest.mark.asyncio
async def test_400_error() -> None:
    """HTTP 400 raises MstProjectorError (not MstProjectorServerError)."""
    from etzhayyim_sdk import mst_projector
    from etzhayyim_sdk.mst_projector import MstProjectorError, MstProjectorServerError

    _inject(_json_handler(400, {"error": "InvalidRequest", "message": "collection required"}))
    with pytest.raises(MstProjectorError) as exc_info:
        await mst_projector.query_by_collection("")
    # Must not be a server error (not 5xx)
    assert not isinstance(exc_info.value, MstProjectorServerError)


# ── Base URL env var ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_base_url_env_var_override() -> None:
    """ETZHAYYIM_MST_PROJECTOR_URL is used as the base for requests."""
    from etzhayyim_sdk import mst_projector

    captured_urls: list[str] = []
    _inject(
        _capturing_handler(
            [{"status_code": 200, "body": {"records": [], "cursor": None}}],
            captured_urls=captured_urls,
        )
    )
    with patch.dict(
        os.environ,
        {"ETZHAYYIM_MST_PROJECTOR_URL": "http://my-projector.local:9999"},
    ):
        await mst_projector.query_by_collection("com.etzhayyim.test.record")

    assert len(captured_urls) == 1
    assert captured_urls[0].startswith("http://my-projector.local:9999/")
