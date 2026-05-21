"""Smoke tests for etzhayyim-sdk Python binding.

Tests:
  1. Package imports cleanly (no missing deps).
  2. Types (lexicon-matched dataclasses) construct correctly.
  3. pds module: real impl via httpx.MockTransport (put_record, get_record,
     list_records, delete_record, error handling).
  4. mst module: real impl wrapping pds (query, get_by_uri).
  5. ipfs / l2: stubs raise NotImplementedError (signatures complete).
  6. Error type hierarchy: all extend PdsError.
  7. RequestCoalescer batches concurrent calls into a single fn() invocation.
  8. RequestCoalescer propagates exceptions to all waiters.
  9. RequestCoalescer flush() drains in-flight tasks.

ADR references:
  ADR-2605215200 — shinka lexicons (ShinkaHeartbeatRecord, etc.)
  ADR-2605215300 — yoro lexicons (TranslationLinkRecord, etc.)
  ADR-2605215300 §Open risks — Zeebe task timeout: coalescer is the M2 unblocker
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))


# ── Import smoke ──────────────────────────────────────────────────────────────


def test_package_imports():
    """Package and all sub-modules import without error."""
    import etzhayyim_sdk  # noqa: F401
    from etzhayyim_sdk import coalesce, ipfs, l2, mst, pds  # noqa: F401
    assert etzhayyim_sdk.__version__ == "0.1.0"


# ── Types construction ────────────────────────────────────────────────────────


def test_shinka_heartbeat_record_constructs():
    from etzhayyim_sdk.types import ShinkaHeartbeatRecord

    rec = ShinkaHeartbeatRecord(
        node_name="levi",
        cycle=42,
        recorded_at="2026-05-21T00:00:00Z",
        cells_observed=3,
        cells_validated=1,
        cells_emitted=1,
    )
    assert rec.node_name == "levi"
    assert rec.cycle == 42
    assert rec.errors == []
    mst_rec = rec.to_mst_record()
    assert mst_rec["$type"] == "app.etzhayyim.shinka.shinkaHeartbeat"
    assert mst_rec["nodeName"] == "levi"
    assert mst_rec["cycle"] == 42
    assert "errors" not in mst_rec  # optional, only present when non-empty


def test_shinka_heartbeat_record_with_errors():
    from etzhayyim_sdk.types import ShinkaHeartbeatRecord

    rec = ShinkaHeartbeatRecord(
        node_name="levi",
        cycle=1,
        recorded_at="2026-05-21T00:00:00Z",
        cells_observed=0,
        cells_validated=0,
        cells_emitted=0,
        errors=["KarmaHegemonObservationCell: timeout after 3000ms"],
    )
    mst_rec = rec.to_mst_record()
    assert "errors" in mst_rec
    assert len(mst_rec["errors"]) == 1


def test_kyumei_signal_record_constructs():
    from etzhayyim_sdk.types import KyumeiSignalRecord

    rec = KyumeiSignalRecord(
        adherent_did="did:web:etzhayyim.com",
        signal_kind="ritual",
        weight=750,
        recorded_at="2026-05-21T00:00:00Z",
        evidence_cid="bafybeig5abc123",
    )
    assert rec.weight == 750
    mst_rec = rec.to_mst_record()
    assert mst_rec["$type"] == "app.etzhayyim.shinka.kyumeiSignal"
    assert mst_rec["adherentDid"] == "did:web:etzhayyim.com"
    assert mst_rec["signalKind"] == "ritual"
    assert "notes" not in mst_rec


def test_translation_link_record_constructs():
    from etzhayyim_sdk.types import TranslationLinkRecord

    rec = TranslationLinkRecord(
        source_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/orig-001",
        source_lang="ja",
        target_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/en-001",
        target_lang="en",
        translated_at="2026-05-21T00:00:00Z",
        quality_score=850,
        translator_did="did:web:yoro.etzhayyim.com",
        model="gemma-4-e4b-it",
    )
    assert rec.quality_score == 850
    mst_rec = rec.to_mst_record()
    assert mst_rec["$type"] == "app.etzhayyim.translationLink"
    assert mst_rec["sourceLang"] == "ja"
    assert mst_rec["targetLang"] == "en"
    # lexicon field name is targetUri (not translatedUri)
    assert mst_rec["targetUri"] == "at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/en-001"
    assert mst_rec["model"] == "gemma-4-e4b-it"


def test_bpmn_activity_event_record_constructs():
    from etzhayyim_sdk.types import BpmnActivityEventRecord

    rec = BpmnActivityEventRecord(
        case_id="case-001",
        task_type="yoro.actorQuality.inspect",
        lifecycle="started",
        actor_did="did:plc:test",
        event_type="yoro.actorQuality.inspect.started",
        payload_json='{"caseId":"case-001"}',
        occurred_at="2026-05-21T00:00:00Z",
    )
    mst_rec = rec.to_mst_record()
    assert mst_rec["$type"] == "app.etzhayyim.bpmnActivityEvent"
    assert mst_rec["lifecycle"] == "started"


# ── Error type hierarchy ─────────────────────────────────────────────────────


def test_error_hierarchy():
    """All PDS errors extend PdsError."""
    from etzhayyim_sdk.errors import (
        PdsAuthError,
        PdsError,
        PdsNetworkError,
        PdsNotFoundError,
        PdsServerError,
    )

    assert issubclass(PdsAuthError, PdsError)
    assert issubclass(PdsNotFoundError, PdsError)
    assert issubclass(PdsServerError, PdsError)
    assert issubclass(PdsNetworkError, PdsError)


def test_pds_server_error_attrs():
    from etzhayyim_sdk.errors import PdsServerError

    err = PdsServerError(503, "Service Unavailable")
    assert err.status_code == 503
    assert "503" in str(err)


# ── pds — real impl via MockTransport ────────────────────────────────────────


def _make_pds_transport(handler):
    """Return a MockTransport + inject it into the pds module singleton."""
    from etzhayyim_sdk import pds as pds_module

    transport = httpx.MockTransport(handler)
    pds_module._inject_transport(transport)
    return transport


@pytest.mark.asyncio
async def test_pds_put_record_success():
    """put_record happy path returns AT URI."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        assert "com.atproto.repo.putRecord" in request.url.path
        body = json.loads(request.content)
        assert body["collection"] == "app.bsky.feed.post"
        assert body["repo"] == "did:web:etzhayyim.com"
        return httpx.Response(
            200,
            json={"uri": "at://did:web:etzhayyim.com/app.bsky.feed.post/self", "cid": "bafy123"},
        )

    _make_pds_transport(handler)
    uri = await pds.put_record("app.bsky.feed.post", {"$type": "app.bsky.feed.post"})
    assert uri == "at://did:web:etzhayyim.com/app.bsky.feed.post/self"


