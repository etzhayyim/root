"""Hyperdrive direct INSERT path for manimani (ADR-0036 + ADR-2605080800).

All domain writes for ``ai.gftd.apps.manimani.*`` go straight into
RisingWave through the canonical ``pymagatama.db_alchemy.sync_cursor``
helper (ADR-2605080300). PDS commit pipeline is **not** used —
manimani is non-federable.

Phase 1 (this file): minimal INSERT for ``vertex_manimani_intake``,
``vertex_manimani_run``, ``vertex_manimani_project`` (when project
emerges), ``vertex_manimani_artifact`` (per processor output), and
``edge_manimani_belongs_to`` (intake → project, primary edge). Skips
silently when ``GFTD_MANIMANI_DRY_RUN=1`` so the StateGraph can be
exercised without a live cluster.

Phase 2 (next session):
  - ``upsert_run_status`` for /runs polling
  - ``demote_primary_edges`` for the ``classify`` re-classification XRPC
  - ``BaseCheckpointSaver`` integration so the Pregel state survives
    pod restart (ADR-2605080600 P3)
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterable, Optional

from pymagatama.manimani.state import Artifact


# ── helpers ──────────────────────────────────────────────────────────


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _today_str() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _dict_query(sql: str, params: dict | None = None) -> list[dict]:
    """Run a raw SQL query and return rows as dicts. Wraps sync_cursor()."""
    from pymagatama.db_sync import sync_cursor  # type: ignore
    with sync_cursor() as cur:
        cur.execute(sql, params or {})
        cols = [d[0] for d in (cur.description or [])]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _exec(sql: str, params: dict | None = None) -> None:
    """Run a raw SQL statement (INSERT/UPDATE/DELETE) — no result fetched."""
    from pymagatama.db_sync import sync_cursor  # type: ignore
    with sync_cursor() as cur:
        cur.execute(sql, params or {})



def _dry_run() -> bool:
    return os.environ.get("GFTD_MANIMANI_DRY_RUN") == "1"


# ── reads ────────────────────────────────────────────────────────────


def list_active_projects_for_actor(
    *,
    actor_did: str,
    org_did: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Top-N active projects for the caller, ordered by ``last_intake_at``
    descending. Used by the classifier as its candidate context window.

    Returns ``[]`` in dry-run mode.
    """

    if _dry_run():
        return []

    rows = _dict_query(f"""
        SELECT vertex_id, project_did, slug, title, kind, status,
               intake_count, last_intake_at
          FROM vertex_manimani_project
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND status <> 'archived'
         ORDER BY COALESCE(last_intake_at, created_at) DESC
         LIMIT {int(limit)}
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    return [dict(r) for r in (rows or [])]


def get_project_by_slug(
    *,
    actor_did: str,
    org_did: str,
    slug: str,
) -> Optional[dict[str, Any]]:
    if _dry_run():
        return None

    rows = _dict_query("""
        SELECT vertex_id, project_did, slug, title, kind, status
          FROM vertex_manimani_project
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND slug = %(slug)s
         LIMIT 1
        """,
        {"actor_did": actor_did, "org_did": org_did, "slug": slug, "today": _today_str(), },
    )
    if not rows:
        return None
    return dict(rows[0])


def get_project_by_vertex_id(
    *,
    actor_did: str,
    org_did: str,
    vertex_id: str,
) -> Optional[dict[str, Any]]:
    if _dry_run():
        return None

    rows = _dict_query("""
        SELECT vertex_id, project_did, slug, title, kind, status,
               initial_tags_csv, intake_count, last_intake_at, created_at
          FROM vertex_manimani_project
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND vertex_id = %(vertex_id)s
         LIMIT 1
        """,
        {"actor_did": actor_did, "org_did": org_did, "vertex_id": vertex_id, "today": _today_str(), },
    )
    if not rows:
        return None
    return dict(rows[0])


def get_intake_by_vertex_id(
    *,
    actor_did: str,
    org_did: str,
    vertex_id: str,
) -> Optional[dict[str, Any]]:
    if _dry_run():
        return None

    rows = _dict_query("""
        SELECT vertex_id, source_kind, raw_text, source_uri, parsed_text,
               lang, sensitivity_ord, byte_size, ts_ms
          FROM vertex_manimani_intake
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND vertex_id = %(vertex_id)s
         LIMIT 1
        """,
        {"actor_did": actor_did, "org_did": org_did, "vertex_id": vertex_id, "today": _today_str(), },
    )
    if not rows:
        return None
    return dict(rows[0])


def list_artifacts_for_project(
    *,
    actor_did: str,
    org_did: str,
    project_vertex_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if _dry_run():
        return []

    rows = _dict_query(f"""
        SELECT vertex_id, intake_vertex_id, run_vertex_id,
               artifact_kind, content, model_id, error_text, created_at
          FROM vertex_manimani_artifact
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND project_vertex_id = %(project_vertex_id)s
         ORDER BY ts_ms DESC
         LIMIT {int(limit)}
        """,
        {
            "actor_did": actor_did,
            "org_did": org_did,
            "project_vertex_id": project_vertex_id,
        "today": _today_str(), },
    )
    return [dict(r) for r in (rows or [])]


def list_projects_for_actor(
    *,
    actor_did: str,
    org_did: str,
    status: Optional[str] = None,
    kind: Optional[str] = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    if _dry_run():
        return []

    where = ["actor_did = %(actor_did)s", "org_did = %(org_did)s"]
    params: dict[str, Any] = {"actor_did": actor_did, "org_did": org_did}
    if status:
        where.append("status = %(status)s")
        params["status"] = status
    else:
        # Default excludes archived.
        where.append("status <> 'archived'")
    if kind:
        where.append("kind = %(kind)s")
        params["kind"] = kind

    rows = _dict_query(f"""
        SELECT vertex_id, project_did, slug, title, kind, status,
               intake_count, last_intake_at, created_at
          FROM vertex_manimani_project
         WHERE {' AND '.join(where)}
         ORDER BY COALESCE(last_intake_at, created_at) DESC
         LIMIT {int(limit)}
        """,
        params,
    )
    return [dict(r) for r in (rows or [])]


def list_active_intake_count_for_projects(
    *,
    actor_did: str,
    org_did: str,
) -> dict[str, int]:
    """Per-project intake count from ``mv_manimani_project_active``.

    Aggregates the day-bucketed MV across all kinds within last 30d.
    Returns an empty dict in dry-run mode.
    """

    if _dry_run():
        return {}

    rows = _dict_query("""
        SELECT project_vertex_id, SUM(intake_count) AS cnt30d
          FROM mv_manimani_project_active
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
         GROUP BY project_vertex_id
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    out: dict[str, int] = {}
    for r in rows or []:
        try:
            out[str(r["project_vertex_id"])] = int(r["cnt30d"] or 0)
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ── coverage aggregates ──────────────────────────────────────────────


def coverage_snapshot(
    *,
    actor_did: str,
    org_did: str,
    window_days: int,
) -> dict[str, Any]:
    """Single Hyperdrive read pass that fills ``ai.gftd.apps.manimani.coverage``.

    Dry-run mode returns deterministic zeros so unit tests stay stable.
    """

    if _dry_run():
        return {
            "intakes": 0, "intakes24h": 0, "projects": 0,
            "projectsByKind": {}, "projectsByStatus": {},
            "artifacts": 0, "artifactsByKind": {},
            "runs": 0, "runsByStatus": {},
            "unroutedCount": 0,
        }

    cutoff_ms = int((time.time() - window_days * 86400) * 1000)
    cutoff_24h_ms = int((time.time() - 86400) * 1000)

    out: dict[str, Any] = {}
    # intake counters
    rows = _dict_query("""
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN ts_ms >= %(c24h)s THEN 1 ELSE 0 END) AS last_24h
          FROM vertex_manimani_intake
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND ts_ms >= %(cutoff)s
        """,
        {
            "actor_did": actor_did, "org_did": org_did,
            "cutoff": cutoff_ms, "c24h": cutoff_24h_ms,
        "today": _today_str(), },
    )
    r = (rows or [{}])[0]
    out["intakes"] = int(r.get("total") or 0)
    out["intakes24h"] = int(r.get("last_24h") or 0)

    # projects by kind / status
    rows = _dict_query("""
        SELECT kind, status, COUNT(*) AS cnt
          FROM vertex_manimani_project
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
         GROUP BY kind, status
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    by_kind: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total_projects = 0
    for row in rows or []:
        cnt = int(row.get("cnt") or 0)
        total_projects += cnt
        k = str(row.get("kind") or "unknown")
        s = str(row.get("status") or "unknown")
        by_kind[k] = by_kind.get(k, 0) + cnt
        by_status[s] = by_status.get(s, 0) + cnt
    out["projects"] = total_projects
    out["projectsByKind"] = by_kind
    out["projectsByStatus"] = by_status

    # artifacts by kind
    rows = _dict_query("""
        SELECT artifact_kind, COUNT(*) AS cnt
          FROM vertex_manimani_artifact
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND ts_ms >= %(cutoff)s
         GROUP BY artifact_kind
        """,
        {"actor_did": actor_did, "org_did": org_did, "cutoff": cutoff_ms, "today": _today_str(), },
    )
    akind: dict[str, int] = {}
    total_art = 0
    for row in rows or []:
        cnt = int(row.get("cnt") or 0)
        akind[str(row.get("artifact_kind") or "unknown")] = cnt
        total_art += cnt
    out["artifacts"] = total_art
    out["artifactsByKind"] = akind

    # runs by status
    rows = _dict_query("""
        SELECT status, COUNT(*) AS cnt
          FROM vertex_manimani_run
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
        GROUP BY status
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    rstatus: dict[str, int] = {}
    total_runs = 0
    for row in rows or []:
        cnt = int(row.get("cnt") or 0)
        rstatus[str(row.get("status") or "unknown")] = cnt
        total_runs += cnt
    out["runs"] = total_runs
    out["runsByStatus"] = rstatus

    # unrouted (artifacts in mv_manimani_intake_unrouted scope)
    rows = _dict_query("""
        SELECT COUNT(*) AS cnt
          FROM mv_manimani_intake_unrouted
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    r2 = (rows or [{}])[0]
    out["unroutedCount"] = int(r2.get("cnt") or 0)
    return out


# ── classify (re-classification) ─────────────────────────────────────


def demote_primary_edges_for_intake(
    *,
    intake_vertex_id: str,
    actor_did: str,
    org_did: str,
) -> int:
    """Set ``is_primary=false`` on every prior primary edge for this intake.

    Returns the number of edges demoted (best-effort; RisingWave does not
    expose ``rowcount`` for ``UPDATE`` reliably, so the count is the
    pre-update SELECT). Dry-run returns 0.
    """

    if _dry_run():
        return 0

    rows = _dict_query("""
        SELECT edge_id FROM edge_manimani_belongs_to
         WHERE src_vid = %(intake)s
           AND actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND is_primary = true
        """,
        {"intake": intake_vertex_id, "actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    edges = [str(r["edge_id"]) for r in (rows or []) if r.get("edge_id")]
    if not edges:
        return 0
    # RisingWave UPDATE on edge tables: delete-then-insert pattern is
    # safer than UPDATE because edges are immutable in Iceberg cold
    # tier. Phase 2 keeps a soft demote (UPDATE), Phase 3 swaps to
    # the canonical delete+insert.
    for eid in edges:
        _exec("""
            UPDATE edge_manimani_belongs_to
               SET is_primary = false
             WHERE edge_id = %(edge_id)s
            """,
            {"edge_id": eid},
        )
    return len(edges)


# ── writes ───────────────────────────────────────────────────────────


def insert_intake(
    *,
    intake_vertex_id: str,
    source_kind: str,
    raw_text: Optional[str],
    source_uri: Optional[str],
    parsed_text: Optional[str],
    lang: Optional[str],
    sensitivity_ord: int,
    byte_size: Optional[int],
    ts_ms: int,
    actor_did: str,
    org_did: str,
) -> None:
    if _dry_run():
        return

    now_iso = _utc_now_iso()
    _exec(f"""
        INSERT INTO vertex_manimani_intake (
            vertex_id, _seq, created_date, sensitivity_ord, owner_did,
            source_kind, raw_text, source_uri, parsed_text,
            lang, byte_size, ts_ms,
            actor_did, org_did, at_did, created_at)
        VALUES (
            %(vertex_id)s, NULL, '{_today_str()}', %(sensitivity_ord)s, %(actor_did)s,
            %(source_kind)s, %(raw_text)s, %(source_uri)s, %(parsed_text)s,
            %(lang)s, %(byte_size)s, %(ts_ms)s,
            %(actor_did)s, %(org_did)s, NULL, %(created_at)s)
        """,
        {
            "vertex_id": intake_vertex_id,
            "sensitivity_ord": sensitivity_ord,
            "actor_did": actor_did,
            "source_kind": source_kind,
            "raw_text": raw_text,
            "source_uri": source_uri,
            "parsed_text": parsed_text,
            "lang": lang,
            "byte_size": byte_size,
            "ts_ms": ts_ms,
            "org_did": org_did,
            "created_at": now_iso,
        "today": _today_str(), },
    )


def insert_run(
    *,
    run_vertex_id: str,
    run_id: str,
    intake_vertex_id: str,
    project_vertex_id: Optional[str],
    status: str,
    started_at: str,
    actor_did: str,
    org_did: str,
) -> None:
    if _dry_run():
        return

    _exec(f"""
        INSERT INTO vertex_manimani_run (
            vertex_id, _seq, created_date, sensitivity_ord, owner_did,
            run_id, thread_id,
            intake_vertex_id, project_vertex_id,
            status, current_node, checkpoint_json, error_text,
            started_at, finished_at, cost_jpy_micro,
            llm_tokens_in, llm_tokens_out,
            classifier_model_id, processor_model_id,
            actor_did, org_did, at_did, created_at)
        VALUES (
            %(vertex_id)s, NULL, '{_today_str()}', 2, %(actor_did)s,
            %(run_id)s, %(run_id)s,
            %(intake_vertex_id)s, %(project_vertex_id)s,
            %(status)s, NULL, NULL, NULL,
            %(started_at)s, NULL, NULL,
            NULL, NULL,
            NULL, NULL,
            %(actor_did)s, %(org_did)s, NULL, %(started_at)s)
        """,
        {
            "vertex_id": run_vertex_id,
            "run_id": run_id,
            "intake_vertex_id": intake_vertex_id,
            "project_vertex_id": project_vertex_id,
            "status": status,
            "started_at": started_at,
            "actor_did": actor_did,
            "org_did": org_did,
        "today": _today_str(), },
    )


def update_run_status(
    *,
    run_vertex_id: str,
    actor_did: str,
    org_did: str,
    status: str,
    current_node: Optional[str] = None,
    error_text: Optional[str] = None,
    finished_at: Optional[str] = None,
    project_vertex_id: Optional[str] = None,
    llm_tokens_in: Optional[int] = None,
    llm_tokens_out: Optional[int] = None,
    cost_jpy_micro: Optional[int] = None,
) -> None:
    """Phase 5: persist run status into ``vertex_manimani_run`` so
    cross-pod ``GET /runs/{id}`` and ``resumeRun`` can read it.

    RisingWave does not support ``ON CONFLICT … UPDATE`` cleanly, and
    transactional UPDATE on PK is the canonical anti-pattern (see
    ADR-2604241342 §rw-no-onconflict). We do a delete-then-insert in a
    single sync_cursor block. Pre-existing fields (run_id / thread_id /
    intake_vertex_id / started_at) are read from the row first so we
    don't lose them on the rewrite.
    """

    if _dry_run():
        return

    now_iso = _utc_now_iso()
    rows = _dict_query("""
        SELECT vertex_id, run_id, thread_id, intake_vertex_id, project_vertex_id,
               status, current_node, checkpoint_json, error_text,
               started_at, finished_at, cost_jpy_micro,
               llm_tokens_in, llm_tokens_out,
               classifier_model_id, processor_model_id,
               actor_did, org_did, at_did, created_at
          FROM vertex_manimani_run
         WHERE vertex_id = %(vid)s
           AND actor_did = %(actor_did)s
           AND org_did = %(org_did)s
         LIMIT 1
        """,
        {"vid": run_vertex_id, "actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    if not rows:
        return  # nothing to update — caller likely missed insert_run
    prev = dict(rows[0])

    _exec("DELETE FROM vertex_manimani_run WHERE vertex_id = %(vid)s",
        {"vid": run_vertex_id},
    )

    merged_project_vid = (
        project_vertex_id if project_vertex_id is not None else prev.get("project_vertex_id")
    )
    merged_current_node = current_node if current_node is not None else prev.get("current_node")
    merged_error_text = error_text if error_text is not None else prev.get("error_text")
    merged_finished_at = finished_at if finished_at is not None else prev.get("finished_at")
    merged_tokens_in = llm_tokens_in if llm_tokens_in is not None else prev.get("llm_tokens_in")
    merged_tokens_out = llm_tokens_out if llm_tokens_out is not None else prev.get("llm_tokens_out")
    merged_cost = cost_jpy_micro if cost_jpy_micro is not None else prev.get("cost_jpy_micro")

    _exec(f"""
        INSERT INTO vertex_manimani_run (
            vertex_id, _seq, created_date, sensitivity_ord, owner_did,
            run_id, thread_id,
            intake_vertex_id, project_vertex_id,
            status, current_node, checkpoint_json, error_text,
            started_at, finished_at, cost_jpy_micro,
            llm_tokens_in, llm_tokens_out,
            classifier_model_id, processor_model_id,
            actor_did, org_did, at_did, created_at)
        VALUES (
            %(vid)s, NULL, '{_today_str()}', 2, %(actor_did)s,
            %(run_id)s, %(thread_id)s,
            %(intake_vid)s, %(project_vid)s,
            %(status)s, %(current_node)s, %(checkpoint_json)s, %(error_text)s,
            %(started_at)s, %(finished_at)s, %(cost)s,
            %(tokens_in)s, %(tokens_out)s,
            %(classifier_mid)s, %(processor_mid)s,
            %(actor_did)s, %(org_did)s, %(at_did)s, %(created_at)s)
        """,
        {
            "vid": run_vertex_id,
            "actor_did": actor_did,
            "run_id": prev.get("run_id"),
            "thread_id": prev.get("thread_id"),
            "intake_vid": prev.get("intake_vertex_id"),
            "project_vid": merged_project_vid,
            "status": status,
            "current_node": merged_current_node,
            "checkpoint_json": prev.get("checkpoint_json"),
            "error_text": merged_error_text,
            "started_at": prev.get("started_at"),
            "finished_at": merged_finished_at,
            "cost": merged_cost,
            "tokens_in": merged_tokens_in,
            "tokens_out": merged_tokens_out,
            "classifier_mid": prev.get("classifier_model_id"),
            "processor_mid": prev.get("processor_model_id"),
            "org_did": org_did,
            "at_did": prev.get("at_did"),
            "created_at": prev.get("created_at") or now_iso,
        "today": _today_str(), },
    )


# Backward-compat alias for any caller that still imports the old name.
upsert_run_status = update_run_status


def list_pending_runs(
    *,
    actor_did: str,
    org_did: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """SELECT runs at the HITL gate (status='interrupted'), newest first.

    Returned rows are joined with pendingClassification at the server
    layer (server._load_run_cross_pod hydrates from checkpoint chain).
    Returns ``[]`` in dry-run mode.
    """

    if _dry_run():
        return []

    rows = _dict_query(f"""
        SELECT vertex_id, run_id, thread_id, intake_vertex_id,
               project_vertex_id, status, current_node, error_text,
               started_at, finished_at
          FROM vertex_manimani_run
         WHERE actor_did = %(actor_did)s
           AND org_did = %(org_did)s
           AND status = 'interrupted'
         ORDER BY started_at DESC
         LIMIT {int(limit)}
        """,
        {"actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    return [dict(r) for r in (rows or [])]


def get_run_record(
    *,
    run_id: str,
    actor_did: str,
    org_did: str,
) -> Optional[dict[str, Any]]:
    """SELECT a single run by ``run_id`` (NOT ``vertex_id``) — used by
    ``GET /runs/{run_id}`` cross-pod fallback and ``resumeRun`` lookup."""

    if _dry_run():
        return None

    rows = _dict_query("""
        SELECT vertex_id, run_id, thread_id, intake_vertex_id,
               project_vertex_id, status, current_node, error_text,
               started_at, finished_at,
               classifier_model_id, processor_model_id
          FROM vertex_manimani_run
         WHERE run_id = %(run_id)s
           AND actor_did = %(actor_did)s
           AND org_did = %(org_did)s
         LIMIT 1
        """,
        {"run_id": run_id, "actor_did": actor_did, "org_did": org_did, "today": _today_str(), },
    )
    if not rows:
        return None
    return dict(rows[0])


def insert_project(
    *,
    project_vertex_id: str,
    project_did: str,
    slug: str,
    title: str,
    kind: str,
    initial_tags_csv: Optional[str],
    ts_ms: int,
    actor_did: str,
    org_did: str,
) -> None:
    if _dry_run():
        return

    now_iso = _utc_now_iso()
    _exec(f"""
        INSERT INTO vertex_manimani_project (
            vertex_id, _seq, created_date, sensitivity_ord, owner_did,
            project_did, slug, title, kind, initial_tags_csv,
            posterior, intake_count, last_intake_at, status,
            ts_ms, actor_did, org_did, at_did, created_at)
        VALUES (
            %(vertex_id)s, NULL, '{_today_str()}', 2, %(actor_did)s,
            %(project_did)s, %(slug)s, %(title)s, %(kind)s, %(initial_tags_csv)s,
            NULL, 0, %(now_iso)s, 'active',
            %(ts_ms)s, %(actor_did)s, %(org_did)s, NULL, %(now_iso)s)
        """,
        {
            "vertex_id": project_vertex_id,
            "project_did": project_did,
            "slug": slug,
            "title": title,
            "kind": kind,
            "initial_tags_csv": initial_tags_csv,
            "ts_ms": ts_ms,
            "actor_did": actor_did,
            "org_did": org_did,
            "now_iso": now_iso,
        "today": _today_str(), },
    )


def insert_artifacts(*, artifacts: Iterable[Artifact], actor_did: str, org_did: str) -> None:
    if _dry_run():
        return

    now_iso = _utc_now_iso()
    for a in artifacts:
        _exec(f"""
            INSERT INTO vertex_manimani_artifact (
                vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                intake_vertex_id, project_vertex_id, run_vertex_id,
                artifact_kind, content, model_id,
                tokens_in, tokens_out, error_text,
                ts_ms, actor_did, org_did, at_did, created_at)
            VALUES (
                %(vertex_id)s, NULL, '{_today_str()}', 2, %(actor_did)s,
                %(intake_vertex_id)s, %(project_vertex_id)s, %(run_vertex_id)s,
                %(artifact_kind)s, %(content)s, %(model_id)s,
                %(tokens_in)s, %(tokens_out)s, %(error_text)s,
                %(ts_ms)s, %(actor_did)s, %(org_did)s, NULL, %(created_at)s)
            """,
            {
                "vertex_id": a.vertex_id,
                "actor_did": actor_did,
                "intake_vertex_id": a.intake_vertex_id,
                "project_vertex_id": a.project_vertex_id,
                "run_vertex_id": a.run_vertex_id,
                "artifact_kind": a.artifact_kind.value,
                "content": a.content,
                "model_id": a.model_id,
                "tokens_in": a.tokens_in,
                "tokens_out": a.tokens_out,
                "error_text": a.error_text,
                "ts_ms": a.ts_ms,
                "org_did": org_did,
                "created_at": now_iso,
            "today": _today_str(), },
        )


def insert_belongs_to_edge(
    *,
    intake_vertex_id: str,
    project_vertex_id: str,
    confidence: float,
    is_primary: bool,
    classification_method: str,
    actor_did: str,
    org_did: str,
) -> str:
    """Insert one ``edge_manimani_belongs_to`` row. Returns the edge_id.

    Phase 1: each intake gets exactly one primary edge (created here);
    re-classification (Phase 2) demotes the prior primary to ``is_primary=false``
    and inserts a new primary.
    """

    edge_id = f"{intake_vertex_id}|{project_vertex_id}"
    if _dry_run():
        return edge_id

    now_iso = _utc_now_iso()
    _exec(f"""
        INSERT INTO edge_manimani_belongs_to (
            edge_id, src_vid, dst_vid, _seq, created_date,
            sensitivity_ord, owner_did,
            confidence, is_primary, classification_method,
            created_at, org_did, actor_did)
        VALUES (
            %(edge_id)s, %(src_vid)s, %(dst_vid)s, NULL, '{_today_str()}',
            2, %(actor_did)s,
            %(confidence)s, %(is_primary)s, %(classification_method)s,
            %(created_at)s, %(org_did)s, %(actor_did)s)
        """,
        {
            "edge_id": edge_id,
            "src_vid": intake_vertex_id,
            "dst_vid": project_vertex_id,
            "actor_did": actor_did,
            "confidence": confidence,
            "is_primary": is_primary,
            "classification_method": classification_method,
            "created_at": now_iso,
            "org_did": org_did,
        "today": _today_str(), },
    )
    return edge_id
