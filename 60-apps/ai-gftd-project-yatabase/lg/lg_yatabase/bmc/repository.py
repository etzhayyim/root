"""BMC repository — INSERT-only writes + read paths against the MVs.

Honours:
  * root CLAUDE.md §"Record-log semantics, not MST" — no UPDATE, no
    ON CONFLICT; PK re-INSERT is implicit upsert.
  * ADR-0095 — every row carries (actor_did, org_did, at_did, created_at).
  * graph-schema CLAUDE.md §"CSR/CSC/SpMV Query Patterns" — current
    status is read from `mv_bmc_hypothesis_status`, current head from
    `mv_bmc_state_head`, latest iteration from `mv_bmc_iteration_latest`.

TODO(substrate-boundary): replace all RW queries with AT Protocol MST writes
per ADR-2605172000. append_state/append_hypothesis/append_iteration become
e.write({collection: 'app.etzhayyim.apps.yata.bmc.state', ...}). Read paths use
e.read() with MST prefix scans. Record-log semantics naturally enforce by
MST immutability.
"""

from __future__ import annotations

import contextlib
import json
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from lg_yatabase.bmc.db import execute, fetch, fetchrow, fetchval, get_pool

_log = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ulid() -> str:
    # uuid4 hex is sufficient — sortability comes from created_at.
    return uuid.uuid4().hex


def _slug_id(slug: str) -> str:
    return f"bmc:hyp:{slug}"


def _state_id(version: int) -> str:
    return f"bmc:state:v{version}"


def _iter_id() -> str:
    return f"bmc:iter:{_ulid()}"


def _dec_id() -> str:
    return f"bmc:dec:{_ulid()}"


def _evt_id(slug: str) -> str:
    return f"bmc:hyp_evt:{slug}:{_ulid()}"


def _sample_id() -> str:
    return f"bmc:sample:{_ulid()}"


# ── State (canvas) ─────────────────────────────────────────────────────


async def get_head(org_did: str) -> dict[str, Any] | None:
    return await fetchrow(
        """
        SELECT vertex_id, version, canvas_json, rationale, source,
               created_by, created_at
        FROM mv_bmc_state_head
        WHERE org_did = $1
        LIMIT 1
        """,
        org_did,
    )


async def append_state(
    *,
    canvas_json: str,
    rationale: str,
    source: str,
    actor_did: str,
    org_did: str,
    created_by: str | None = None,
) -> dict[str, Any]:
    head = await get_head(org_did)
    next_v = (head["version"] if head else 0) + 1
    vid = _state_id(next_v)
    now = _now_iso()
    parent = head["vertex_id"] if head else None
    await execute(
        """
        INSERT INTO vertex_bmc_state
          (vertex_id, version, canvas_json, rationale, source, parent_vertex_id,
           sensitivity_ord, owner_did, actor_did, org_did, at_did,
           created_by, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, 1, $7, $7, $8, NULL, $9, $10)
        """,
        vid, next_v, canvas_json[:65536], rationale[:4096], source[:128], parent,
        actor_did, org_did, created_by or actor_did, now,
    )
    if parent:
        await execute(
            """
            INSERT INTO edge_bmc_state_supersedes
              (edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
               actor_did, org_did, at_did, created_at)
            VALUES ($1, $2, $3, 1, $4, $4, $5, NULL, $6)
            """,
            f"bmc:supersedes:{vid}", vid, parent, actor_did, org_did, now,
        )
    return {"vertex_id": vid, "version": next_v}


# ── Hypothesis ─────────────────────────────────────────────────────────


async def add_hypothesis(
    *,
    slug: str,
    block: str,
    statement: str,
    metric: str,
    metric_query: str,
    threshold: float,
    baseline: float,
    deadline_iso: str,
    min_sample: int,
    authored_by: str,
    auto_apply_pivot: bool,
    actor_did: str,
    org_did: str,
) -> dict[str, Any]:
    now = _now_iso()
    vid = _slug_id(slug)
    await execute(
        """
        INSERT INTO vertex_bmc_hypothesis
          (vertex_id, slug, block, statement, metric, metric_query,
           threshold, baseline, deadline_iso, min_sample, authored_by,
           auto_apply_pivot, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                1, $13, $13, $14, NULL, $15)
        """,
        vid, slug, block, statement[:1024], metric[:256], metric_query[:4096],
        threshold, baseline, deadline_iso, min_sample, authored_by[:256],
        1 if auto_apply_pivot else 0, actor_did, org_did, now,
    )
    # Initial status event = pending.
    await append_hypothesis_event(
        slug=slug,
        next_status="pending",
        reason="initial",
        authored_by=authored_by,
        actor_did=actor_did,
        org_did=org_did,
    )
    return {"vertex_id": vid}


