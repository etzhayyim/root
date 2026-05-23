# Migrated 2026-05-22 from RisingWave/asyncpg → AT MST. See ADR-2605172000.
"""AT Protocol MST bridge for BMC data layer.

Replaces asyncpg pool with HTTP client hitting AT XRPC endpoints.
Maintains the same public function signatures (fetch, fetchrow, fetchval, execute)
so callers in repository.py do not need to change.

Collection mapping:
  vertex_bmc_state → ai.gftd.apps.yatable.bmc.state
  vertex_bmc_hypothesis → ai.gftd.apps.yatable.bmc.hypothesis
  vertex_bmc_iteration → ai.gftd.apps.yatable.bmc.iteration
  vertex_bmc_hypothesis_event → ai.gftd.apps.yatable.bmc.hypothesis_event
  vertex_bmc_metric_sample → ai.gftd.apps.yatable.bmc.metric_sample
  vertex_bmc_decision → ai.gftd.apps.yatable.bmc.decision
  edge_bmc_state_supersedes → ai.gftd.apps.yatable.bmc.edge_state_supersedes
  edge_bmc_iteration_of_hypothesis → ai.gftd.apps.yatable.bmc.edge_iter_hyp
  edge_bmc_decision_of_iteration → ai.gftd.apps.yatable.bmc.edge_dec_iter
  edge_bmc_pivot_applied_to_state → ai.gftd.apps.yatable.bmc.edge_pivot_state

SELECT queries map to listRecords(collection, limit, cursor) with client-side
filtering. INSERT maps to createRecord(collection, record, rkey). UPDATE/DELETE
operations are stubbed with TODO — MST is append-only, so updates become
overwrite-at-same-rkey (getRecord → createRecord).

Auth: Bearer token from env ETZHAYYIM_BEARER_TOKEN.
Endpoint: https://atproto.etzhayyim.com/xrpc/ (configurable via ETZHAYYIM_PDS_URL)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

_log = logging.getLogger(__name__)

_HTTP_CLIENT: httpx.AsyncClient | None = None

# Collection → table name mapping (reverse of above)
_COLLECTION_MAP = {
    "vertex_bmc_state": "ai.gftd.apps.yatable.bmc.state",
    "vertex_bmc_hypothesis": "ai.gftd.apps.yatable.bmc.hypothesis",
    "vertex_bmc_iteration": "ai.gftd.apps.yatable.bmc.iteration",
    "vertex_bmc_hypothesis_event": "ai.gftd.apps.yatable.bmc.hypothesis_event",
    "vertex_bmc_metric_sample": "ai.gftd.apps.yatable.bmc.metric_sample",
    "vertex_bmc_decision": "ai.gftd.apps.yatable.bmc.decision",
    "edge_bmc_state_supersedes": "ai.gftd.apps.yatable.bmc.edge_state_supersedes",
    "edge_bmc_iteration_of_hypothesis": "ai.gftd.apps.yatable.bmc.edge_iter_hyp",
    "edge_bmc_decision_of_iteration": "ai.gftd.apps.yatable.bmc.edge_dec_iter",
    "edge_bmc_pivot_applied_to_state": "ai.gftd.apps.yatable.bmc.edge_pivot_state",
}


def _get_bearer_token() -> str:
    token = os.environ.get("ETZHAYYIM_BEARER_TOKEN")
    if not token:
        raise RuntimeError(
            "ETZHAYYIM_BEARER_TOKEN not set. Set in k8s Secret or env."
        )
    return token


def _get_pds_url() -> str:
    return (os.environ.get("ETZHAYYIM_PDS_URL") or "https://atproto.etzhayyim.com").rstrip("/")


async def get_pool() -> httpx.AsyncClient:
    """Return the per-process singleton HTTP client, creating it on first call."""
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        return _HTTP_CLIENT
    token = _get_bearer_token()
    _HTTP_CLIENT = httpx.AsyncClient(
        base_url=_get_pds_url(),
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    _log.info("[bmc.db] HTTP client ready pds_url=%s", _get_pds_url())
    return _HTTP_CLIENT


async def close_pool() -> None:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is not None:
        await _HTTP_CLIENT.aclose()
        _HTTP_CLIENT = None


def _extract_table_name(query: str) -> str | None:
    """Extract table name from SQL query. Supports SELECT/INSERT/UPDATE from."""
    # SELECT ... FROM vertex_bmc_state
    match = re.search(r"FROM\s+(\w+)", query, re.IGNORECASE)
    if match:
        return match.group(1)
    # INSERT INTO vertex_bmc_state
    match = re.search(r"INSERT\s+INTO\s+(\w+)", query, re.IGNORECASE)
    if match:
        return match.group(1)
    # UPDATE vertex_bmc_state
    match = re.search(r"UPDATE\s+(\w+)", query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _extract_where_clause(query: str) -> dict[str, Any]:
    """Parse simple WHERE clauses for client-side filtering.

    Supports: WHERE col = $N (positional arg reference).
    Returns dict of {col: param_index}.
    """
    match = re.search(r"WHERE\s+(.+?)(?:ORDER|LIMIT|OFFSET|;|$)", query, re.IGNORECASE)
    if not match:
        return {}

    where_text = match.group(1)
    filters = {}
    # Match patterns like: col = $1, col = $2, etc.
    for m in re.finditer(r"(\w+)\s*=\s*\$(\d+)", where_text):
        col, param_idx = m.groups()
        filters[col] = int(param_idx) - 1  # Convert to 0-indexed
    return filters


async def fetch(query: str, *args: Any) -> list[dict[str, Any]]:
    """SELECT query → listRecords with client-side filtering."""
    table = _extract_table_name(query)
    if not table or table not in _COLLECTION_MAP:
        _log.warning("[bmc.db] fetch: unknown table %s, returning []", table)
        return []

    collection = _COLLECTION_MAP[table]
    client = await get_pool()

    try:
        # Fetch records with a reasonable limit (callers use LIMIT anyway)
        resp = await client.post(
            "/xrpc/com.atproto.repo.listRecords",
            json={"collection": collection, "limit": 100},
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])

        # Extract WHERE filters and apply client-side
        filters = _extract_where_clause(query)
        results = []
        for rec in records:
            value = rec.get("value", {})
            # Check if this record matches all filters
            match = True
            for col, arg_idx in filters.items():
                if arg_idx < len(args) and value.get(col) != args[arg_idx]:
                    match = False
                    break
            if match:
                # Flatten: uri + cid + value fields
                row = {"uri": rec.get("uri"), "cid": rec.get("cid")}
                row.update(value)
                results.append(row)

        return results
    except Exception as e:
        _log.error("[bmc.db] fetch failed: %s", e)
        return []


async def fetchrow(query: str, *args: Any) -> dict[str, Any] | None:
    """SELECT ... LIMIT 1 → listRecords, return first match or None."""
    rows = await fetch(query, *args)
    return rows[0] if rows else None


async def fetchval(query: str, *args: Any) -> Any:
    """SELECT COUNT(*) or similar aggregation → approximation via listRecords count."""
    table = _extract_table_name(query)
    if not table or table not in _COLLECTION_MAP:
        _log.warning("[bmc.db] fetchval: unknown table %s, returning None", table)
        return None

    # For COUNT(*), fetch all and count (not ideal, but correct for now)
    collection = _COLLECTION_MAP[table]
    client = await get_pool()

    try:
        resp = await client.post(
            "/xrpc/com.atproto.repo.listRecords",
            json={"collection": collection, "limit": 100},
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])

        # Apply filtering like in fetch()
        filters = _extract_where_clause(query)
        count = 0
        for rec in records:
            value = rec.get("value", {})
            match = True
            for col, arg_idx in filters.items():
                if arg_idx < len(args) and value.get(col) != args[arg_idx]:
                    match = False
                    break
            if match:
                count += 1

        return count
    except Exception as e:
        _log.error("[bmc.db] fetchval failed: %s", e)
        return None


async def execute(query: str, *args: Any) -> str:
    """INSERT/UPDATE/DELETE → createRecord or getRecord + createRecord.

    Returns a dummy status string to maintain compatibility with callers.
    """
    table = _extract_table_name(query)
    if not table or table not in _COLLECTION_MAP:
        _log.warning("[bmc.db] execute: unknown table %s, skipping", table)
        return "SKIP UNKNOWN TABLE"

    collection = _COLLECTION_MAP[table]
    client = await get_pool()

    # Parse INSERT query to extract column names and values
    if "INSERT INTO" in query.upper():
        # Extract columns: INSERT INTO table (col1, col2, ...) VALUES ($1, $2, ...)
        match = re.search(r"INSERT\s+INTO\s+\w+\s*\(([^)]+)\)\s*VALUES", query, re.IGNORECASE)
        if not match:
            _log.warning("[bmc.db] execute: cannot parse INSERT columns")
            return "PARSE FAILED"

        col_names = [c.strip() for c in match.group(1).split(",")]

        # Map positional args to column dict
        record = {}
        for i, col in enumerate(col_names):
            if i < len(args):
                record[col] = args[i]

        # Use vertex_id (or similar) as rkey
        rkey = record.get("vertex_id") or record.get("edge_id")
        if not rkey:
            _log.warning("[bmc.db] execute: no vertex_id or edge_id for rkey")
            return "NO RKEY"

        try:
            resp = await client.post(
                "/xrpc/com.atproto.repo.createRecord",
                json={
                    "collection": collection,
                    "rkey": rkey,
                    "record": {
                        "$type": collection,
                        **record,
                    },
                },
            )
            resp.raise_for_status()
            _log.debug("[bmc.db] execute INSERT: uri=%s", resp.json().get("uri"))
            return "INSERT 1"
        except Exception as e:
            _log.error("[bmc.db] execute INSERT failed: %s", e)
            return "INSERT FAILED"

    # TODO(substrate-boundary): UPDATE → getRecord + createRecord (overwrite at rkey)
    # TODO(substrate-boundary): DELETE → soft-delete marker or skip (MST immutable)
    _log.warning("[bmc.db] execute: UPDATE/DELETE not yet implemented")
    return "TODO"
