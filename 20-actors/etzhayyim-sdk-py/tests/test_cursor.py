"""Tests for cursor persistence helper (ADR-2605215200)."""

from __future__ import annotations

import asyncio
import os
from typing import Any
from unittest import mock

import pytest

from etzhayyim_sdk import cursor as cursor_helper


@pytest.mark.asyncio
async def test_get_cursor_returns_none_when_not_set():
    """Test that get_cursor returns None when cursor not persisted."""
    with mock.patch("etzhayyim_sdk.cursor.pds") as pds_mock:
        pds_mock.get_record = mock.AsyncMock(side_effect=Exception("Not found"))

        result = await cursor_helper.get_cursor("test-cursor")

        assert result is None
        pds_mock.get_record.assert_called_once()


@pytest.mark.asyncio
async def test_get_cursor_returns_persisted_seq():
    """Test that get_cursor returns persisted sequence number."""
    with mock.patch("etzhayyim_sdk.cursor.pds") as pds_mock:
        pds_mock.get_record = mock.AsyncMock(
            return_value={
                "value": {
                    "seq": 12345,
                    "cursorId": "test-cursor",
                    "updatedAt": "2026-05-21T12:00:00Z",
                }
            }
        )

        result = await cursor_helper.get_cursor("test-cursor")

        assert result == 12345
        pds_mock.get_record.assert_called_once()


@pytest.mark.asyncio
async def test_put_cursor_writes_record():
    """Test that put_cursor writes cursor record to PDS."""
    with mock.patch("etzhayyim_sdk.cursor.pds") as pds_mock:
        pds_mock.put_record = mock.AsyncMock()

        await cursor_helper.put_cursor("test-cursor", 99999)

        pds_mock.put_record.assert_called_once()
        call_kwargs = pds_mock.put_record.call_args[1]

        assert call_kwargs["collection"] == cursor_helper.CURSOR_COLLECTION
        assert call_kwargs["record"]["cursorId"] == "test-cursor"
        assert call_kwargs["record"]["seq"] == 99999
        assert "updatedAt" in call_kwargs["record"]
        assert call_kwargs["rkey"] == "test-cursor"  # hyphens preserved in rkey


@pytest.mark.asyncio
async def test_put_cursor_updates_cache():
    """Test that put_cursor updates module-level cache."""
    with mock.patch("etzhayyim_sdk.cursor.pds") as pds_mock:
        pds_mock.put_record = mock.AsyncMock()
        cursor_helper._active_cursors.clear()

        await cursor_helper.put_cursor("test-cursor", 42)

        assert cursor_helper._active_cursors["test-cursor"] == 42


def test_safe_rkey():
    """Test that _safe_rkey converts special chars to underscores."""
    assert cursor_helper._safe_rkey("test-cursor") == "test-cursor"
    assert cursor_helper._safe_rkey("test:cursor") == "test_cursor"
    assert cursor_helper._safe_rkey("test/cursor") == "test_cursor"
    assert cursor_helper._safe_rkey("test cursor") == "test_cursor"
    assert cursor_helper._safe_rkey("complex:test/cursor id") == "complex_test_cursor_id"


@pytest.mark.asyncio
async def test_subscribe_with_checkpoint_uses_persisted_cursor():
    """Test that subscribe_with_checkpoint loads persisted cursor."""
    with mock.patch("etzhayyim_sdk.cursor.get_cursor") as get_cursor_mock:
        get_cursor_mock.return_value = 5000
        with mock.patch("etzhayyim_sdk.cursor.mst") as mst_mock:
            async def mock_gen(*args, **kwargs):
                return
                yield  # pragma: no cover

            mst_mock.subscribe = mock_gen

            # Collect from generator
            async for event in cursor_helper.subscribe_with_checkpoint(
                cursor_id="test-cursor",
                collections=["app.bsky.feed.post"],
            ):
                pass

            # Verify get_cursor was called
            get_cursor_mock.assert_called_once_with("test-cursor")


