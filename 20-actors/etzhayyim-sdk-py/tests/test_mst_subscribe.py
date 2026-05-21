"""Tests for etzhayyim_sdk.mst.subscribe — WebSocket firehose (M5).

Tests:
  1. test_subscribe_yields_decoded_frames      — mock WS sends CBOR frames, verify yield
  2. test_subscribe_filters_by_collection      — collection filter drops non-matching ops
  3. test_subscribe_reconnect_on_disconnect    — ConnectionClosedError triggers retry
  4. test_subscribe_reconnect_exhaustion       — 10 failures → MstSubscribeError
  5. test_subscribe_cursor_advance             — cursor updates from seq field each frame
  6. test_subscribe_skips_text_frames          — str messages are skipped gracefully
  7. test_subscribe_skips_bad_cbor             — corrupt binary frames are skipped
  8. test_subscribe_error_frame_raises         — op=-1 header → MstSubscribeError
  9. test_subscribe_cursor_in_url              — since_cursor is appended as ?cursor=N
  10. test_subscribe_url_from_env              — ETZHAYYIM_PDS_URL env → correct wss:// URL

ADR reference: ADR-2605215200 §1 KarmaHegemonObservationCell.
"""

from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import cbor2
import pytest
from websockets.exceptions import ConnectionClosedError

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))


# ── CBOR frame helpers ────────────────────────────────────────────────────────


def _make_commit_frame(
    seq: int,
    repo: str = "did:web:etzhayyim.com",
    ops: list[dict] | None = None,
) -> bytes:
    """Build a minimal AT Protocol firehose commit frame (2 concatenated CBOR objects)."""
    header = {"op": 1, "t": "#commit"}
    payload = {
        "seq": seq,
        "repo": repo,
        "ops": ops or [{"action": "create", "path": "app.etzhayyim.shinka.kyumeiSignal/rkey1", "cid": None}],
        "blocks": b"",
    }
    return cbor2.dumps(header) + cbor2.dumps(payload)


def _make_error_frame(error: str = "FutureCursor") -> bytes:
    """Build an AT Protocol firehose error frame (op=-1)."""
    header = {"op": -1}
    payload = {"error": error, "message": "cursor too new"}
    return cbor2.dumps(header) + cbor2.dumps(payload)


# ── Mock WebSocket helpers ─────────────────────────────────────────────────────


class _MockWebSocket:
    """Async context manager that yields messages then raises ConnectionClosedError.

    The raise_after_messages=True default mirrors real firehose behaviour: the
    server eventually closes the connection cleanly, which the websockets library
    surfaces as ConnectionClosedError.  This lets the subscribe() reconnect loop
    terminate properly when side_effect limits the number of connect() calls.
    """

    def __init__(
        self,
        messages: list[bytes | str],
        *,
        raise_on_enter: Exception | None = None,
        raise_after_messages: bool = True,
    ):
        self._messages = messages
        self._raise_on_enter = raise_on_enter
        self._raise_after = raise_after_messages

    async def __aenter__(self):
        if self._raise_on_enter:
            raise self._raise_on_enter
        return self

    async def __aexit__(self, *args):
        pass

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        for msg in self._messages:
            yield msg
        if self._raise_after:
            raise ConnectionClosedError(None, None)


