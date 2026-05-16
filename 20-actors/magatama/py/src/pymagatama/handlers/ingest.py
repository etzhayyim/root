"""Cross-domain ingest control handlers.

These handlers are the XRPC/MCP-facing control surface for the durable ingest
spine. Source-specific acquisition remains in `pymagatama.ingest.*` workers.
"""

from __future__ import annotations

import json
from typing import Any

from pymagatama import udf
from pymagatama.db_sync import sync_cursor
from pymagatama.ingest.core import IngestRun, mark_run_finished, upsert_run
from pymagatama.ingest.zeebe import start_process_if_configured


_BPMN_BY_FAMILY_SOURCE = {
    ("houbun", "egov-jpn"): "ingest_houbun_egov_jpn_delta",
    ("houbun", "govinfo-cfr"): "ingest_houbun_govinfo_cfr",
    ("houbun", "eurlex"): "ingest_houbun_eurlex",
    ("houbun", "un-treaty"): "ingest_houbun_un_treaty",
    ("contracts", "constitute-project"): "ingest_contracts_constitute_project",
    ("contracts", "un-treaty"): "ingest_contracts_un_treaty",
    ("domain", "common-crawl"): "ingest_domain_common_crawl",
    ("site", "common-crawl"): "ingest_site_common_crawl_delta",
    ("patent", "uspto-patentsview"): "ingest_patent_uspto_patentsview",
    ("blockchain", "bitcoin-mainnet"): "blockchain_bitcoin_head_delta",
    ("blockchain", "ethereum-mainnet"): "blockchain_ethereum_head_delta",
}

_TARGETS_BY_FAMILY = {
    "houbun": ["vertex_houbun_statute", "vertex_houbun_article", "edge_houbun_statute_article"],
    "contracts": ["vertex_contracts_social_contract", "vertex_houbun_treaty"],
    "domain": ["vertex_page", "vertex_wet_chunk", "vertex_collection_job", "vertex_collector_run"],
    "site": ["vertex_page", "vertex_wet_chunk", "vertex_wat", "vertex_screenshot", "vertex_collection_job"],
    "maps": ["vertex_maps_job"],
    "patent": ["vertex_open_patent_patent", "edge_open_patent_citation_pair", "vertex_patent_blob"],
    "workspace": ["vertex_workspace_sync_job", "vertex_workspace_cursor", "vertex_workspace_raw_event"],
    "media": ["vertex_repo_commit"],
    "talent": ["vertex_job_posting", "vertex_occupation"],
    "blockchain": ["vertex_blockchain_block", "vertex_blockchain_tx"],
}


