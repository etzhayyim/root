"""Tests for mst_projector.query_api (M3) — XRPC server handlers.

Uses aiohttp.test_utils for in-process HTTP round-trips and a stub Indexer
that avoids touching LanceDB or the filesystem.  aiohttp is required;
tests are skipped if it is not installed.

Per ADR-2605215500 §3 M3 testing contract.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip all tests if aiohttp is not installed (dep declared in pyproject.toml
# but may not be present in the local venv during CI bootstrapping).
aiohttp = pytest.importorskip("aiohttp")
from aiohttp.test_utils import AioHTTPTestCase  # noqa: E402

from mst_projector.query_api import build_app  # noqa: E402


# ── Stub Indexer ────────────────────────────────────────────────────────────────


def _make_record(did: str, rkey: str, **extra: Any) -> dict[str, Any]:
    return {
        "did": did,
        "rkey": rkey,
        "record_cid": f"bafyrei{rkey}",
        "indexed_at": "2026-05-21T00:00:00Z",
        "record_json": json.dumps({"did": did, "rkey": rkey, **extra}),
        **extra,
    }


def _make_indexer(records: list[dict[str, Any]], collections: list[str] | None = None) -> Any:
    """Return a MagicMock Indexer whose query() returns records."""
    indexer = MagicMock()

    async def _query(
        collection: str,
        filter_sql: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filtered = records
        if filter_sql:
            # Very simple filter evaluation for tests: handle `key = 'value'` patterns
            import re

            m = re.match(r"(\w+)\s*=\s*'(.*?)'", filter_sql)
            if m:
                key, val = m.group(1), m.group(2)
                filtered = [r for r in records if str(r.get(key, "")) == val]
        return filtered[:limit]

    async def _list_collections() -> list[str]:
        return collections or ["com.etzhayyim.test.record"]

    indexer.query = _query
    indexer.list_collections = _list_collections
    return indexer


# ── Test cases ──────────────────────────────────────────────────────────────────


class TestHealthz(AioHTTPTestCase):
    async def get_application(self) -> aiohttp.web.Application:
        return build_app()

    async def test_healthz_returns_200_when_indexer_ok(self) -> None:
        """GET /healthz returns 200 + ok:true when indexer.list_collections succeeds."""
        stub = MagicMock()
        stub.list_collections = AsyncMock(return_value=["com.etzhayyim.test.a", "com.etzhayyim.test.b"])
        stub.data_dir = "/data/mst"

        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.get("/healthz")

        assert resp.status == 200
        body = await resp.json()
        assert body["ok"] is True
        assert body["service"] == "mst-projector"
        assert body["indexed_collections"] == 2
        assert body["data_dir"] == "/data/mst"

    async def test_healthz_returns_503_when_indexer_fails(self) -> None:
        """GET /healthz returns 503 + ok:false when indexer.list_collections raises."""
        stub = MagicMock()
        stub.list_collections = AsyncMock(side_effect=RuntimeError("lancedb unavailable"))

        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.get("/healthz")

        assert resp.status == 503
        body = await resp.json()
        assert body["ok"] is False
        assert body["service"] == "mst-projector"
        assert "lancedb unavailable" in body["error"]


class TestQueryByCollection(AioHTTPTestCase):
    async def get_application(self) -> aiohttp.web.Application:
        return build_app()

    async def test_query_by_collection_happy(self) -> None:
        """Returns records and no cursor when results fit in one page."""
        records = [
            _make_record("did:plc:aaa", "r1"),
            _make_record("did:plc:bbb", "r2"),
            _make_record("did:plc:ccc", "r3"),
        ]
        stub = _make_indexer(records)
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByCollection",
                json={"collection": "com.etzhayyim.test.record", "limit": 50},
            )
        assert resp.status == 200
        body = await resp.json()
        assert len(body["records"]) == 3
        assert body["cursor"] is None

    async def test_query_by_collection_pagination(self) -> None:
        """Cursor is set when results exceed limit; second page works."""
        records = [_make_record("did:plc:a", f"r{i}") for i in range(10)]
        stub = _make_indexer(records)
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            # First page
            resp1 = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByCollection",
                json={"collection": "com.etzhayyim.test.record", "limit": 3},
            )
            body1 = await resp1.json()
            assert resp1.status == 200
            assert len(body1["records"]) == 3
            assert body1["cursor"] == "3"

            # Second page
            resp2 = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByCollection",
                json={
                    "collection": "com.etzhayyim.test.record",
                    "limit": 3,
                    "cursor": body1["cursor"],
                },
            )
            body2 = await resp2.json()
            assert resp2.status == 200
            assert len(body2["records"]) == 3
            assert body2["cursor"] == "6"

    async def test_invalid_request_400_missing_collection(self) -> None:
        """Returns 400 when collection is missing."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.queryByCollection",
            json={"limit": 10},
        )
        assert resp.status == 400
        body = await resp.json()
        assert body["error"] == "InvalidRequest"


