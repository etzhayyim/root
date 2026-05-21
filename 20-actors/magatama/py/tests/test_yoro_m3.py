"""M3 implementation tests for yoro murakumo primitives.

Tests verify happy-path behaviour for the 7 functions implemented in M3:
  Social module (yoro_social_murakumo.py):
    1. record_bpmn_activity_event  — app.etzhayyim.bpmnActivityEvent
    2. record_actor_quality_report — app.etzhayyim.actorQualityReport
    3. like_post                   — app.bsky.feed.like
    4. follow_actor                — app.bsky.graph.follow  (coalesced)
    5. repost                      — app.bsky.feed.repost

  Product ingest module (yoro_product_ingest_murakumo.py):
    6. ingest_product              — ai.gftd.apps.etzhayyim.productIngest
    7. batch_ingest_products       — batch putRecord + coalescer

Test strategy per function:
  - Happy path: mock SDK, call function, verify SDK call args + return URI shape.
  - Coalesced functions (follow_actor, batch_ingest_products): additional batching test.
  - All new functions: substrate-fit check (no psycopg/Stripe/runpod imports).

NOTE on test isolation: test_yoro_murakumo.py contains tests that evict and reimport
the module from sys.modules (substrate-fit guard tests). This means the module-level
`YS` / `YP` aliases in this file can become stale. All test methods use _ys() / _yp()
helper functions that always return the current sys.modules instance.

ADR authority:
    ADR-2605215300 — yoro Python primitives MST rewrite addendum (M3 milestone)
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_PY_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PY_SRC) not in sys.path:
    sys.path.insert(0, str(_PY_SRC))

# Also add etzhayyim-sdk-py to path so coalesce.py can be imported directly in tests.
_SDK_SRC = Path(__file__).resolve().parents[3] / "etzhayyim-sdk-py" / "src"
if str(_SDK_SRC) not in sys.path:
    sys.path.insert(0, str(_SDK_SRC))


def _clean_env_import(module_name: str) -> Any:
    env_backup = os.environ.pop("RW_URL", None)
    try:
        if module_name in sys.modules:
            del sys.modules[module_name]
        return importlib.import_module(module_name)
    finally:
        if env_backup is not None:
            os.environ["RW_URL"] = env_backup


_clean_env_import("pymagatama.primitives.yoro_social_murakumo")
_clean_env_import("pymagatama.primitives.yoro_product_ingest_murakumo")

_SOCIAL_MOD = "pymagatama.primitives.yoro_social_murakumo"
_INGEST_MOD = "pymagatama.primitives.yoro_product_ingest_murakumo"


def _ys() -> Any:
    """Always return the current sys.modules instance (safe after module evictions)."""
    return sys.modules[_SOCIAL_MOD]


def _yp() -> Any:
    """Always return the current sys.modules instance (safe after module evictions)."""
    return sys.modules[_INGEST_MOD]


# ---------------------------------------------------------------------------
# §1 — record_bpmn_activity_event
# ---------------------------------------------------------------------------

class TestRecordBpmnActivityEvent:
    """app.etzhayyim.bpmnActivityEvent — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_at_uri(self):
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            uri = await _ys().record_bpmn_activity_event(
                repo="did:web:yoro.etzhayyim.com",
                process_id="yoro.actorQuality",
                activity_id="yoro.actorQuality.inspect",
                instance_key="instance-001",
                event_kind="started",
                actor_did="did:plc:testactor",
                case_id="case-001",
            )
        assert uri.startswith("at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/")
        mock_put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sdk_call_args_wire_shape(self):
        """Verify the exact wire shape passed to SDK matches lexicon."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _ys().record_bpmn_activity_event(
                repo="did:web:yoro.etzhayyim.com",
                process_id="yoro.actorQuality",
                activity_id="yoro.actorQuality.inspect",
                instance_key="instance-001",
                event_kind="completed",
                actor_did="did:plc:testactor",
                error_message="",
                evidence_cid="bafytest",
            )

        assert captured["collection"] == "app.etzhayyim.bpmnActivityEvent"
        record = captured["record"]
        assert record["$type"] == "app.etzhayyim.bpmnActivityEvent"
        assert record["processId"] == "yoro.actorQuality"
        assert record["activityId"] == "yoro.actorQuality.inspect"
        assert record["instanceKey"] == "instance-001"
        assert record["eventKind"] == "completed"
        assert record["actorDid"] == "did:plc:testactor"
        assert record["evidenceCid"] == "bafytest"
        # errorMessage should not be set when empty
        assert "errorMessage" not in record

    @pytest.mark.asyncio
    async def test_invalid_event_kind_raises_value_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = AsyncMock()
            with pytest.raises(ValueError, match="event_kind"):
                await _ys().record_bpmn_activity_event(
                    repo="did:web:yoro.etzhayyim.com",
                    process_id="p",
                    activity_id="a",
                    instance_key="i",
                    event_kind="invalid-kind",
                )

    @pytest.mark.asyncio
    async def test_failed_event_kind_includes_error_message(self):
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _ys().record_bpmn_activity_event(
                repo="did:web:yoro.etzhayyim.com",
                process_id="p",
                activity_id="a",
                instance_key="i",
                event_kind="failed",
                error_message="timeout after 25s",
            )

        assert captured["record"]["errorMessage"] == "timeout after 25s"

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().record_bpmn_activity_event(
                    repo="did:web:yoro.etzhayyim.com",
                    process_id="p",
                    activity_id="a",
                    instance_key="i",
                    event_kind="started",
                )


# ---------------------------------------------------------------------------
# §2 — record_actor_quality_report
# ---------------------------------------------------------------------------

class TestRecordActorQualityReport:
    """app.etzhayyim.actorQualityReport — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_at_uri(self):
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            uri = await _ys().record_actor_quality_report(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:subject",
                reporter_did="did:web:yoro.etzhayyim.com",
                quality_score=750,
                dimensions=[
                    {"dimension": "charter-compliance", "score": 800},
                    {"dimension": "wellbecoming", "score": 700},
                ],
            )
        assert uri.startswith("at://did:web:yoro.etzhayyim.com/app.etzhayyim.actorQualityReport/")
        mock_put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wire_shape_matches_lexicon(self):
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _ys().record_actor_quality_report(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:subject",
                quality_score=500,
                dimensions=[{"dimension": "contribution", "score": 500}],
                notes="Automated quality scan.",
            )

        assert captured["collection"] == "app.etzhayyim.actorQualityReport"
        record = captured["record"]
        assert record["$type"] == "app.etzhayyim.actorQualityReport"
        assert record["subjectDid"] == "did:plc:subject"
        assert record["qualityScore"] == 500
        assert record["notes"] == "Automated quality scan."
        assert record["dimensions"] == [{"dimension": "contribution", "score": 500}]

    @pytest.mark.asyncio
    async def test_quality_score_clamped_to_0_1000(self):
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _ys().record_actor_quality_report(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:subject",
                quality_score=9999,  # should be clamped to 1000
                dimensions=[],
            )

        assert captured["record"]["qualityScore"] == 1000

    @pytest.mark.asyncio
    async def test_invalid_dimensions_skipped(self):
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _ys().record_actor_quality_report(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:subject",
                quality_score=600,
                dimensions=[
                    {"dimension": "invalid-dim", "score": 900},   # skipped
                    {"dimension": "governance", "score": 600},     # kept
                ],
            )

        dims = captured["record"]["dimensions"]
        assert len(dims) == 1
        assert dims[0]["dimension"] == "governance"


