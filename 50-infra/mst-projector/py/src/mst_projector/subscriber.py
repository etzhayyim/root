"""mst-projector subscriber — consume AT Protocol firehose, dispatch to indexer.

Per ADR-2605215500 §1 architecture, M2 milestone deliverable.

Subscribes to com.atproto.sync.subscribeRepos via etzhayyim_sdk.cursor.subscribe_with_checkpoint(),
decodes each commit event, dispatches per-op to indexer.index_op() (create/update)
or indexer.delete_op() (delete). Periodic cursor checkpoint to data dir.

CBOR decoding is delegated to etzhayyim_sdk.mst.subscribe() which already does the
CBOR frame decode; events arrive as Python dicts with {seq, repo, ops, blocks, ...}.
"""

from __future__ import annotations

import logging
from typing import Any

from etzhayyim_sdk import cursor as _sdk_cursor
from etzhayyim_sdk import pds as _pds

from .indexer import get_indexer

_log = logging.getLogger(__name__)


def _resolve_collections(collections: list[str] | str | None) -> list[str] | None:
    """Normalize collections arg. None → all collections (no filter)."""
    if collections is None:
        return None
    if isinstance(collections, str):
        return [collections]
    return list(collections)


def _extract_ops(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Pure: extract ops list from firehose event."""
    ops = event.get("ops") or []
    return [op for op in ops if isinstance(op, dict)]


def _parse_op_path(path: str) -> tuple[str, str]:
    """Pure: split AT op path 'collection/rkey' → (collection, rkey).

    Returns ('', '') on malformed paths.
    """
    if "/" not in path:
        return ("", "")
    collection, _, rkey = path.partition("/")
    return (collection, rkey)


async def _resolve_record_value(
    op: dict[str, Any],
    event: dict[str, Any],
    repo: str,
) -> dict[str, Any] | None:
    """Resolve the record value for an op.

    For now (M2 simplified): attempt to extract from ``op.record`` if present,
    else fall back to pds.get_record() of the URI.

    Future M3: decode from ``event.blocks`` (CAR-encoded) to avoid extra fetch.
    """
    if "record" in op and isinstance(op["record"], dict):
        return op["record"]

    cid = op.get("cid", "")
    path = op.get("path", "")
    if not cid or not path:
        return None

    uri = f"at://{repo}/{path}"
    try:
        result = await _pds.get_record(uri=uri)
        return result.get("value", result)
    except Exception as e:
        _log.debug("could not resolve record for %s: %s", uri, e)
        return None


async def run_subscriber(
    *,
    collections: list[str] | str | None = None,
    cursor_id: str = "mst-projector-default",
    checkpoint_every: int = 100,
    checkpoint_interval_s: float = 30.0,
) -> None:
    """Main subscriber loop. Runs until SIGTERM or unhandled error.

    Args:
        collections:          Optional collection NSID filter.  None = all collections.
        cursor_id:            Identifier for this projector's checkpoint
                              (default "mst-projector-default").
        checkpoint_every:     Flush cursor after this many events (default 100).
        checkpoint_interval_s: Also flush cursor every N seconds (default 30).
    """
    indexer = get_indexer()
    target_collections = _resolve_collections(collections)

    _log.info(
        "mst-projector subscriber starting (collections=%s, cursor_id=%s)",
        target_collections,
        cursor_id,
    )

    async for event in _sdk_cursor.subscribe_with_checkpoint(
        cursor_id=cursor_id,
        collections=target_collections,
        checkpoint_every=checkpoint_every,
        checkpoint_interval_s=checkpoint_interval_s,
    ):
        try:
            await _process_event(event, indexer)
        except Exception as e:
            _log.error(
                "subscriber: failed to process event seq=%s: %s",
                event.get("seq"),
                e,
                exc_info=True,
            )
            # Continue on error — don't kill the subscriber for one bad event


async def _process_event(event: dict[str, Any], indexer: Any) -> None:
    """Process one firehose event. Each op dispatches to indexer per action."""
    seq = event.get("seq", 0)
    repo = event.get("repo", "")
    if not repo:
        return

    for op in _extract_ops(event):
        action = op.get("action", "")
        path = op.get("path", "")
        collection, rkey = _parse_op_path(path)
        if not collection or not rkey:
            continue

        if action == "delete":
            await indexer.delete_op(
                collection,
                repo,
                rkey,
            )
        elif action in ("create", "update"):
            record = await _resolve_record_value(op, event, repo)
            if record is None:
                _log.warning(
                    "subscriber: could not resolve record for op seq=%s path=%s",
                    seq,
                    path,
                )
                continue

            cid = op.get("cid", "")
            await indexer.index_op(
                collection,
                repo,
                rkey,
                cid,
                record,
            )
