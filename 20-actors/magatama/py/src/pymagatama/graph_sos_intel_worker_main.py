"""
Zeebe worker for the graph-sos-intel actor (ADR-2605071700).

Subscribes to 6 BPMN job types:
  com.etzhayyim.apps.graphSosIntel.inventoryCatalog  – R/PT15M: snapshot RisingWave topology
  com.etzhayyim.apps.graphSosIntel.writeSnapshot     – persist snapshot + relation rows
  com.etzhayyim.apps.graphSosIntel.detectFindings    – compare snapshots, emit findings
  com.etzhayyim.apps.graphSosIntel.queryLatestSnapshot – fetch latest snapshot for briefing
  com.etzhayyim.apps.graphSosIntel.generateBriefing  – LLM-driven briefing text
  com.etzhayyim.apps.graphSosIntel.writeFinding      – persist finding row

Run:
  python -m pymagatama.graph_sos_intel_worker_main

Env:
  AGENTGATEWAY_MCP_URL    — LangServer AgentGateway URL (default 127.0.0.1:8080)
  RW_URL           — RisingWave postgres URL
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from typing import Any

from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

from pymagatama.db_sync import fetch_all, fetch_one, sync_cursor
from pymagatama.local_agent_env import load_env_file, load_keychain_secret

LOG = logging.getLogger("graph_sos_intel_worker")

ACTOR_DID = "did:web:graph-sos-intel.etzhayyim.com"

# ─── helpers ──────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gen_id(prefix: str = "snap") -> str:
    import hashlib
    import time
    ts = str(time.time_ns())
    digest = hashlib.sha256(ts.encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ─── inventoryCatalog ─────────────────────────────────────────────────────


async def task_inventory_catalog(**_kwargs: Any) -> dict[str, Any]:
    """Query information_schema to build a topology catalog snapshot."""
    observed_at = _now()

    relations = await asyncio.to_thread(
        fetch_all,
        """
        SELECT table_schema, table_name, table_type, is_insertable_into
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name NOT LIKE 'rw_%'
        ORDER BY table_name
        """,
    )

    indexes = await asyncio.to_thread(
        fetch_all,
        """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
        """,
    )

    vertex_tables = [r for r in relations if r[1].startswith("vertex_")]
    edge_tables = [r for r in relations if r[1].startswith("edge_")]
    mv_tables = [r for r in relations if r[2] == "MATERIALIZED VIEW"]
    idx_count = len(indexes)

    LOG.info(
        "inventoryCatalog: %d vertex / %d edge / %d mv / %d idx",
        len(vertex_tables), len(edge_tables), len(mv_tables), idx_count,
    )

    return {
        "observedAt": observed_at,
        "relationTotal": len(relations),
        "vertexTableCount": len(vertex_tables),
        "edgeTableCount": len(edge_tables),
        "mvCount": len(mv_tables),
        "idxCount": idx_count,
        "relations": [
            {"schema": r[0], "name": r[1], "kind": r[2], "insertable": r[3]}
            for r in relations
        ],
        "indexes": [
            {"schema": r[0], "table": r[1], "name": r[2], "def": r[3]}
            for r in indexes
        ],
    }


# ─── writeSnapshot ────────────────────────────────────────────────────────


async def task_write_snapshot(
    observedAt: str = "",
    relationTotal: int = 0,
    vertexTableCount: int = 0,
    edgeTableCount: int = 0,
    mvCount: int = 0,
    idxCount: int = 0,
    relations: list | None = None,
    indexes: list | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Persist snapshot + relation/index inventory rows."""
    snapshot_id = _gen_id("snap")
    vertex_id = f"at://{ACTOR_DID}/com.etzhayyim.apps.graphSosIntel.snapshot/{snapshot_id}"
    created_at = _now()

    def _write() -> None:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_graph_sos_intel_snapshot
                  (vertex_id, snapshot_id, actor_did, scope, status,
                   relation_total, vertex_table_count, edge_table_count,
                   mv_count, idx_count, anomaly_count,
                   stale_relation_count, heavy_ddl_pending_count,
                   summary, recommendation_json, evidence_json,
                   created_at, updated_at, owner_did,
                   org_id, user_id, actor_id, sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    vertex_id, snapshot_id, ACTOR_DID, "public", "active",
                    relationTotal, vertexTableCount, edgeTableCount,
                    mvCount, idxCount, 0, 0, 0,
                    f"Topology snapshot {snapshot_id}: {relationTotal} relations",
                    json.dumps({}), json.dumps({"observedAt": observedAt}),
                    created_at, created_at, ACTOR_DID,
                    "etzhayyim", "graph-sos-intel", "gs0s1nt7", 0,
                ),
            )

        if relations:
            with sync_cursor() as cur:
                for rel in relations[:500]:
                    rel_vid = (
                        f"at://{ACTOR_DID}/com.etzhayyim.apps.graphSosIntel.relation"
                        f"/{snapshot_id}:{rel['name']}"
                    )
                    cur.execute(
                        """
                        INSERT INTO vertex_graph_sos_relation_inventory
                          (vertex_id, schema_name, relation_name, relation_kind,
                           table_type, is_insertable_into, observed_at,
                           owner_did, sensitivity_ord)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            rel_vid, rel.get("schema", "public"),
                            rel["name"], rel.get("kind", ""),
                            rel.get("kind", ""), rel.get("insertable", "NO"),
                            observedAt, ACTOR_DID, 0,
                        ),
                    )

        if indexes:
            with sync_cursor() as cur:
                for idx in indexes[:500]:
                    idx_vid = (
                        f"at://{ACTOR_DID}/com.etzhayyim.apps.graphSosIntel.index"
                        f"/{snapshot_id}:{idx['name']}"
                    )
                    cur.execute(
                        """
                        INSERT INTO vertex_graph_sos_index_inventory
                          (vertex_id, schema_name, table_name, index_name,
                           index_def, observed_at, owner_did, sensitivity_ord)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT DO NOTHING
                        """,
                        (
                            idx_vid, idx.get("schema", "public"),
                            idx.get("table", ""), idx["name"],
                            idx.get("def", ""), observedAt, ACTOR_DID, 0,
                        ),
                    )

    await asyncio.to_thread(_write)
    LOG.info("writeSnapshot: persisted %s", snapshot_id)
    return {"snapshotId": snapshot_id, "vertexId": vertex_id}


# ─── detectFindings ───────────────────────────────────────────────────────


async def task_detect_findings(
    snapshotId: str = "",
    vertexTableCount: int = 0,
    edgeTableCount: int = 0,
    mvCount: int = 0,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Compare with previous snapshot and emit findings for anomalies."""
    prev = await asyncio.to_thread(
        fetch_one,
        """
        SELECT snapshot_id, vertex_table_count, edge_table_count, mv_count
        FROM vertex_graph_sos_intel_snapshot
        WHERE snapshot_id != %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (snapshotId,),
    )

    findings: list[dict[str, Any]] = []
    created_at = _now()

    def _check_delta(label: str, curr: int, prev_val: int, threshold: int = 5) -> None:
        delta = abs(curr - prev_val)
        if delta >= threshold:
            fid = _gen_id("fnd")
            findings.append({
                "finding_id": fid,
                "finding_kind": "table_count_delta",
                "severity": "warning" if delta < 20 else "critical",
                "affected_relation": label,
                "affected_relation_kind": "vertex_table" if "vertex" in label else label,
                "summary": f"{label} count changed by {delta} (prev={prev_val}, curr={curr})",
                "evidence_json": json.dumps({"prev": prev_val, "curr": curr, "delta": delta}),
                "recommendation": "Investigate DDL migration backlog",
                "recommended_action_kind": "investigate",
            })

    if prev:
        _, prev_v, prev_e, prev_m = prev
        _check_delta("vertex_table", vertexTableCount, prev_v or 0)
        _check_delta("edge_table", edgeTableCount, prev_e or 0)
        _check_delta("materialized_view", mvCount, prev_m or 0)

    if findings:
        def _write_findings() -> None:
            with sync_cursor() as cur:
                for f in findings:
                    fid = f["finding_id"]
                    vid = f"at://{ACTOR_DID}/com.etzhayyim.apps.graphSosIntel.finding/{fid}"
                    cur.execute(
                        """
                        INSERT INTO vertex_graph_sos_intel_finding
                          (vertex_id, finding_id, actor_did, finding_kind,
                           severity, status, affected_relation,
                           affected_relation_kind, summary, evidence_json,
                           recommendation, recommended_action_kind,
                           ddl_request_ref, created_at, updated_at,
                           owner_did, org_id, user_id, actor_id, sensitivity_ord)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            vid, fid, ACTOR_DID,
                            f["finding_kind"], f["severity"], "open",
                            f["affected_relation"], f["affected_relation_kind"],
                            f["summary"], f["evidence_json"],
                            f["recommendation"], f["recommended_action_kind"],
                            snapshotId, created_at, created_at,
                            ACTOR_DID, "etzhayyim", "graph-sos-intel", "gs0s1nt7", 0,
                        ),
                    )

        await asyncio.to_thread(_write_findings)

    LOG.info("detectFindings: %d finding(s) for snapshot %s", len(findings), snapshotId)
    return {"findingCount": len(findings), "findings": [f["finding_id"] for f in findings]}