@pytest.mark.asyncio
async def test_pds_put_record_with_rkey():
    """put_record passes custom rkey in request body."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["rkey"] == "my-key"
        return httpx.Response(
            200,
            json={"uri": "at://did:web:etzhayyim.com/app.bsky.feed.post/my-key", "cid": "bafy456"},
        )

    _make_pds_transport(handler)
    uri = await pds.put_record("app.bsky.feed.post", {}, rkey="my-key")
    assert "my-key" in uri


@pytest.mark.asyncio
async def test_pds_put_record_401_raises_auth_error():
    """put_record 401 → PdsAuthError."""
    from etzhayyim_sdk import pds
    from etzhayyim_sdk.errors import PdsAuthError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "AuthRequired"})

    _make_pds_transport(handler)
    with pytest.raises(PdsAuthError):
        await pds.put_record("app.bsky.feed.post", {})


@pytest.mark.asyncio
async def test_pds_put_record_403_raises_auth_error():
    """put_record 403 → PdsAuthError."""
    from etzhayyim_sdk import pds
    from etzhayyim_sdk.errors import PdsAuthError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "Forbidden"})

    _make_pds_transport(handler)
    with pytest.raises(PdsAuthError):
        await pds.put_record("app.bsky.feed.post", {})


@pytest.mark.asyncio
async def test_pds_put_record_500_raises_server_error():
    """put_record 500 → PdsServerError with body."""
    from etzhayyim_sdk import pds
    from etzhayyim_sdk.errors import PdsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    _make_pds_transport(handler)
    with pytest.raises(PdsServerError) as exc_info:
        await pds.put_record("app.bsky.feed.post", {})
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_pds_get_record_happy_path():
    """get_record returns the record dict from PDS."""
    from etzhayyim_sdk import pds

    expected_value = {"$type": "app.bsky.feed.post", "text": "Hello"}

    def handler(request: httpx.Request) -> httpx.Response:
        assert "com.atproto.repo.getRecord" in request.url.path
        assert request.url.params["repo"] == "did:web:etzhayyim.com"
        assert request.url.params["collection"] == "app.bsky.feed.post"
        assert request.url.params["rkey"] == "abc123"
        return httpx.Response(
            200,
            json={
                "uri": "at://did:web:etzhayyim.com/app.bsky.feed.post/abc123",
                "cid": "bafy789",
                "value": expected_value,
            },
        )

    _make_pds_transport(handler)
    record = await pds.get_record("at://did:web:etzhayyim.com/app.bsky.feed.post/abc123")
    assert record["value"] == expected_value


@pytest.mark.asyncio
async def test_pds_get_record_404_raises_not_found():
    """get_record 404 → PdsNotFoundError."""
    from etzhayyim_sdk import pds
    from etzhayyim_sdk.errors import PdsNotFoundError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "RecordNotFound"})

    _make_pds_transport(handler)
    with pytest.raises(PdsNotFoundError):
        await pds.get_record("at://did:web:etzhayyim.com/app.bsky.feed.post/missing")


@pytest.mark.asyncio
async def test_pds_list_records_with_cursor():
    """list_records returns records + cursor from PDS."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        assert "com.atproto.repo.listRecords" in request.url.path
        assert request.url.params["repo"] == "did:web:etzhayyim.com"
        assert request.url.params["collection"] == "app.bsky.feed.post"
        return httpx.Response(
            200,
            json={
                "records": [
                    {"uri": "at://…/post/1", "cid": "bafy001", "value": {}},
                    {"uri": "at://…/post/2", "cid": "bafy002", "value": {}},
                ],
                "cursor": "next-page-token",
            },
        )

    _make_pds_transport(handler)
    result = await pds.list_records("did:web:etzhayyim.com", "app.bsky.feed.post")
    assert len(result["records"]) == 2
    assert result["cursor"] == "next-page-token"


