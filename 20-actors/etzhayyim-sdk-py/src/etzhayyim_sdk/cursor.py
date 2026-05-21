"""Cursor persistence helper for mst.subscribe() firehose consumption.

Per ADR-2605215200 §1 and Task 44 open follow-up: cursor persistence is caller
responsibility. This module provides a recommended pattern that wraps subscribe()
with auto-checkpoint to an `app.etzhayyim.shinka.firehoseCursor` MST record.

Usage:
    from etzhayyim_sdk import cursor as cursor_helper

    async for event in cursor_helper.subscribe_with_checkpoint(
        collections=["app.bsky.feed.post"],
        cursor_id="my-cell",
    ):
        ...  # process event
        # cursor auto-checkpoints every `checkpoint_every` events (default 100)
        # or every `checkpoint_interval_s` seconds (default 30)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from . import mst, pds

_log = logging.getLogger(__name__)

CURSOR_COLLECTION = "app.etzhayyim.shinka.firehoseCursor"

# Module-level cache for active cursor sessions
_active_cursors: dict[str, int] = {}


async def get_cursor(cursor_id: str) -> int | None:
    """Read latest persisted cursor for cursor_id. Returns None if not yet set."""
    rkey = _safe_rkey(cursor_id)
    try:
        result = await pds.get_record(
            uri=f"at://{_default_repo()}/{CURSOR_COLLECTION}/{rkey}"
        )
        return int(result.get("value", {}).get("seq", 0))
    except Exception:
        return None


async def put_cursor(cursor_id: str, seq: int) -> None:
    """Persist cursor for cursor_id."""
    rkey = _safe_rkey(cursor_id)
    record = {
        "cursorId": cursor_id,
        "seq": seq,
        "updatedAt": _now_iso(),
    }
    await pds.put_record(
        collection=CURSOR_COLLECTION,
        record=record,
        rkey=rkey,
    )
    _active_cursors[cursor_id] = seq


async def subscribe_with_checkpoint(
    *,
    cursor_id: str,
    collections: list[str] | None = None,
    checkpoint_every: int = 100,
    checkpoint_interval_s: float = 30.0,
    since_cursor: int | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Subscribe to MST firehose with auto-checkpointed cursor.

    cursor_id: unique identifier for this consumer (e.g. "shinka-aggregator").
    Persists cursor to app.etzhayyim.shinka.firehoseCursor MST record.

    Yields events from mst.subscribe(). Caller can process events
    incrementally; checkpoint fires automatically every N events or every T seconds.
    """
    # Resume from persisted cursor if not explicitly overridden
    if since_cursor is None:
        since_cursor = await get_cursor(cursor_id) or 0

    last_checkpoint_time = time.time()
    events_since_checkpoint = 0

    async for event in mst.subscribe(
        collections=collections,
        since_cursor=since_cursor,
    ):
        yield event
        events_since_checkpoint += 1

        now = time.time()
        if (
            events_since_checkpoint >= checkpoint_every
            or (now - last_checkpoint_time) >= checkpoint_interval_s
        ):
            seq = event.get("seq", 0)
            if seq:
                await put_cursor(cursor_id, seq)
                last_checkpoint_time = now
                events_since_checkpoint = 0


# ── Helpers ──


def _default_repo() -> str:
    return os.environ.get("ETZHAYYIM_PDS_DEFAULT_REPO", "did:web:etzhayyim.com")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_rkey(cursor_id: str) -> str:
    """Convert cursor_id to PDS-safe rkey (no : or /)."""
    return cursor_id.replace(":", "_").replace("/", "_").replace(" ", "_")