@pytest.mark.asyncio
async def test_subscribe_with_checkpoint_uses_explicit_cursor():
    """Test that explicit since_cursor overrides persisted cursor."""
    with mock.patch("etzhayyim_sdk.cursor.get_cursor") as get_cursor_mock:
        with mock.patch("etzhayyim_sdk.cursor.mst") as mst_mock:
            async def mock_gen(*args, **kwargs):
                return
                yield  # pragma: no cover

            mst_mock.subscribe = mock_gen

            async for event in cursor_helper.subscribe_with_checkpoint(
                cursor_id="test-cursor",
                collections=["app.bsky.feed.post"],
                since_cursor=1000,  # Explicit override
            ):
                pass

            # get_cursor should NOT be called when explicit cursor provided
            get_cursor_mock.assert_not_called()


@pytest.mark.asyncio
async def test_subscribe_with_checkpoint_writes_cursor_every_N_events():
    """Test that cursor is checkpointed every N events."""
    # Create 200 mock events
    mock_events = [{"seq": i, "data": f"event-{i}"} for i in range(1, 201)]

    async def mock_subscribe_gen(*args, **kwargs):
        for event in mock_events:
            yield event

    with mock.patch("etzhayyim_sdk.cursor.mst") as mst_mock:
        mst_mock.subscribe = mock_subscribe_gen

        with mock.patch("etzhayyim_sdk.cursor.put_cursor") as put_cursor_mock:
            with mock.patch("etzhayyim_sdk.cursor.get_cursor", return_value=0):
                event_count = 0
                async for event in cursor_helper.subscribe_with_checkpoint(
                    cursor_id="test-cursor",
                    collections=["app.bsky.feed.post"],
                    checkpoint_every=100,
                    checkpoint_interval_s=999.0,  # High to avoid time-based checkpoint
                ):
                    event_count += 1

                assert event_count == 200

                # Should checkpoint at 100 events and 200 events (2 checkpoints)
                assert put_cursor_mock.call_count == 2

                # Verify checkpoint sequences
                calls = put_cursor_mock.call_args_list
                assert calls[0][0] == ("test-cursor", 100)  # After 100 events
                assert calls[1][0] == ("test-cursor", 200)  # After 200 events


@pytest.mark.asyncio
async def test_subscribe_with_checkpoint_writes_cursor_every_T_seconds():
    """Test that cursor is checkpointed every T seconds."""

    async def mock_subscribe_gen(*args, **kwargs):
        # Generate 10 events with small delays
        for i in range(1, 11):
            await asyncio.sleep(0.05)
            yield {"seq": i, "data": f"event-{i}"}

    with mock.patch("etzhayyim_sdk.cursor.mst") as mst_mock:
        mst_mock.subscribe = mock_subscribe_gen

        with mock.patch("etzhayyim_sdk.cursor.put_cursor") as put_cursor_mock:
            with mock.patch("etzhayyim_sdk.cursor.get_cursor", return_value=0):
                event_count = 0
                async for event in cursor_helper.subscribe_with_checkpoint(
                    cursor_id="test-cursor",
                    collections=["app.bsky.feed.post"],
                    checkpoint_every=9999,  # High to avoid event-based checkpoint
                    checkpoint_interval_s=0.1,  # 100ms interval
                ):
                    event_count += 1

                assert event_count == 10

                # Should checkpoint at least once due to time interval
                # (exact count depends on timing, but should be ≥ 1)
                assert put_cursor_mock.call_count >= 1


@pytest.mark.asyncio
async def test_subscribe_with_checkpoint_skips_events_without_seq():
    """Test that events without seq are not checkpointed."""
    mock_events = [
        {"seq": 1, "data": "event-1"},
        {"data": "event-no-seq"},  # No seq field
        {"seq": 2, "data": "event-2"},
    ]

    async def mock_subscribe_gen(*args, **kwargs):
        for event in mock_events:
            yield event

    with mock.patch("etzhayyim_sdk.cursor.mst") as mst_mock:
        mst_mock.subscribe = mock_subscribe_gen

        with mock.patch("etzhayyim_sdk.cursor.put_cursor") as put_cursor_mock:
            with mock.patch("etzhayyim_sdk.cursor.get_cursor", return_value=0):
                async for event in cursor_helper.subscribe_with_checkpoint(
                    cursor_id="test-cursor",
                    collections=["app.bsky.feed.post"],
                    checkpoint_every=1,
                ):
                    pass

                # Should only checkpoint events with seq
                # Event 1 and Event 2 have seq; event-no-seq does not
                calls = put_cursor_mock.call_args_list
                assert len(calls) == 2
                assert calls[0][0][1] == 1
                assert calls[1][0][1] == 2