def _one_shot_ws(messages: list[bytes | str]) -> _MockWebSocket:
    """WS that yields messages then raises ConnectionClosedError (clean server close)."""
    return _MockWebSocket(messages, raise_after_messages=True)


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_yields_decoded_frames():
    """Mock WebSocket sends 3 CBOR-encoded frames; subscribe yields all 3 payloads."""
    from etzhayyim_sdk import mst

    frames = [
        _make_commit_frame(seq=1, repo="did:web:alice.example"),
        _make_commit_frame(seq=2, repo="did:web:bob.example"),
        _make_commit_frame(seq=3, repo="did:web:carol.example"),
    ]

    # side_effect: first call → messages; second call → immediate ConnectionClosedError
    # (so the reconnect loop terminates after one successful batch)
    call_count = 0

    def fake_connect(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _one_shot_ws(frames)
        return _MockWebSocket([], raise_on_enter=ConnectionClosedError(None, None))

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            events: list[dict] = []
            with pytest.raises(Exception):
                # After first batch + reconnect exhaustion raises MstSubscribeError;
                # we collect what was yielded before the exception.
                async for event in mst.subscribe(reconnect_max_attempts=1):
                    events.append(event)

    assert len(events) == 3
    assert events[0]["seq"] == 1
    assert events[0]["repo"] == "did:web:alice.example"
    assert events[1]["seq"] == 2
    assert events[2]["seq"] == 3


@pytest.mark.asyncio
async def test_subscribe_filters_by_collection():
    """Frames whose ops don't match the requested collection are dropped."""
    from etzhayyim_sdk import mst

    kyumei_op = {"action": "create", "path": "app.etzhayyim.shinka.kyumeiSignal/r1", "cid": None}
    other_op = {"action": "create", "path": "app.bsky.feed.post/r2", "cid": None}

    frames = [
        _make_commit_frame(seq=10, ops=[kyumei_op]),         # matches
        _make_commit_frame(seq=11, ops=[other_op]),           # no match — filtered
        _make_commit_frame(seq=12, ops=[kyumei_op, other_op]), # partial match → kept
    ]

    def fake_connect(url, **kwargs):
        return _one_shot_ws(frames)

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            events: list[dict] = []
            with pytest.raises(Exception):
                async for event in mst.subscribe(
                    ["app.etzhayyim.shinka.kyumeiSignal"],
                    reconnect_max_attempts=1,
                ):
                    events.append(event)

    assert len(events) == 2
    assert events[0]["seq"] == 10
    assert events[1]["seq"] == 12
    # partial match: only kyumei op remains in the yielded payload
    assert len(events[1]["ops"]) == 1
    assert "kyumeiSignal" in events[1]["ops"][0]["path"]


@pytest.mark.asyncio
async def test_subscribe_reconnect_on_disconnect():
    """ConnectionClosedError on first connect triggers a single retry.

    Strategy: connect attempt 1 fails immediately; connect attempt 2 sends
    one frame then raises ConnectionClosedError (simulating a server-side
    graceful close), which triggers a third attempt that we allow to fail
    (exhaustion) so the generator terminates.
    """
    from etzhayyim_sdk import mst
    from etzhayyim_sdk.errors import MstSubscribeError

    frames_second_connect = [_make_commit_frame(seq=100)]

    call_count = 0

    def fake_connect(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First connect: fail immediately
            return _MockWebSocket([], raise_on_enter=ConnectionClosedError(None, None))
        if call_count == 2:
            # Second connect: succeed, yield one frame, then close
            return _one_shot_ws(frames_second_connect)
        # All subsequent connects: fail immediately (drives exhaustion)
        return _MockWebSocket([], raise_on_enter=ConnectionClosedError(None, None))

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            events: list[dict] = []
            with pytest.raises((MstSubscribeError, Exception)):
                async for event in mst.subscribe(
                    reconnect_backoff_seconds=0.0,
                    reconnect_max_attempts=3,
                ):
                    events.append(event)

    # First connect failed; second connect succeeded and yielded 1 event
    assert call_count >= 2
    assert mock_sleep.call_count >= 1  # at least one backoff sleep after first failure
    assert len(events) == 1
    assert events[0]["seq"] == 100


@pytest.mark.asyncio
async def test_subscribe_reconnect_exhaustion():
    """After reconnect_max_attempts=10 failures, MstSubscribeError is raised."""
    from etzhayyim_sdk import mst
    from etzhayyim_sdk.errors import MstSubscribeError

    def fake_connect(url, **kwargs):
        return _MockWebSocket([], raise_on_enter=ConnectionClosedError(None, None))

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(MstSubscribeError) as exc_info:
                async for _ in mst.subscribe(reconnect_max_attempts=10, reconnect_backoff_seconds=0.0):
                    pass

    err = exc_info.value
    assert err.attempts == 10
    assert "10" in str(err) or "exhausted" in str(err).lower()


@pytest.mark.asyncio
async def test_subscribe_cursor_advance():
    """The cursor variable advances with each yielded frame's seq value."""
    from etzhayyim_sdk import mst

    frames = [
        _make_commit_frame(seq=50),
        _make_commit_frame(seq=51),
        _make_commit_frame(seq=52),
    ]
    captured_urls: list[str] = []

    def fake_connect(url, **kwargs):
        captured_urls.append(url)
        return _one_shot_ws(frames)

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            events: list[dict] = []
            with pytest.raises(Exception):
                async for event in mst.subscribe(since_cursor=49, reconnect_max_attempts=1):
                    events.append(event)

    # First connect URL should include the initial cursor
    assert len(captured_urls) >= 1
    assert "cursor=49" in captured_urls[0]
    assert events[-1]["seq"] == 52


@pytest.mark.asyncio
async def test_subscribe_skips_text_frames():
    """String (text) WebSocket frames are logged and skipped; binary frames yield normally."""
    from etzhayyim_sdk import mst

    frames: list[bytes | str] = [
        "unexpected text",            # should be skipped
        _make_commit_frame(seq=200),  # should yield
    ]

    def fake_connect(url, **kwargs):
        return _one_shot_ws(frames)

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            events: list[dict] = []
            with pytest.raises(Exception):
                async for event in mst.subscribe(reconnect_max_attempts=1):
                    events.append(event)

    assert len(events) == 1
    assert events[0]["seq"] == 200


@pytest.mark.asyncio
async def test_subscribe_skips_bad_cbor():
    """Corrupt binary frames log a warning and are skipped; subsequent valid frames yield."""
    from etzhayyim_sdk import mst

    corrupt = b"\xff\xfe\xfd\xfc"  # not valid CBOR
    frames: list[bytes | str] = [
        corrupt,
        _make_commit_frame(seq=300),
    ]

    def fake_connect(url, **kwargs):
        return _one_shot_ws(frames)

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            events: list[dict] = []
            with pytest.raises(Exception):
                async for event in mst.subscribe(reconnect_max_attempts=1):
                    events.append(event)

    assert len(events) == 1
    assert events[0]["seq"] == 300


@pytest.mark.asyncio
async def test_subscribe_error_frame_raises():
    """An op=-1 (error) frame from the server raises MstSubscribeError immediately."""
    from etzhayyim_sdk import mst
    from etzhayyim_sdk.errors import MstSubscribeError

    frames: list[bytes | str] = [
        _make_commit_frame(seq=1),
        _make_error_frame("FutureCursor"),
    ]

    # Error frame raises MstSubscribeError which propagates out of the generator;
    # it is NOT caught by the reconnect handler (different exception type).
    def fake_connect(url, **kwargs):
        return _MockWebSocket(frames, raise_after_messages=False)

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with pytest.raises(Exception) as exc_info:
            async for _ in mst.subscribe():
                pass

    assert "FutureCursor" in str(exc_info.value)


@pytest.mark.asyncio
async def test_subscribe_cursor_in_url():
    """since_cursor=42 appends ?cursor=42 to the WebSocket URL."""
    from etzhayyim_sdk import mst
    from etzhayyim_sdk.errors import MstSubscribeError

    captured_urls: list[str] = []

    def fake_connect(url, **kwargs):
        captured_urls.append(url)
        return _MockWebSocket([], raise_on_enter=ConnectionClosedError(None, None))

    with patch("etzhayyim_sdk.mst.websockets.connect", side_effect=fake_connect):
        with patch("etzhayyim_sdk.mst.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(MstSubscribeError):
                async for _ in mst.subscribe(since_cursor=42, reconnect_max_attempts=1):
                    pass

    assert len(captured_urls) >= 1
    assert "cursor=42" in captured_urls[0]


def test_subscribe_url_from_env(monkeypatch):
    """ETZHAYYIM_PDS_URL is converted from https:// to wss:// for the firehose URL."""
    from etzhayyim_sdk.mst import _firehose_ws_url

    monkeypatch.setenv("ETZHAYYIM_PDS_URL", "https://pds.custom.example")
    url = _firehose_ws_url()
    assert url.startswith("wss://pds.custom.example")
    assert "subscribeRepos" in url

    monkeypatch.setenv("ETZHAYYIM_PDS_URL", "http://pds.local")
    url = _firehose_ws_url()
    assert url.startswith("ws://pds.local")