@pytest.mark.asyncio
async def test_pds_list_records_no_cursor():
    """list_records returns None cursor when PDS omits it."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"records": []})

    _make_pds_transport(handler)
    result = await pds.list_records("did:web:etzhayyim.com", "app.bsky.feed.post")
    assert result["records"] == []
    assert result["cursor"] is None


@pytest.mark.asyncio
async def test_pds_delete_record_happy_path():
    """delete_record calls deleteRecord XRPC and returns None."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        assert "com.atproto.repo.deleteRecord" in request.url.path
        body = json.loads(request.content)
        assert body["rkey"] == "abc123"
        return httpx.Response(200, json={})

    _make_pds_transport(handler)
    result = await pds.delete_record("at://did:web:etzhayyim.com/app.bsky.feed.post/abc123")
    assert result is None


@pytest.mark.asyncio
async def test_pds_dispatch_alias():
    """dispatch() is an alias for put_record and returns the same AT URI."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"uri": "at://did:web:etzhayyim.com/app.bsky.feed.post/self", "cid": "bafy999"},
        )

    _make_pds_transport(handler)
    uri = await pds.dispatch("app.bsky.feed.post", {"$type": "app.bsky.feed.post"})
    assert uri.startswith("at://")


# ── mst — real impl wrapping pds ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mst_query_returns_records():
    """mst.query fetches records via pds.list_records."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        assert "listRecords" in request.url.path
        return httpx.Response(
            200,
            json={
                "records": [
                    {"uri": "at://…/kyumeiSignal/r1", "cid": "c1", "value": {"adherentDid": "did:web:etzhayyim.com"}},
                    {"uri": "at://…/kyumeiSignal/r2", "cid": "c2", "value": {"adherentDid": "did:web:other.com"}},
                ]
            },
        )

    _make_pds_transport(handler)

    from etzhayyim_sdk import mst

    records = await mst.query("app.etzhayyim.shinka.kyumeiSignal")
    assert len(records) == 2