def _loads(params_json: str) -> dict[str, Any]:
    if not params_json:
        return {}
    data = json.loads(params_json)
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _require_str(params: dict[str, Any], key: str) -> str:
    value = str(params.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _mode(params: dict[str, Any], default: str = "delta") -> str:
    mode = str(params.get("mode") or default).strip().lower()
    if mode not in {"delta", "backfill", "repair", "verify"}:
        raise ValueError("mode must be one of delta, backfill, repair, verify")
    return mode


def _run_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    keys = [
        "runVertexId",
        "runId",
        "ingestFamily",
        "sourceId",
        "mode",
        "status",
        "zeebeProcessInstanceKey",
        "bpmnProcessId",
        "startedAt",
        "finishedAt",
        "recordsRead",
        "recordsWritten",
        "recordsSkipped",
        "errorCount",
        "lastError",
        "inputJson",
        "outputJson",
    ]
    return {k: v for k, v in zip(keys, row)}


def _plan_payload(params: dict[str, Any]) -> dict[str, Any]:
    family = _require_str(params, "ingestFamily")
    source_id = _require_str(params, "sourceId")
    mode = _mode(params)
    bpmn_process_id = _BPMN_BY_FAMILY_SOURCE.get((family, source_id)) or f"ingest_{family}_{source_id}".replace("-", "_")
    targets = _TARGETS_BY_FAMILY.get(family, [])
    limit = params.get("limit")
    estimated_records = int(limit) if isinstance(limit, int) and limit > 0 else 0
    estimated_shards = 1 if estimated_records <= 0 else max(1, min(1000, (estimated_records + 999) // 1000))
    return {
        "ok": True,
        "ingestFamily": family,
        "sourceId": source_id,
        "mode": mode,
        "bpmnProcessId": bpmn_process_id,
        "estimatedShards": estimated_shards,
        "estimatedRecords": estimated_records,
        "targets": targets,
        "planJson": json.dumps(
            {
                "range": params.get("range"),
                "limit": params.get("limit"),
                "inputJson": params.get("inputJson"),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    }


@udf(
    nsid="ai.gftd.apps.ingest.plan",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "plan", "mcp"),
    agent_tool="Dry-run a durable ingest plan without mutating graph rows.",
)
def ingest_plan(params_json: str) -> str:
    try:
        return _dump(_plan_payload(_loads(params_json)))
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e)})


@udf(
    nsid="ai.gftd.apps.ingest.start",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "start", "mcp"),
    agent_tool="Create a durable ingest run row. Zeebe launch is handled by the scheduler/dispatcher layer.",
)
def ingest_start(params_json: str) -> str:
    try:
        params = _loads(params_json)
        plan = _plan_payload(params)
        if bool(params.get("dryRun")):
            return _dump({**plan, "dryRun": True})
        run = IngestRun(
            ingest_family=plan["ingestFamily"],
            source_id=plan["sourceId"],
            mode=plan["mode"],
            status="planned",
            bpmn_process_id=plan["bpmnProcessId"],
            requested_by=str(params.get("requestedBy") or "mcp"),
            input_json=str(params.get("inputJson") or params.get("range") or ""),
        ).with_run_id()
        vid = upsert_run(run)
        variables = {
            "runId": run.run_id,
            "runVertexId": vid,
            "ingestFamily": run.ingest_family,
            "sourceId": run.source_id,
            "mode": run.mode,
            "inputJson": run.input_json or "",
            "requestedBy": run.requested_by or "mcp",
        }
        instance_key, zeebe_error = start_process_if_configured(run.bpmn_process_id or "", variables)
        if instance_key:
            run = IngestRun(
                ingest_family=run.ingest_family,
                source_id=run.source_id,
                mode=run.mode,
                run_id=run.run_id,
                status="running",
                zeebe_process_instance_key=instance_key,
                bpmn_process_id=run.bpmn_process_id,
                requested_by=run.requested_by,
                input_json=run.input_json,
            )
            upsert_run(run)
        return _dump(
            {
                "ok": True,
                "runId": run.run_id,
                "runVertexId": vid,
                "status": run.status,
                "bpmnProcessId": run.bpmn_process_id,
                "zeebeProcessInstanceKey": instance_key,
                "zeebeError": zeebe_error,
            }
        )
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e)})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "error": f"ingest.start failed: {e}"})


@udf(
    nsid="ai.gftd.apps.ingest.backfill",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "backfill", "mcp"),
    agent_tool="Create a bounded durable backfill run with an explicit range.",
)
def ingest_backfill(params_json: str) -> str:
    try:
        params = _loads(params_json)
        if not str(params.get("range") or "").strip():
            raise ValueError("range is required for backfill")
        params["mode"] = "backfill"
        return ingest_start(json.dumps(params))
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e)})


@udf(
    nsid="ai.gftd.apps.ingest.status",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "status", "mcp"),
    agent_tool="Read durable ingest run status from vertex_ingest_run.",
)
def ingest_status(params_json: str) -> str:
    try:
        params = _loads(params_json)
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e), "runs": []})

    clauses: list[str] = []
    args: list[Any] = []
    for column, key in (
        ("run_id", "runId"),
        ("ingest_family", "ingestFamily"),
        ("source_id", "sourceId"),
        ("status", "status"),
    ):
        value = params.get(key)
        if value:
            clauses.append(f"{column} = %s")
            args.append(str(value))
    limit = max(1, min(int(params.get("limit") or 20), 100))
    sql_text = """
        SELECT vertex_id, run_id, ingest_family, source_id, mode, status,
               zeebe_process_instance_key, bpmn_process_id, started_at, finished_at,
               records_read, records_written, records_skipped, error_count,
               last_error, input_json, output_json
          FROM vertex_ingest_run
    """
    if clauses:
        sql_text += " WHERE " + " AND ".join(clauses)
    sql_text += f" ORDER BY started_at DESC LIMIT {int(limit)}"
    try:
        with sync_cursor() as cur:
            cur.execute(sql_text, tuple(args))
            rows = cur.fetchall() or []
        return _dump({"ok": True, "runs": [_run_dict(r) for r in rows]})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "error": f"ingest.status failed: {e}", "runs": []})