# ─── queryLatestSnapshot ──────────────────────────────────────────────────


async def task_query_latest_snapshot(**_kwargs: Any) -> dict[str, Any]:
    """Return the most recent snapshot for the briefing task."""
    row = await asyncio.to_thread(
        fetch_one,
        """
        SELECT snapshot_id, relation_total, vertex_table_count,
               edge_table_count, mv_count, idx_count,
               anomaly_count, created_at
        FROM vertex_graph_sos_intel_snapshot
        ORDER BY created_at DESC
        LIMIT 1
        """,
    )
    if not row:
        return {"snapshotFound": False}

    sid, rt, vtc, etc, mvc, ic, ac, cat = row
    return {
        "snapshotFound": True,
        "snapshotId": sid,
        "relationTotal": rt,
        "vertexTableCount": vtc,
        "edgeTableCount": etc,
        "mvCount": mvc,
        "idxCount": ic,
        "anomalyCount": ac,
        "snapshotCreatedAt": str(cat),
    }


# ─── generateBriefing ─────────────────────────────────────────────────────


async def task_generate_briefing(
    snapshotFound: bool = False,
    snapshotId: str = "",
    relationTotal: int = 0,
    vertexTableCount: int = 0,
    edgeTableCount: int = 0,
    mvCount: int = 0,
    idxCount: int = 0,
    anomalyCount: int = 0,
    snapshotCreatedAt: str = "",
    **_kwargs: Any,
) -> dict[str, Any]:
    """LLM-driven briefing summarizing the latest topology snapshot."""
    from pymagatama import llm

    if not snapshotFound:
        return {
            "briefingText": "No topology snapshot available yet.",
            "severity": "info",
        }

    user_prompt = (
        f"Graph SoS Intel topology briefing — snapshot {snapshotId} @ {snapshotCreatedAt}.\n"
        f"Stats: {relationTotal} relations total "
        f"({vertexTableCount} vertex tables, {edgeTableCount} edge tables, "
        f"{mvCount} MVs, {idxCount} indexes). "
        f"Anomalies detected: {anomalyCount}.\n"
        "Write a concise 3-sentence operational briefing for a system reliability engineer. "
        "Include the counts, highlight any anomaly count > 0, and recommend next action if needed."
    )

    result = await asyncio.to_thread(
        llm.call_tier,
        "fast",
        "You are a graph database observability assistant. Respond in plain English.",
        user_prompt,
        max_tokens=200,
    )

    briefing_text = (result.get("content") or "").strip()
    severity = "warning" if anomalyCount > 0 else "info"

    LOG.info("generateBriefing: snapshot=%s anomalies=%d", snapshotId, anomalyCount)
    return {
        "briefingText": briefing_text,
        "severity": severity,
        "snapshotId": snapshotId,
    }