@pytest.mark.asyncio
async def test_mst_query_client_side_filter():
    """mst.query applies client-side filter to records."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "records": [
                    {"uri": "at://…/r1", "cid": "c1", "value": {"adherentDid": "did:web:etzhayyim.com", "kind": "ritual"}},
                    {"uri": "at://…/r2", "cid": "c2", "value": {"adherentDid": "did:web:other.com", "kind": "ritual"}},
                ]
            },
        )

    _make_pds_transport(handler)

    from etzhayyim_sdk import mst

    records = await mst.query(
        "app.etzhayyim.shinka.kyumeiSignal",
        filter={"adherentDid": "did:web:etzhayyim.com"},
    )
    assert len(records) == 1
    assert records[0]["value"]["adherentDid"] == "did:web:etzhayyim.com"


@pytest.mark.asyncio
async def test_mst_get_by_uri_happy_path():
    """mst.get_by_uri returns a single record dict."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"uri": "at://did:web:etzhayyim.com/app.bsky.feed.post/abc", "cid": "c1", "value": {"text": "hi"}},
        )

    _make_pds_transport(handler)

    from etzhayyim_sdk import mst

    record = await mst.get_by_uri("at://did:web:etzhayyim.com/app.bsky.feed.post/abc")
    assert record["value"]["text"] == "hi"