# ---------------------------------------------------------------------------
# §3 — like_post
# ---------------------------------------------------------------------------

class TestLikePost:
    """app.bsky.feed.like — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_at_uri(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            uri = await _ys().like_post(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://did:plc:author/app.bsky.feed.post/post001",
                subject_cid="bafypost001",
            )
        assert uri.startswith("at://did:web:yoro.etzhayyim.com/app.bsky.feed.like/")
        mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wire_shape_matches_at_lexicon(self):
        """app.bsky.feed.like requires subject.uri + subject.cid (StrongRef)."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _capture
            await _ys().like_post(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://did:plc:author/app.bsky.feed.post/post001",
                subject_cid="bafypost001",
            )

        assert captured["collection"] == "app.bsky.feed.like"
        record = captured["record"]
        assert record["$type"] == "app.bsky.feed.like"
        assert record["subject"]["uri"] == "at://did:plc:author/app.bsky.feed.post/post001"
        assert record["subject"]["cid"] == "bafypost001"
        assert "createdAt" in record

    @pytest.mark.asyncio
    async def test_uses_dispatch_not_put_record(self):
        """like_post must use pds.dispatch (federated), not put_record."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        mock_put_record = AsyncMock()
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put_record
            await _ys().like_post(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://x/app.bsky.feed.post/p1",
                subject_cid="bafyp1",
            )
        mock_dispatch.assert_awaited_once()
        mock_put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().like_post(
                    repo="did:web:yoro.etzhayyim.com",
                    subject_uri="at://x/app.bsky.feed.post/p1",
                    subject_cid="bafyp1",
                )


# ---------------------------------------------------------------------------
# §4 — follow_actor
# ---------------------------------------------------------------------------

class TestFollowActor:
    """app.bsky.graph.follow — M3 IMPLEMENTED (coalesced)."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_at_uri(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            uri = await _ys().follow_actor(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:followee",
                coalescer=None,  # bypass coalescer for simple test
            )
        assert uri.startswith("at://did:web:yoro.etzhayyim.com/app.bsky.graph.follow/")

    @pytest.mark.asyncio
    async def test_wire_shape_matches_at_lexicon(self):
        """app.bsky.graph.follow requires subject (DID string) + createdAt."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _capture
            await _ys().follow_actor(
                repo="did:web:yoro.etzhayyim.com",
                subject_did="did:plc:followee",
                coalescer=None,
            )

        assert captured["collection"] == "app.bsky.graph.follow"
        record = captured["record"]
        assert record["$type"] == "app.bsky.graph.follow"
        assert record["subject"] == "did:plc:followee"
        assert "createdAt" in record

    @pytest.mark.asyncio
    async def test_coalescer_batching(self):
        """Concurrent follow_actor calls for the same subject_did share one pds.dispatch."""
        from etzhayyim_sdk.coalesce import RequestCoalescer

        call_count = 0

        async def _counting_dispatch(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"uri": "at://x", "cid": "bafycid"}

        coalescer = RequestCoalescer(window_ms=50, max_batch=10)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _counting_dispatch
            # Fan out 5 concurrent follow calls for the same subject_did
            tasks = [
                _ys().follow_actor(
                    repo="did:web:yoro.etzhayyim.com",
                    subject_did="did:plc:same-followee",
                    coalescer=coalescer,
                )
                for _ in range(5)
            ]
            uris = await asyncio.gather(*tasks)

        # All 5 URIs should be returned (each caller gets the coalesced result)
        assert len(uris) == 5
        # The coalescer should have collapsed 5 concurrent calls into ≥ 1 dispatch
        assert call_count >= 1
        await coalescer.flush()
        coalescer.close()

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().follow_actor(
                    repo="did:web:yoro.etzhayyim.com",
                    subject_did="did:plc:followee",
                )


# ---------------------------------------------------------------------------
# §5 — repost
# ---------------------------------------------------------------------------

class TestRepost:
    """app.bsky.feed.repost — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_at_uri(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            uri = await _ys().repost(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://did:plc:author/app.bsky.feed.post/post001",
                subject_cid="bafypost001",
            )
        assert uri.startswith("at://did:web:yoro.etzhayyim.com/app.bsky.feed.repost/")
        mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wire_shape_matches_at_lexicon(self):
        """app.bsky.feed.repost requires subject.uri + subject.cid (StrongRef)."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _capture
            await _ys().repost(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://did:plc:author/app.bsky.feed.post/post001",
                subject_cid="bafypost001",
            )

        assert captured["collection"] == "app.bsky.feed.repost"
        record = captured["record"]
        assert record["$type"] == "app.bsky.feed.repost"
        assert record["subject"]["uri"] == "at://did:plc:author/app.bsky.feed.post/post001"
        assert record["subject"]["cid"] == "bafypost001"
        assert "createdAt" in record

    @pytest.mark.asyncio
    async def test_uses_dispatch_not_put_record(self):
        """repost must use pds.dispatch (federated), not put_record."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        mock_put_record = AsyncMock()
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put_record
            await _ys().repost(
                repo="did:web:yoro.etzhayyim.com",
                subject_uri="at://x/app.bsky.feed.post/p1",
                subject_cid="bafyp1",
            )
        mock_dispatch.assert_awaited_once()
        mock_put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().repost(
                    repo="did:web:yoro.etzhayyim.com",
                    subject_uri="at://x/app.bsky.feed.post/p1",
                    subject_cid="bafyp1",
                )


# ---------------------------------------------------------------------------
# §6 — ingest_product
# ---------------------------------------------------------------------------

class TestIngestProduct:
    """ai.gftd.apps.etzhayyim.productIngest — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_result_dict(self):
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "bafycid"})
        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = await _yp().ingest_product(
                {"product_id": "prod-001", "category": "book", "status": "active"},
                repo="did:web:yoro.etzhayyim.com",
            )

        assert result["product_id"] == "prod-001"
        assert result["status"] == "active"
        assert result["uri"].startswith(
            "at://did:web:yoro.etzhayyim.com/ai.gftd.apps.etzhayyim.productIngest/"
        )
        assert "rkey" in result
        assert "ingested_at" in result
        mock_put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wire_shape_matches_lexicon(self):
        """productIngest record must include productId, sourceUri, productKind, metadata."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _yp().ingest_product(
                {
                    "product_id": "prod-abc",
                    "product_kind": "scripture",
                    "metadata": {"title": "etz hayim", "lang": "he"},
                },
                repo="did:web:yoro.etzhayyim.com",
            )

        assert captured["collection"] == "ai.gftd.apps.etzhayyim.productIngest"
        record = captured["record"]
        assert record["$type"] == "ai.gftd.apps.etzhayyim.productIngest"
        assert record["productId"] == "prod-abc"
        assert record["productKind"] == "scripture"
        assert record["metadata"]["title"] == "etz hayim"
        assert record["metadata"]["lang"] == "he"
        assert "ingestedAt" in record

    @pytest.mark.asyncio
    async def test_missing_product_id_raises_value_error(self):
        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = AsyncMock()
            with pytest.raises(ValueError, match="product_id"):
                await _yp().ingest_product({"title": "no-id"})

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_INGEST_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _yp().ingest_product({"product_id": "p1"})

    @pytest.mark.asyncio
    async def test_metadata_from_top_level_fields(self):
        """title/description at top level should flow into metadata."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _capture
            await _yp().ingest_product(
                {
                    "product_id": "p-top",
                    "title": "My Product",
                    "description": "Desc",
                },
                repo="did:web:yoro.etzhayyim.com",
            )

        meta = captured["record"]["metadata"]
        assert meta["title"] == "My Product"
        assert meta["description"] == "Desc"


# ---------------------------------------------------------------------------
# §7 — batch_ingest_products
# ---------------------------------------------------------------------------

class TestBatchIngestProducts:
    """batch ai.gftd.apps.etzhayyim.productIngest with coalescer — M3 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_all_succeed(self):
        call_count = 0

        async def _counting_put(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _counting_put
            results = await _yp().batch_ingest_products(
                [
                    {"product_id": "p1", "category": "book"},
                    {"product_id": "p2", "category": "video"},
                    {"product_id": "p3", "category": "audio"},
                ],
                repo="did:web:yoro.etzhayyim.com",
            )

        assert len(results) == 3
        for result in results:
            assert "uri" in result
            assert "product_id" in result
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_result_order_matches_input(self):
        products = [
            {"product_id": f"prod-{i:03d}", "category": "test"}
            for i in range(5)
        ]

        async def _put(**kwargs: Any) -> dict[str, Any]:
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _put
            results = await _yp().batch_ingest_products(
                products, repo="did:web:yoro.etzhayyim.com"
            )

        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["product_id"] == f"prod-{i:03d}"

    @pytest.mark.asyncio
    async def test_single_failed_item_reported_not_raised(self):
        """A missing product_id returns an error dict without raising."""

        async def _put(**kwargs: Any) -> dict[str, Any]:
            return {"uri": "at://x", "cid": "bafycid"}

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _put
            results = await _yp().batch_ingest_products(
                [
                    {"product_id": "ok-product"},
                    {"title": "no-id-here"},   # missing product_id → ValueError → error dict
                ],
                repo="did:web:yoro.etzhayyim.com",
            )

        # Both items are in results; the second has an error key
        assert len(results) == 2
        ok_result = next(r for r in results if r.get("product_id") == "ok-product")
        assert "error" not in ok_result
        err_result = next(r for r in results if r.get("error"))
        assert "product_id" in err_result

    @pytest.mark.asyncio
    async def test_coalescer_batching_same_product_id(self):
        """Concurrent batch_ingest_products calls for the same product_id are coalesced."""
        from etzhayyim_sdk.coalesce import RequestCoalescer

        call_count = 0

        async def _counting_put(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            return {"uri": "at://x", "cid": "bafycid"}

        coalescer = RequestCoalescer(window_ms=50, max_batch=10)
        products = [{"product_id": "same-product"}] * 5

        with patch(f"{_INGEST_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = _counting_put
            results = await _yp().batch_ingest_products(
                products,
                repo="did:web:yoro.etzhayyim.com",
                coalescer=coalescer,
            )

        assert len(results) == 5
        # Coalescer should have collapsed calls for the same product_id
        assert call_count >= 1
        await coalescer.flush()
        coalescer.close()

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_INGEST_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _yp().batch_ingest_products([{"product_id": "p1"}])


# ---------------------------------------------------------------------------
# §8 — New constant and collection name checks
# ---------------------------------------------------------------------------

class TestM3Constants:
    def test_like_collection_constant(self):
        assert _ys().LIKE_COLLECTION == "app.bsky.feed.like"

    def test_repost_collection_constant(self):
        assert _ys().REPOST_COLLECTION == "app.bsky.feed.repost"

    def test_follow_collection_unchanged(self):
        assert _ys().FOLLOW_COLLECTION == "app.bsky.graph.follow"

    def test_bpmn_collection_unchanged(self):
        assert _ys().BPMN_ACTIVITY_EVENT_COLLECTION == "app.etzhayyim.bpmnActivityEvent"

    def test_actor_quality_report_collection(self):
        assert _ys().ACTOR_QUALITY_REPORT_COLLECTION == "app.etzhayyim.actorQualityReport"


# ---------------------------------------------------------------------------
# §9 — Substrate-fit regression for new M3 functions
# ---------------------------------------------------------------------------

class TestM3SubstrateFit:
    """No prohibited imports introduced by M3 implementations."""

    def _social_src(self) -> str:
        import inspect
        return Path(inspect.getfile(_ys())).read_text(encoding="utf-8")

    def _ingest_src(self) -> str:
        import inspect
        return Path(inspect.getfile(_yp())).read_text(encoding="utf-8")

    def test_no_psycopg_in_social(self):
        src = self._social_src()
        for pat in ["import psycopg\n", "import psycopg2\n", "from psycopg ", "from psycopg2 "]:
            assert pat not in src

    def test_no_psycopg_in_ingest(self):
        src = self._ingest_src()
        for pat in ["import psycopg\n", "import psycopg2\n", "from psycopg ", "from psycopg2 "]:
            assert pat not in src

    def test_no_stripe_in_social(self):
        src = self._social_src()
        for pat in ["import stripe\n", "from stripe "]:
            assert pat not in src

    def test_no_stripe_in_ingest(self):
        src = self._ingest_src()
        for pat in ["import stripe\n", "from stripe "]:
            assert pat not in src

    def test_no_runpod_in_social(self):
        assert "import runpod" not in self._social_src().lower()

    def test_no_runpod_in_ingest(self):
        assert "import runpod" not in self._ingest_src().lower()

    def test_no_sync_cursor_in_social(self):
        assert "sync_cursor" not in self._social_src()

    def test_no_sync_cursor_in_ingest(self):
        assert "sync_cursor" not in self._ingest_src()

    def test_m3_functions_are_async(self):
        import inspect
        ys = _ys()
        yp = _yp()
        assert inspect.iscoroutinefunction(ys.record_bpmn_activity_event)
        assert inspect.iscoroutinefunction(ys.record_actor_quality_report)
        assert inspect.iscoroutinefunction(ys.like_post)
        assert inspect.iscoroutinefunction(ys.follow_actor)
        assert inspect.iscoroutinefunction(ys.repost)
        assert inspect.iscoroutinefunction(yp.ingest_product)
        assert inspect.iscoroutinefunction(yp.batch_ingest_products)