# ─── writeFinding ─────────────────────────────────────────────────────────


async def task_write_finding(
    briefingText: str = "",
    severity: str = "info",
    snapshotId: str = "",
    **_kwargs: Any,
) -> dict[str, Any]:
    """Persist a briefing-derived finding row."""
    if not briefingText:
        return {"written": False, "reason": "empty briefing"}

    fid = _gen_id("fnd")
    vid = f"at://{ACTOR_DID}/com.etzhayyim.apps.graphSosIntel.finding/{fid}"
    created_at = _now()

    def _write() -> None:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_graph_sos_intel_finding
                  (vertex_id, finding_id, actor_did, finding_kind,
                   severity, status, affected_relation,
                   affected_relation_kind, summary, evidence_json,
                   recommendation, recommended_action_kind,
                   ddl_request_ref, created_at, updated_at,
                   owner_did, org_id, user_id, actor_id, sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    vid, fid, ACTOR_DID, "briefing",
                    severity, "open", "graph_topology", "snapshot",
                    briefingText[:1000], json.dumps({"snapshotId": snapshotId}),
                    "Review latest snapshot findings", "review",
                    snapshotId, created_at, created_at,
                    ACTOR_DID, "etzhayyim", "graph-sos-intel", "gs0s1nt7", 0,
                ),
            )

    await asyncio.to_thread(_write)
    LOG.info("writeFinding: %s (severity=%s)", fid, severity)
    return {"written": True, "findingId": fid, "vertexId": vid}


# ─── worker entrypoint ────────────────────────────────────────────────────


async def run_worker() -> None:
    gateway = os.environ.get("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    channel = create_langserver_channel(grpc_address=gateway)
    worker = LangServerWorker(channel)
    timeout_ms = int(os.environ.get("GRAPH_SOS_INTEL_TASK_TIMEOUT_MS", "120000"))

    registrations = {
        "com.etzhayyim.apps.graphSosIntel.inventoryCatalog": task_inventory_catalog,
        "com.etzhayyim.apps.graphSosIntel.writeSnapshot": task_write_snapshot,
        "com.etzhayyim.apps.graphSosIntel.detectFindings": task_detect_findings,
        "com.etzhayyim.apps.graphSosIntel.queryLatestSnapshot": task_query_latest_snapshot,
        "com.etzhayyim.apps.graphSosIntel.generateBriefing": task_generate_briefing,
        "com.etzhayyim.apps.graphSosIntel.writeFinding": task_write_finding,
    }
    for task_type, fn in registrations.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(fn)

    LOG.info(
        "graph-sos-intel zeebe worker registered %d task types via %s",
        len(registrations), gateway,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    task = asyncio.create_task(worker.work())
    await stop.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def main() -> None:
    load_env_file()
    if not os.environ.get("RW_URL"):
        rw_url = load_keychain_secret(service="etzhayyim.rw", account="ROOT_URL")
        if rw_url:
            os.environ["RW_URL"] = rw_url
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    os.environ.setdefault("RW_SYNC_POOL", "0")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