@pytest.mark.asyncio
async def test_mst_council_objections_filter_by_claim_id():
    """mst.council_objections filters by claim_id, returns matching objections only."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        # Return 3 records: 2 for claim-123, 1 for claim-456
        return httpx.Response(
            200,
            json={
                "records": [
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/r1",
                        "cid": "c1",
                        "value": {
                            "claimId": "claim-123",
                            "objectorDid": "did:web:objector1.com",
                            "filedAt": "2026-05-21T12:00:00Z",
                            "reason": "insufficient-witness-quality",
                            "evidenceCid": None,
                        },
                    },
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/r2",
                        "cid": "c2",
                        "value": {
                            "claimId": "claim-456",  # Different claim
                            "objectorDid": "did:web:objector2.com",
                            "filedAt": "2026-05-21T10:00:00Z",
                            "reason": "procedural-error",
                            "evidenceCid": None,
                        },
                    },
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/r3",
                        "cid": "c3",
                        "value": {
                            "claimId": "claim-123",  # Matches first
                            "objectorDid": "did:web:objector3.com",
                            "filedAt": "2026-05-21T11:00:00Z",
                            "reason": "charter-non-compliance-undetected",
                            "evidenceCid": "bafybeig5abc123",
                        },
                    },
                ]
            },
        )

    _make_pds_transport(handler)

    from etzhayyim_sdk import mst

    objections = await mst.council_objections("claim-123")
    # Should return 2 objections (r1 and r3, not r2 which is for claim-456)
    assert len(objections) == 2
    assert objections[0]["objector_did"] == "did:web:objector1.com"
    assert objections[1]["objector_did"] == "did:web:objector3.com"
    assert objections[1]["evidence_cid"] == "bafybeig5abc123"


@pytest.mark.asyncio
async def test_mst_council_objections_filter_by_recency():
    """mst.council_objections filters out old objections beyond since_days."""
    from etzhayyim_sdk import pds

    def handler(request: httpx.Request) -> httpx.Response:
        # Return 3 records with varied timestamps: 1 very old, 2 recent
        return httpx.Response(
            200,
            json={
                "records": [
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/old",
                        "cid": "cold",
                        "value": {
                            "claimId": "claim-123",
                            "objectorDid": "did:web:objector-old.com",
                            "filedAt": "2026-04-15T00:00:00Z",  # 36 days ago
                            "reason": "procedural-error",
                            "evidenceCid": None,
                        },
                    },
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/recent1",
                        "cid": "crecent1",
                        "value": {
                            "claimId": "claim-123",
                            "objectorDid": "did:web:objector-new1.com",
                            "filedAt": "2026-05-20T10:00:00Z",  # 1 day ago
                            "reason": "insufficient-witness-quality",
                            "evidenceCid": None,
                        },
                    },
                    {
                        "uri": "at://did:web:etzhayyim.com/app.etzhayyim.evolution-objection/recent2",
                        "cid": "crecent2",
                        "value": {
                            "claimId": "claim-123",
                            "objectorDid": "did:web:objector-new2.com",
                            "filedAt": "2026-05-19T15:00:00Z",  # 2 days ago
                            "reason": "conflict-of-interest",
                            "evidenceCid": "bafybeig5xyz789",
                        },
                    },
                ]
            },
        )

    _make_pds_transport(handler)

    from etzhayyim_sdk import mst

    # since_days=30 (default): old objection from 36 days ago should be filtered out
    objections = await mst.council_objections("claim-123", since_days=30)
    assert len(objections) == 2  # Only recent 2, old one filtered
    assert "objector-old.com" not in [o["objector_did"] for o in objections]
    assert objections[0]["objector_did"] == "did:web:objector-new1.com"
    assert objections[1]["objector_did"] == "did:web:objector-new2.com"


# ── ipfs — M4 real impl; detailed tests in tests/test_ipfs.py ────────────────
# (stub tests removed in M4 — ipfs is now a real httpx impl)

# ── l2: real impl (M5) — detailed tests in tests/test_l2.py ─────────────────
# Smoke tests confirm the real impl is wired and raises typed L2 errors
# (not NotImplementedError) when env vars are missing.


@pytest.mark.asyncio
async def test_l2_anchor_raises_contract_error_without_env():
    """l2.anchor() raises L2ContractError when contract address is unset (M5 real impl)."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ContractError

    with pytest.raises(L2ContractError, match="ETZHAYYIM_L2_CONTRACT_ADDRESS"):
        await l2.anchor("bafybeig5abc123")


@pytest.mark.asyncio
async def test_l2_read_anchor_raises_l2_error_with_null_receipt():
    """l2.read_anchor() raises L2Error (not-found) with null receipt (M5 real impl)."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2Error

    def null_receipt_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": None},
        )

    l2._inject_transport(httpx.MockTransport(null_receipt_handler))
    with pytest.raises(L2Error, match="not found"):
        await l2.read_anchor("0x" + "a" * 64)


@pytest.mark.asyncio
async def test_l2_latest_block_returns_int_with_mock():
    """l2.latest_block() returns int from mock RPC (M5 real impl — no longer a stub)."""
    from etzhayyim_sdk import l2

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": "0xdeadbeef"},
        )

    l2._inject_transport(httpx.MockTransport(handler))
    block = await l2.latest_block()
    assert block == 0xDEADBEEF


@pytest.mark.asyncio
async def test_l2_anchor_cid_raises_contract_error_without_env():
    """l2.anchor_cid() raises L2ContractError when contract address is unset (M5 real impl)."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ContractError

    with pytest.raises(L2ContractError, match="ETZHAYYIM_L2_CONTRACT_ADDRESS"):
        await l2.anchor_cid("bafybeig5abc123")