async def append_hypothesis_event(
    *,
    slug: str,
    next_status: str,
    authored_by: str,
    actor_did: str,
    org_did: str,
    reason: str | None = None,
    iteration_vertex_id: str | None = None,
) -> dict[str, Any]:
    prev = await fetchval(
        """
        SELECT status FROM mv_bmc_hypothesis_status
        WHERE hypothesis_slug = $1 AND org_did = $2
        """,
        slug, org_did,
    )
    vid = _evt_id(slug)
    now = _now_iso()
    await execute(
        """
        INSERT INTO vertex_bmc_hypothesis_event
          (vertex_id, hypothesis_slug, prev_status, next_status, reason,
           authored_by, iteration_vertex_id, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 1, $8, $8, $9, NULL, $10)
        """,
        vid, slug, prev, next_status, (reason or "")[:1024],
        authored_by[:256], iteration_vertex_id,
        actor_did, org_did, now,
    )
    return {"vertex_id": vid, "prev_status": prev, "next_status": next_status}


async def list_hypotheses(
    *,
    org_did: str,
    status: str | None = None,
    block: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    base_filters = ["h.org_did = $1"]
    params: list[Any] = [org_did]
    if status is not None:
        params.append(status)
        base_filters.append(f"s.status = ${len(params)}")
    if block is not None:
        params.append(block)
        base_filters.append(f"h.block = ${len(params)}")
    where_sql = " AND ".join(base_filters)

    off_i = max(0, int(offset))
    lim_i = max(1, min(200, int(limit)))
    rows = await fetch(
        f"""
        SELECT h.vertex_id, h.slug, h.block, h.statement, h.metric,
               h.metric_query, h.threshold, h.baseline, h.deadline_iso,
               h.min_sample, h.authored_by, h.auto_apply_pivot,
               COALESCE(s.status, 'pending') AS status,
               s.status_at,
               h.created_at
        FROM vertex_bmc_hypothesis h
        LEFT JOIN mv_bmc_hypothesis_status s
          ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
        WHERE {where_sql}
        ORDER BY h.deadline_iso ASC, h.created_at ASC
        OFFSET {off_i} LIMIT {lim_i}
        """,
        *params,
    )
    total = await fetchval(
        f"""
        SELECT COUNT(*) FROM vertex_bmc_hypothesis h
        LEFT JOIN mv_bmc_hypothesis_status s
          ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
        WHERE {where_sql}
        """,
        *params,
    )
    return rows, int(total or 0)


async def pick_next_hypothesis(org_did: str) -> dict[str, Any] | None:
    """Selection policy (see design): overdue > never-iterated > LRU."""
    now = _now_iso()
    overdue = await fetchrow(
        """
        SELECT h.*
        FROM vertex_bmc_hypothesis h
        JOIN mv_bmc_hypothesis_status s
          ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
        WHERE h.org_did = $1
          AND s.status = 'active'
          AND h.deadline_iso <= $2
        ORDER BY h.deadline_iso ASC
        LIMIT 1
        """,
        org_did, now,
    )
    if overdue:
        return overdue
    never = await fetchrow(
        """
        SELECT h.*
        FROM vertex_bmc_hypothesis h
        JOIN mv_bmc_hypothesis_status s
          ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
        LEFT JOIN mv_bmc_iteration_latest i
          ON i.hypothesis_slug = h.slug AND i.org_did = h.org_did
        WHERE h.org_did = $1
          AND s.status = 'active'
          AND i.iteration_vertex_id IS NULL
        ORDER BY h.created_at ASC
        LIMIT 1
        """,
        org_did,
    )
    if never:
        return never
    lru = await fetchrow(
        """
        SELECT h.*, i.created_at AS last_iter_at
        FROM vertex_bmc_hypothesis h
        JOIN mv_bmc_hypothesis_status s
          ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
        LEFT JOIN mv_bmc_iteration_latest i
          ON i.hypothesis_slug = h.slug AND i.org_did = h.org_did
        WHERE h.org_did = $1
          AND s.status = 'active'
        ORDER BY i.created_at ASC NULLS FIRST, h.created_at ASC
        LIMIT 1
        """,
        org_did,
    )
    return lru


async def next_iteration_no(slug: str, org_did: str) -> int:
    n = await fetchval(
        """
        SELECT COALESCE(MAX(iteration_no), 0) + 1
        FROM vertex_bmc_iteration
        WHERE hypothesis_slug = $1 AND org_did = $2
        """,
        slug, org_did,
    )
    return int(n or 1)


# ── Iteration + decision + sample ──────────────────────────────────────


async def record_metric_sample(
    *,
    iteration_vertex_id: str,
    hypothesis_slug: str,
    metric: str,
    metric_query: str,
    measured_value: float,
    sample_size: int,
    source: str,
    actor_did: str,
    org_did: str,
    numerator: float | None = None,
    denominator: float | None = None,
    window_start_ms: int | None = None,
    window_end_ms: int | None = None,
    raw_response: str | None = None,
    latency_ms: int | None = None,
    error_text: str | None = None,
) -> dict[str, Any]:
    vid = _sample_id()
    now = _now_iso()
    await execute(
        """
        INSERT INTO vertex_bmc_metric_sample
          (vertex_id, iteration_vertex_id, hypothesis_slug, metric,
           metric_query, numerator, denominator, measured_value, sample_size,
           window_start_ms, window_end_ms, source, raw_response, latency_ms,
           error_text, sensitivity_ord, owner_did, actor_did, org_did,
           at_did, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                $14, $15, 2, $16, $16, $17, NULL, $18)
        """,
        vid, iteration_vertex_id, hypothesis_slug, metric[:256],
        metric_query[:4096], numerator, denominator, measured_value, sample_size,
        window_start_ms, window_end_ms, source[:256],
        (raw_response or "")[:4096], latency_ms,
        (error_text or "")[:1024], actor_did, org_did, now,
    )
    return {"vertex_id": vid}


async def record_iteration(
    *,
    hypothesis_slug: str,
    iteration_no: int,
    bmc_version_in: int,
    bmc_version_out: int,
    measured_value: float,
    measurement_source: str,
    passed: bool,
    actor_did: str,
    org_did: str,
    notes: str | None = None,
) -> dict[str, Any]:
    vid = _iter_id()
    now = _now_iso()
    await execute(
        """
        INSERT INTO vertex_bmc_iteration
          (vertex_id, hypothesis_slug, iteration_no, bmc_version_in,
           bmc_version_out, measured_value, measured_at, measurement_source,
           passed, notes, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 1, $11,
                $11, $12, NULL, $13)
        """,
        vid, hypothesis_slug, iteration_no, bmc_version_in, bmc_version_out,
        measured_value, now, measurement_source[:256],
        1 if passed else 0, (notes or "")[:4096],
        actor_did, org_did, now,
    )
    # CSR edge iteration -> hypothesis
    await execute(
        """
        INSERT INTO edge_bmc_iteration_of_hypothesis
          (edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, 1, $4, $4, $5, NULL, $6)
        """,
        f"bmc:e_iter_hyp:{vid}", vid, _slug_id(hypothesis_slug),
        actor_did, org_did, now,
    )
    return {"vertex_id": vid}


async def record_decision(
    *,
    iteration_vertex_id: str,
    hypothesis_slug: str,
    action: str,
    rationale: str,
    authored_by: str,
    actor_did: str,
    org_did: str,
) -> dict[str, Any]:
    vid = _dec_id()
    now = _now_iso()
    await execute(
        """
        INSERT INTO vertex_bmc_decision
          (vertex_id, iteration_vertex_id, hypothesis_slug, action,
           rationale, authored_by, applied_at, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 1, $8, $8, $9, NULL, $10)
        """,
        vid, iteration_vertex_id, hypothesis_slug, action,
        rationale[:4096], authored_by[:256], now,
        actor_did, org_did, now,
    )
    await execute(
        """
        INSERT INTO edge_bmc_decision_of_iteration
          (edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, 1, $4, $4, $5, NULL, $6)
        """,
        f"bmc:e_dec_iter:{vid}", vid, iteration_vertex_id,
        actor_did, org_did, now,
    )
    return {"vertex_id": vid}


async def link_pivot_to_state(
    *,
    decision_vertex_id: str,
    state_vertex_id: str,
    actor_did: str,
    org_did: str,
) -> None:
    now = _now_iso()
    await execute(
        """
        INSERT INTO edge_bmc_pivot_applied_to_state
          (edge_id, src_vid, dst_vid, sensitivity_ord, owner_did,
           actor_did, org_did, at_did, created_at)
        VALUES ($1, $2, $3, 1, $4, $4, $5, NULL, $6)
        """,
        f"bmc:e_pivot:{decision_vertex_id}", decision_vertex_id, state_vertex_id,
        actor_did, org_did, now,
    )


# ── Reads (iterations / decisions / block health) ─────────────────────


async def list_iterations(
    *,
    org_did: str,
    hypothesis_slug: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    filters = ["org_did = $1"]
    params: list[Any] = [org_did]
    if hypothesis_slug:
        params.append(hypothesis_slug)
        filters.append(f"hypothesis_slug = ${len(params)}")
    where = " AND ".join(filters)
    off_i = max(0, int(offset))
    lim_i = max(1, min(200, int(limit)))
    rows = await fetch(
        f"""
        SELECT vertex_id, hypothesis_slug, iteration_no, bmc_version_in,
               bmc_version_out, measured_value, measured_at, measurement_source,
               passed, notes, created_at
        FROM vertex_bmc_iteration
        WHERE {where}
        ORDER BY created_at DESC
        OFFSET {off_i} LIMIT {lim_i}
        """,
        *params,
    )
    total = await fetchval(
        f"SELECT COUNT(*) FROM vertex_bmc_iteration WHERE {where}",
        *params,
    )
    return rows, int(total or 0)


async def list_decisions(
    *,
    org_did: str,
    hypothesis_slug: str | None = None,
    action: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    filters = ["org_did = $1"]
    params: list[Any] = [org_did]
    if hypothesis_slug:
        params.append(hypothesis_slug)
        filters.append(f"hypothesis_slug = ${len(params)}")
    if action:
        params.append(action)
        filters.append(f"action = ${len(params)}")
    where = " AND ".join(filters)
    off_i = max(0, int(offset))
    lim_i = max(1, min(200, int(limit)))
    rows = await fetch(
        f"""
        SELECT vertex_id, iteration_vertex_id, hypothesis_slug, action,
               rationale, authored_by, applied_at, created_at
        FROM vertex_bmc_decision
        WHERE {where}
        ORDER BY created_at DESC
        OFFSET {off_i} LIMIT {lim_i}
        """,
        *params,
    )
    total = await fetchval(
        f"SELECT COUNT(*) FROM vertex_bmc_decision WHERE {where}",
        *params,
    )
    return rows, int(total or 0)


async def block_health(org_did: str) -> list[dict[str, Any]]:
    return await fetch(
        """
        SELECT block, hyp_total, hyp_active, hyp_completed, hyp_killed,
               avg_measured, last_iter_at
        FROM mv_bmc_block_health
        WHERE org_did = $1
        ORDER BY block
        """,
        org_did,
    )


# ── Mutex (cron + on-demand iterate) ──────────────────────────────────


@contextlib.asynccontextmanager
async def iterate_lock(org_did: str) -> AsyncIterator[bool]:
    """Per-org distributed lock via AT MST lock records.

    TODO(substrate-boundary): Implement via MST lock record pattern.
    For now, always yields True (no actual locking). Callers should
    implement idempotency in their iterate() logic.

    Historical: Used PG advisory locks (pg_try_advisory_lock).
    """
    # TODO: Implement MST-backed lock using a dedicated lock collection:
    # - createRecord(org_did + "/bmc/iterate-lock") with timestamp
    # - getRecord to check if current timestamp is within TTL
    # - Cleanup via cron job for stale locks
    _log.warning("[bmc.repository] iterate_lock: distributed lock not yet implemented; returning True")
    yield True