def _update_run_status(params: dict[str, Any], status: str) -> int:
    clauses: list[str] = []
    args: list[Any] = [status]
    for column, key in (("run_id", "runId"), ("ingest_family", "ingestFamily"), ("source_id", "sourceId")):
        value = params.get(key)
        if value:
            clauses.append(f"{column} = %s")
            args.append(str(value))
    if not clauses:
        raise ValueError("runId or ingestFamily/sourceId is required")
    sql_text = "UPDATE vertex_ingest_run SET status = %s, updated_at = to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"') WHERE " + " AND ".join(clauses)
    with sync_cursor() as cur:
        cur.execute(sql_text, tuple(args))
        return int(cur.rowcount or 0)


@udf(
    nsid="ai.gftd.apps.ingest.pause",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "pause", "mcp"),
    agent_tool="Pause durable ingest runs by runId or family/source.",
)
def ingest_pause(params_json: str) -> str:
    try:
        params = _loads(params_json)
        count = _update_run_status(params, "paused")
        return _dump({"ok": True, "paused": count})
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e), "paused": 0})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "error": f"ingest.pause failed: {e}", "paused": 0})


@udf(
    nsid="ai.gftd.apps.ingest.resume",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "resume", "mcp"),
    agent_tool="Resume paused durable ingest runs by runId or family/source.",
)
def ingest_resume(params_json: str) -> str:
    try:
        params = _loads(params_json)
        count = _update_run_status(params, "planned")
        return _dump({"ok": True, "resumed": count})
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e), "resumed": 0})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "error": f"ingest.resume failed: {e}", "resumed": 0})


@udf(
    nsid="ai.gftd.apps.ingest.validate",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("ingest", "validate", "mcp"),
    agent_tool="Validate ingest run visibility and cursor/artifact counts.",
)
def ingest_validate(params_json: str) -> str:
    try:
        params = _loads(params_json)
        run_id = str(params.get("runId") or "").strip()
        family = str(params.get("ingestFamily") or "").strip()
        source_id = str(params.get("sourceId") or "").strip()
        checks: list[dict[str, Any]] = []
        status = "ok"
        with sync_cursor() as cur:
            if run_id:
                cur.execute("SELECT COUNT(*) FROM vertex_ingest_run WHERE run_id = %s", (run_id,))
                run_count = int((cur.fetchone() or [0])[0])
                checks.append({"name": "run_visible", "ok": run_count == 1, "count": run_count})
                cur.execute("SELECT COUNT(*) FROM vertex_ingest_artifact WHERE run_id = %s", (run_id,))
                artifact_count = int((cur.fetchone() or [0])[0])
                checks.append({"name": "artifacts_visible", "ok": True, "count": artifact_count})
            if family and source_id:
                cur.execute(
                    "SELECT COUNT(*) FROM vertex_ingest_cursor WHERE ingest_family = %s AND source_id = %s",
                    (family, source_id),
                )
                cursor_count = int((cur.fetchone() or [0])[0])
                checks.append({"name": "cursors_visible", "ok": True, "count": cursor_count})
        if any(not c.get("ok") for c in checks):
            status = "failed"
        return _dump({"ok": status == "ok", "status": status, "checks": checks})
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "status": "failed", "checks": [], "error": str(e)})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "status": "failed", "checks": [], "error": f"ingest.validate failed: {e}"})


@udf(
    nsid="ai.gftd.apps.coverage.refresh",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("coverage", "refresh", "mcp"),
    agent_tool="Record a coverage refresh request for post-ingest reconciliation.",
)
def coverage_refresh(params_json: str) -> str:
    try:
        params = _loads(params_json)
        family = str(params.get("coverageFamily") or "world").strip()
        run_id = str(params.get("runId") or "").strip()
        if run_id:
            mark_run_finished(run_id, status="completed", output={"coverageFamily": family, "refreshRequested": True})
        return _dump({"ok": True, "coverageFamily": family, "status": "requested"})
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "status": "failed", "error": str(e)})
    except Exception as e:  # noqa: BLE001
        return _dump({"ok": False, "status": "failed", "error": f"coverage.refresh failed: {e}"})