# ── pds.subscribe: M4 stub ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pds_subscribe_raises_not_implemented():
    from etzhayyim_sdk import pds

    with pytest.raises(NotImplementedError, match="M4"):
        async for _ in pds.subscribe(["app.etzhayyim.shinka.kyumeiSignal"]):
            pass


# ── mst.subscribe: M5 real impl — detailed tests in tests/test_mst_subscribe.py ──


def test_mst_subscribe_is_async_generator():
    """mst.subscribe is an async generator function (not a NotImplementedError stub)."""
    import inspect

    from etzhayyim_sdk import mst

    assert inspect.isasyncgenfunction(mst.subscribe)


# ── RequestCoalescer — real impl ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_coalescer_batches_concurrent_calls():
    """Two concurrent submits for the same key share one fn() invocation."""
    from etzhayyim_sdk.coalesce import RequestCoalescer

    call_count = 0

    async def expensive_fn() -> str:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)  # yield to let other coroutines register
        return "mst-commit-ok"

    coalescer = RequestCoalescer(window_ms=100, max_batch=64)

    # Submit two concurrent calls for the same key
    results = await asyncio.gather(
        coalescer.submit("at://repo/feed.post/rkey1", expensive_fn),
        coalescer.submit("at://repo/feed.post/rkey1", expensive_fn),
    )

    assert results[0] == "mst-commit-ok"
    assert results[1] == "mst-commit-ok"
    # Only one fn() invocation despite two concurrent submits
    assert call_count == 1


@pytest.mark.asyncio
async def test_coalescer_different_keys_call_fn_separately():
    """Different keys each trigger their own fn() invocation."""
    from etzhayyim_sdk.coalesce import RequestCoalescer

    calls: list[str] = []

    async def make_fn(key: str):
        async def fn() -> str:
            calls.append(key)
            return f"ok-{key}"
        return fn

    coalescer = RequestCoalescer(window_ms=100, max_batch=64)

    fn_a = await make_fn("lang-en")
    fn_b = await make_fn("lang-ja")

    results = await asyncio.gather(
        coalescer.submit("source-uri-A", fn_a),
        coalescer.submit("source-uri-B", fn_b),
    )

    assert "ok-lang-en" in results
    assert "ok-lang-ja" in results
    assert len(calls) == 2  # two keys → two invocations


@pytest.mark.asyncio
async def test_coalescer_propagates_exception_to_all_waiters():
    """If fn() raises, all waiters in the batch receive the exception."""
    from etzhayyim_sdk.coalesce import RequestCoalescer

    async def failing_fn() -> str:
        raise ValueError("PDS put_record failed: 503")

    coalescer = RequestCoalescer(window_ms=100, max_batch=64)

    with pytest.raises(ValueError, match="503"):
        await asyncio.gather(
            coalescer.submit("source-uri-X", failing_fn),
            coalescer.submit("source-uri-X", failing_fn),
        )


@pytest.mark.asyncio
async def test_coalescer_flush_drains_in_flight():
    """flush() returns after all in-flight batch windows complete."""
    from etzhayyim_sdk.coalesce import RequestCoalescer

    results: list[str] = []

    async def slow_fn() -> str:
        await asyncio.sleep(0.02)  # 20 ms
        results.append("done")
        return "done"

    coalescer = RequestCoalescer(window_ms=50, max_batch=64)

    # Start a submit (don't await it)
    task = asyncio.create_task(coalescer.submit("key-flush", slow_fn))
    await asyncio.sleep(0)  # let task start

    # flush() should wait for it
    await coalescer.flush()
    assert results == ["done"]
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):
        pass