class TestQueryByDid(AioHTTPTestCase):
    async def get_application(self) -> aiohttp.web.Application:
        return build_app()

    async def test_query_by_did_specific_collection(self) -> None:
        """Returns only records matching DID in a specific collection."""
        records = [
            _make_record("did:plc:alice", "r1"),
            _make_record("did:plc:bob", "r2"),
            _make_record("did:plc:alice", "r3"),
        ]
        stub = _make_indexer(records)
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByDid",
                json={
                    "did": "did:plc:alice",
                    "collection": "com.etzhayyim.test.record",
                },
            )
        assert resp.status == 200
        body = await resp.json()
        assert all(r["did"] == "did:plc:alice" for r in body["records"])
        assert len(body["records"]) == 2

    async def test_query_by_did_no_collection(self) -> None:
        """Cross-collection query aggregates from all collections."""
        records = [
            _make_record("did:plc:alice", "r1"),
            _make_record("did:plc:alice", "r2"),
        ]
        stub = _make_indexer(
            records, collections=["com.etzhayyim.test.a", "com.etzhayyim.test.b"]
        )
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByDid",
                json={"did": "did:plc:alice"},
            )
        assert resp.status == 200
        body = await resp.json()
        # Should have results from both collections (2 records × 2 collections)
        assert len(body["records"]) >= 2

    async def test_query_by_did_missing_did_400(self) -> None:
        """Returns 400 when did is missing."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.queryByDid",
            json={"collection": "com.etzhayyim.test.record"},
        )
        assert resp.status == 400


class TestQueryByField(AioHTTPTestCase):
    async def get_application(self) -> aiohttp.web.Application:
        return build_app()

    async def test_query_by_field_happy(self) -> None:
        """Returns records matching field value."""
        records = [
            _make_record("did:plc:a", "r1", status="published"),
            _make_record("did:plc:b", "r2", status="draft"),
            _make_record("did:plc:c", "r3", status="published"),
        ]
        stub = _make_indexer(records)
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.queryByField",
                json={
                    "collection": "com.etzhayyim.test.record",
                    "fieldName": "status",
                    "fieldValue": "published",
                },
            )
        assert resp.status == 200
        body = await resp.json()
        assert len(body["records"]) == 2
        assert all(r["status"] == "published" for r in body["records"])

    async def test_query_by_field_sql_injection_blocked(self) -> None:
        """Rejects fieldName containing characters outside [A-Za-z0-9_]."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.queryByField",
            json={
                "collection": "com.etzhayyim.test.record",
                "fieldName": "status'; DROP TABLE--",
                "fieldValue": "x",
            },
        )
        assert resp.status == 400
        body = await resp.json()
        assert body["error"] == "InvalidRequest"

    async def test_query_by_field_numeric_start_blocked(self) -> None:
        """Rejects fieldName starting with a digit."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.queryByField",
            json={
                "collection": "com.etzhayyim.test.record",
                "fieldName": "1badfield",
                "fieldValue": "x",
            },
        )
        assert resp.status == 400

    async def test_query_by_field_missing_params_400(self) -> None:
        """Returns 400 when required params are absent."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.queryByField",
            json={"collection": "com.etzhayyim.test.record"},
        )
        assert resp.status == 400


class TestCountByCollection(AioHTTPTestCase):
    async def get_application(self) -> aiohttp.web.Application:
        return build_app()

    async def test_count_by_collection(self) -> None:
        """Returns count and asOf timestamp."""
        records = [_make_record("did:plc:a", f"r{i}") for i in range(7)]
        stub = _make_indexer(records)
        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.countByCollection",
                json={"collection": "com.etzhayyim.test.record"},
            )
        assert resp.status == 200
        body = await resp.json()
        assert body["count"] == 7
        assert body["asOf"].endswith("Z")

    async def test_count_missing_collection_400(self) -> None:
        """Returns 400 when collection is missing."""
        resp = await self.client.post(
            "/xrpc/com.etzhayyim.mstProjector.countByCollection",
            json={},
        )
        assert resp.status == 400

    async def test_count_by_collection_uses_native_count(self) -> None:
        """Uses indexer.count_rows() (native LanceDB count) instead of full scan.

        Verifies M4 optimisation: count_rows is called and its return value
        is reflected in the response without any query() scan.
        Per ADR-2605215500 §4 Deliverable E.
        """
        stub = MagicMock()
        # count_rows returns 42 directly — no records needed
        stub.count_rows = AsyncMock(return_value=42)
        # query should NOT be called; attach a sentinel so we can assert
        stub.query = AsyncMock(side_effect=AssertionError("query() must not be called"))

        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.countByCollection",
                json={"collection": "app.bsky.feed.post"},
            )

        assert resp.status == 200
        body = await resp.json()
        assert body["count"] == 42
        assert body["asOf"].endswith("Z")
        stub.count_rows.assert_awaited_once_with("app.bsky.feed.post")

    async def test_count_by_collection_fallback_on_count_rows_error(self) -> None:
        """Falls back to query()-based scan when count_rows() raises.

        Ensures backward compatibility with environments where count_rows
        is unavailable or raises an unexpected exception.
        """
        records = [_make_record("did:plc:a", f"r{i}") for i in range(5)]
        stub = MagicMock()
        stub.count_rows = AsyncMock(side_effect=RuntimeError("not supported"))

        async def _query(collection: str, filter_sql: str | None = None, limit: int = 100) -> list:
            return records[:limit]

        stub.query = _query

        with patch("mst_projector.query_api.get_indexer", return_value=stub):
            resp = await self.client.post(
                "/xrpc/com.etzhayyim.mstProjector.countByCollection",
                json={"collection": "app.bsky.feed.post"},
            )

        assert resp.status == 200
        body = await resp.json()
        assert body["count"] == 5
        assert body["asOf"].endswith("Z")