@pytest.mark.asyncio
async def test_coalescer_max_batch_closes_window_early():
    """When max_batch submissions arrive, the window closes immediately."""
    from etzhayyim_sdk.coalesce import RequestCoalescer

    call_count = 0

    async def fn() -> int:
        nonlocal call_count
        call_count += 1
        return 42

    # max_batch=2: after 2 submits the window closes without waiting
    coalescer = RequestCoalescer(window_ms=5000, max_batch=2)

    results = await asyncio.gather(
        coalescer.submit("key-max", fn),
        coalescer.submit("key-max", fn),
    )

    assert all(r == 42 for r in results)
    assert call_count == 1


# ── Registry & flush_all (M3) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_coalescer_registers_in_global_registry():
    """RequestCoalescer instances auto-register on __init__."""
    from etzhayyim_sdk import coalesce

    # Clear any previous instances
    coalesce._active_coalescers.clear()

    c1 = coalesce.RequestCoalescer()
    c2 = coalesce.RequestCoalescer()

    assert c1 in coalesce._active_coalescers
    assert c2 in coalesce._active_coalescers
    assert len(coalesce._active_coalescers) == 2

    # Clean up
    coalesce._active_coalescers.clear()


@pytest.mark.asyncio
async def test_coalescer_context_manager_deregisters():
    """Async context manager __aexit__ deregisters the coalescer."""
    from etzhayyim_sdk import coalesce

    coalesce._active_coalescers.clear()

    async with coalesce.RequestCoalescer() as c:
        assert c in coalesce._active_coalescers

    # Should be removed after exit
    assert c not in coalesce._active_coalescers
    assert len(coalesce._active_coalescers) == 0


@pytest.mark.asyncio
async def test_coalescer_close_deregisters():
    """close() method deregisters the coalescer."""
    from etzhayyim_sdk import coalesce

    coalesce._active_coalescers.clear()

    c = coalesce.RequestCoalescer()
    assert c in coalesce._active_coalescers

    c.close()
    assert c not in coalesce._active_coalescers

    # Calling close() again is safe (idempotent)
    c.close()
    assert c not in coalesce._active_coalescers


@pytest.mark.asyncio
async def test_flush_all_drains_multiple_coalescers():
    """flush_all() drains all registered coalescers."""
    from etzhayyim_sdk import coalesce

    coalesce._active_coalescers.clear()

    results: list[str] = []

    async def slow_fn() -> str:
        await asyncio.sleep(0.01)
        results.append("done")
        return "done"

    c1 = coalesce.RequestCoalescer(window_ms=100)
    c2 = coalesce.RequestCoalescer(window_ms=100)

    # Start submissions but don't await
    task1 = asyncio.create_task(c1.submit("key1", slow_fn))
    task2 = asyncio.create_task(c2.submit("key2", slow_fn))

    await asyncio.sleep(0)  # let tasks start

    # flush_all should drain both
    count = await coalesce.flush_all(timeout_seconds=2.0)
    assert count == 2

    # Wait for tasks to complete
    await asyncio.gather(task1, task2, return_exceptions=True)
    assert len(results) == 2

    # Clean up
    coalesce._active_coalescers.clear()


@pytest.mark.asyncio
async def test_flush_all_respects_timeout():
    """flush_all() respects the timeout parameter."""
    from etzhayyim_sdk import coalesce

    coalesce._active_coalescers.clear()

    async def forever_fn() -> str:
        await asyncio.sleep(10)  # longer than timeout
        return "done"

    c = coalesce.RequestCoalescer(window_ms=100)

    # Start submission
    task = asyncio.create_task(c.submit("forever", forever_fn))
    await asyncio.sleep(0)

    # flush_all with short timeout should not raise, just timeout silently
    count = await coalesce.flush_all(timeout_seconds=0.05)
    assert count == 1

    # Clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    coalesce._active_coalescers.clear()


@pytest.mark.asyncio
async def test_flush_all_returns_zero_when_empty():
    """flush_all() returns 0 when no coalescers are registered."""
    from etzhayyim_sdk import coalesce

    coalesce._active_coalescers.clear()

    count = await coalesce.flush_all(timeout_seconds=1.0)
    assert count == 0
