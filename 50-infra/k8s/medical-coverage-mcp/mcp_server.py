#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
import secrets
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


NAMESPACE = os.environ.get("NAMESPACE", "risingwave")
CRONJOB_NAME = os.environ.get("CRONJOB_NAME", "medical-coverage-ingester")
APP_LABEL = os.environ.get("APP_LABEL", "medical-coverage-ingester")
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "")
PORT = int(os.environ.get("PORT", "8080"))

TARGETS = {
    "pubmed": ("gakujutsu_ronbun", "com.etzhayyim.apps.iryo.pubmedPaper"),
    "clinical_trials": ("rinshou_shiken", "com.etzhayyim.apps.iryo.rinshou"),
    "dsm": ("dsm_shikkan", "com.etzhayyim.apps.iryo.dsmCategory"),
    "facilities": ("iryo_shisetsu", "com.etzhayyim.apps.iryo.shisetsu"),
    "facilities_csv": ("iryo_shisetsu", "com.etzhayyim.apps.iryo.shisetsu"),
}

READ_ONLY_TOOLS = {
    "medical.coverage.get",
    "medical.targets.list",
    "medical.ingest.status",
    "medical.ingest.logs",
    "medical.ingest.reconcile",
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "medical.coverage.get",
        "description": "Read medical domain coverage from RisingWave.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {"type": "array", "items": {"type": "string"}},
                "includeRows": {"type": "boolean"},
            },
        },
    },
    {
        "name": "medical.targets.list",
        "description": "List configured medical coverage target mappings.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "medical.ingest.trigger",
        "description": "Create a one-shot Kubernetes Job from the medical coverage CronJob.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {"type": "array", "items": {"type": "string"}},
                "maxRecords": {"type": "integer"},
                "pubmedTerm": {"type": "string"},
                "requestedBy": {"type": "string"},
                "idempotencyKey": {"type": "string"},
                "dryRun": {"type": "boolean"},
            },
        },
    },
    {
        "name": "medical.ingest.status",
        "description": "Read status for medical coverage ingest Jobs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jobName": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "medical.ingest.logs",
        "description": "Return bounded logs for a medical coverage ingest Job.",
        "inputSchema": {
            "type": "object",
            "required": ["jobName"],
            "properties": {
                "jobName": {"type": "string"},
                "tailLines": {"type": "integer"},
            },
        },
    },
    {
        "name": "medical.ingest.pause",
        "description": "Suspend the medical coverage CronJob.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "requestedBy": {"type": "string"},
            },
        },
    },
    {
        "name": "medical.ingest.resume",
        "description": "Unsuspend the medical coverage CronJob.",
        "inputSchema": {
            "type": "object",
            "properties": {"requestedBy": {"type": "string"}},
        },
    },
    {
        "name": "medical.ingest.reconcile",
        "description": "Check live Kubernetes and RisingWave state for the medical ingester.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "medical.ingest.configure",
        "description": "Patch approved medical ingester Secret keys such as FACILITY_CSV_URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "facilityCsvUrl": {"type": "string"},
                "facilitySourceLabel": {"type": "string"},
            },
        },
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_label(value: str, max_len: int = 63) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())[:max_len].strip("-.")
    return cleaned or "unknown"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def text_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


def load_k8s() -> tuple[Any, Any]:
    from kubernetes import client, config

    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    cfg = client.Configuration.get_default_copy()
    if os.environ.get("K8S_VERIFY_SSL", "false").lower() in {"0", "false", "no"}:
        # VKE service-account CA projection can be rejected by the Python
        # client/certifi stack even though kubectl works in the same cluster.
        # This server only talks to the in-cluster Kubernetes service and is
        # constrained by namespace-scoped RBAC, so default to disabling client
        # certificate verification unless explicitly overridden.
        cfg.verify_ssl = False
    client.Configuration.set_default(cfg)
    return client.BatchV1Api(), client.CoreV1Api()


def rw_rows(sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if not RW_DSN:
        raise RuntimeError("RW_DSN is not configured")
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(RW_DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return list(cur.fetchall() or [])


def selected_collections(args: dict[str, Any]) -> list[str]:
    requested = args.get("targets")
    names = requested if isinstance(requested, list) else list(TARGETS)
    collections: list[str] = []
    for name in names:
        key = str(name)
        if key not in TARGETS:
            raise ValueError(f"unknown target: {key}")
        collection = TARGETS[key][1]
        if collection not in collections:
            collections.append(collection)
    return collections


def get_coverage(args: dict[str, Any]) -> dict[str, Any]:
    collections = selected_collections(args)
    placeholders = ",".join(["%s"] * len(collections))
    rows = rw_rows(
        f"""
        SELECT domain, app_host, collection, world_total, unit, sector,
               did_count, record_count, collected, coverage_rate
          FROM mv_world_collection_coverage_live
         WHERE collection IN ({placeholders})
         ORDER BY collection
        """,
        tuple(collections),
    )
    by_collection = {v[1]: k for k, v in TARGETS.items()}
    coverage = []
    for row in rows:
        coverage.append(
            {
                "target": by_collection.get(row["collection"], row["collection"]),
                "domain": row["domain"],
                "collection": row["collection"],
                "recordCount": row["record_count"],
                "collected": row["collected"],
                "worldTotal": row["world_total"],
                "coverageRate": row["coverage_rate"],
                "unit": row["unit"],
                "sector": row["sector"],
            }
        )
    return {"ok": True, "coverage": coverage}


def list_targets(_: dict[str, Any]) -> dict[str, Any]:
    collections = sorted({v[1] for v in TARGETS.values()})
    placeholders = ",".join(["%s"] * len(collections))
    rows = rw_rows(
        f"""
        SELECT domain, app_host, collection, world_total, unit, sector
          FROM dim_world_domain_collection
         WHERE collection IN ({placeholders})
         ORDER BY collection
        """,
        tuple(collections),
    )
    return {"ok": True, "targets": rows}


def list_jobs(batch: Any, label_selector: str, limit: int) -> list[Any]:
    jobs = batch.list_namespaced_job(NAMESPACE, label_selector=label_selector).items
    jobs.sort(key=lambda j: j.metadata.creation_timestamp or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return jobs[:limit]


def job_to_dict(job: Any) -> dict[str, Any]:
    status = job.status
    return {
        "name": job.metadata.name,
        "namespace": job.metadata.namespace,
        "active": status.active or 0,
        "succeeded": status.succeeded or 0,
        "failed": status.failed or 0,
        "startTime": status.start_time.isoformat() if status.start_time else None,
        "completionTime": status.completion_time.isoformat() if status.completion_time else None,
        "labels": job.metadata.labels or {},
    }


def pods_for_job(core: Any, job_name: str) -> list[Any]:
    return core.list_namespaced_pod(NAMESPACE, label_selector=f"job-name={job_name}").items


def pod_to_dict(pod: Any) -> dict[str, Any]:
    reason = None
    for st in pod.status.container_statuses or []:
        if st.state and st.state.waiting:
            reason = st.state.waiting.reason
        elif st.state and st.state.terminated:
            reason = st.state.terminated.reason
    return {
        "name": pod.metadata.name,
        "phase": pod.status.phase,
        "node": pod.spec.node_name,
        "podIP": pod.status.pod_ip,
        "reason": reason,
    }


def status(args: dict[str, Any]) -> dict[str, Any]:
    batch, core = load_k8s()
    job_name = str(args.get("jobName") or "").strip()
    if job_name:
        job = batch.read_namespaced_job(job_name, NAMESPACE)
        if (job.metadata.labels or {}).get("app.kubernetes.io/name") != APP_LABEL:
            raise PermissionError("job is not a medical coverage ingester job")
        return {
            "ok": True,
            "jobs": [job_to_dict(job)],
            "pods": [pod_to_dict(p) for p in pods_for_job(core, job_name)],
        }
    limit = max(1, min(int(args.get("limit") or 10), 50))
    jobs = list_jobs(batch, f"app.kubernetes.io/name={APP_LABEL}", limit)
    return {"ok": True, "jobs": [job_to_dict(j) for j in jobs]}


def trigger(args: dict[str, Any]) -> dict[str, Any]:
    batch, _ = load_k8s()
    targets_arg = args.get("targets")
    targets = [str(t) for t in targets_arg] if isinstance(targets_arg, list) else ["pubmed", "clinical_trials", "dsm", "facilities_csv"]
    for target in targets:
        if target not in TARGETS:
            raise ValueError(f"unknown target: {target}")
    idempotency_key = str(args.get("idempotencyKey") or "").strip()
    if idempotency_key:
        existing = list_jobs(batch, f"app.kubernetes.io/name={APP_LABEL},ai.etzhayyim.com/idempotency-key={clean_label(idempotency_key)}", 1)
        if existing:
            return {"ok": True, "jobName": existing[0].metadata.name, "namespace": NAMESPACE, "existing": True}

    cron = batch.read_namespaced_cron_job(CRONJOB_NAME, NAMESPACE)
    job_spec = cron.spec.job_template.spec
    template = job_spec.template
    template.metadata.labels = template.metadata.labels or {}
    template.metadata.labels["app.kubernetes.io/name"] = APP_LABEL

    for container in template.spec.containers:
        if container.name != "ingester":
            continue
        env = container.env or []
        env_by_name = {e.name: e for e in env}
        from kubernetes import client

        def set_env(name: str, value: str) -> None:
            if name in env_by_name:
                env_by_name[name].value = value
                env_by_name[name].value_from = None
            else:
                env.append(client.V1EnvVar(name=name, value=value))

        set_env("TARGETS", ",".join(targets))
        if "maxRecords" in args:
            set_env("MAX_RECORDS_PER_RUN", str(max(1, min(int(args["maxRecords"]), 100000))))
        if isinstance(args.get("pubmedTerm"), str) and args["pubmedTerm"].strip():
            set_env("PUBMED_TERM", args["pubmedTerm"].strip())
        container.env = env

    if bool(args.get("dryRun")):
        return {"ok": True, "dryRun": True, "targets": targets}

    from kubernetes import client

    suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    job_name = f"medical-coverage-manual-{suffix}-{secrets.token_hex(2)}"
    labels = {
        "app.kubernetes.io/name": APP_LABEL,
        "ai.etzhayyim.com/requested-by": clean_label(str(args.get("requestedBy") or "mcp")),
        "ai.etzhayyim.com/targets": clean_label("-".join(targets)),
        "ai.etzhayyim.com/run-kind": "manual",
    }
    if idempotency_key:
        labels["ai.etzhayyim.com/idempotency-key"] = clean_label(idempotency_key)

    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace=NAMESPACE, labels=labels),
        spec=job_spec,
    )
    job.spec.selector = None
    job.spec.template.metadata.labels.update(labels)
    created = batch.create_namespaced_job(NAMESPACE, job)
    return {"ok": True, "jobName": created.metadata.name, "namespace": NAMESPACE}


def logs(args: dict[str, Any]) -> dict[str, Any]:
    _, core = load_k8s()
    job_name = str(args.get("jobName") or "").strip()
    if not job_name:
        raise ValueError("jobName is required")
    batch, _ = load_k8s()
    job = batch.read_namespaced_job(job_name, NAMESPACE)
    if (job.metadata.labels or {}).get("app.kubernetes.io/name") != APP_LABEL:
        raise PermissionError("job is not a medical coverage ingester job")
    tail_lines = max(1, min(int(args.get("tailLines") or 200), 1000))
    out = []
    for pod in pods_for_job(core, job_name):
        body = core.read_namespaced_pod_log(pod.metadata.name, NAMESPACE, tail_lines=tail_lines)
        out.append({"pod": pod.metadata.name, "log": redact(body)})
    return {"ok": True, "logs": out}


def redact(text: str) -> str:
    patterns = ["RW_DSN", "NCBI_API_KEY", "FACILITY_CSV_URL", "MCP_AUTH_TOKEN"]
    redacted = text
    for key in patterns:
        redacted = re.sub(rf"({key}=)[^\s]+", rf"\1[redacted]", redacted)
    return redacted


def patch_cron_suspend(suspend: bool, args: dict[str, Any]) -> dict[str, Any]:
    batch, _ = load_k8s()
    now = utc_now()
    annotations = {
        f"ai.etzhayyim.com/{'paused' if suspend else 'resumed'}-by": str(args.get("requestedBy") or "mcp"),
        f"ai.etzhayyim.com/{'paused' if suspend else 'resumed'}-at": now,
    }
    if suspend and args.get("reason"):
        annotations["ai.etzhayyim.com/pause-reason"] = str(args["reason"])[:200]
    body = {"metadata": {"annotations": annotations}, "spec": {"suspend": suspend}}
    cron = batch.patch_namespaced_cron_job(CRONJOB_NAME, NAMESPACE, body)
    return {"ok": True, "cronJob": cron.metadata.name, "suspend": cron.spec.suspend}


def configure(args: dict[str, Any]) -> dict[str, Any]:
    _, core = load_k8s()
    string_data: dict[str, str] = {}
    if isinstance(args.get("facilityCsvUrl"), str):
        string_data["FACILITY_CSV_URL"] = args["facilityCsvUrl"].strip()
    if isinstance(args.get("facilitySourceLabel"), str):
        string_data["FACILITY_SOURCE_LABEL"] = args["facilitySourceLabel"].strip()
    if not string_data:
        raise ValueError("no approved config keys supplied")
    body = {"stringData": string_data}
    core.patch_namespaced_secret("medical-coverage-ingester-secrets", NAMESPACE, body)
    return {"ok": True, "updatedKeys": sorted(string_data)}


def reconcile(_: dict[str, Any]) -> dict[str, Any]:
    batch, core = load_k8s()
    checks: list[dict[str, Any]] = []
    try:
        cron = batch.read_namespaced_cron_job(CRONJOB_NAME, NAMESPACE)
        checks.append({"name": "cronjob_exists", "ok": True})
        checks.append({"name": "cronjob_not_suspended", "ok": not bool(cron.spec.suspend)})
        pull_names = [s.name for s in (cron.spec.job_template.spec.template.spec.image_pull_secrets or [])]
        checks.append({"name": "ghcr_pull_secret_attached", "ok": "ghcr-pull" in pull_names})
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "cronjob_exists", "ok": False, "error": str(e)})
    for secret_name in ("medical-coverage-ingester-secrets", "ghcr-pull"):
        try:
            core.read_namespaced_secret(secret_name, NAMESPACE)
            checks.append({"name": f"secret_{secret_name}_exists", "ok": True})
        except Exception as e:  # noqa: BLE001
            checks.append({"name": f"secret_{secret_name}_exists", "ok": False, "error": str(e)})
    try:
        coverage = get_coverage({})
        checks.append({"name": "coverage_rows_visible", "ok": len(coverage["coverage"]) >= 4, "count": len(coverage["coverage"])})
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "coverage_rows_visible", "ok": False, "error": str(e)})
    try:
        jobs = list_jobs(batch, f"app.kubernetes.io/name={APP_LABEL}", 1)
        checks.append({"name": "recent_job_exists", "ok": bool(jobs)})
        if jobs:
            checks.append({"name": "recent_job_succeeded", "ok": bool(jobs[0].status.succeeded)})
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "recent_job_exists", "ok": False, "error": str(e)})
    return {"ok": all(c.get("ok") for c in checks), "checks": checks}


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "medical.coverage.get":
        return get_coverage(args)
    if name == "medical.targets.list":
        return list_targets(args)
    if name == "medical.ingest.trigger":
        return trigger(args)
    if name == "medical.ingest.status":
        return status(args)
    if name == "medical.ingest.logs":
        return logs(args)
    if name == "medical.ingest.pause":
        return patch_cron_suspend(True, args)
    if name == "medical.ingest.resume":
        return patch_cron_suspend(False, args)
    if name == "medical.ingest.reconcile":
        return reconcile(args)
    if name == "medical.ingest.configure":
        return configure(args)
    raise ValueError(f"unknown tool: {name}")


class Handler(BaseHTTPRequestHandler):
    server_version = "medical-coverage-mcp/0.1"

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.add_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self.write_json({"status": "ok", "server": "medical-coverage-mcp"})
            return
        if self.path == "/mcp":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.add_common_headers()
            self.end_headers()
            self.wfile.write(b": ping\n\n")
            return
        self.write_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        if self.path != "/mcp":
            self.write_json({"error": "not found"}, status=404)
            return
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length).decode("utf-8")
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            self.write_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "invalid JSON"}})
            return
        response = self.handle_rpc(msg)
        if response is None:
            self.send_response(204)
            self.add_common_headers()
            self.end_headers()
            return
        self.write_json(response)

    def handle_rpc(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        rpc_id = msg.get("id")
        method = msg.get("method")
        if msg.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32600, "message": "malformed request"}}
        if rpc_id is None and "id" not in msg:
            return None
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "medical-coverage-mcp", "version": "0.1.0"},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": TOOLS}}
        if method != "tools/call":
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": f"method not found: {method}"}}

        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        name = str(params.get("name") or "")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if not name:
            return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "params.name is required"}}
        if not self.authorized(name):
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result({"ok": False, "error": "unauthorized"}, is_error=True)}
        try:
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result(call_tool(name, args))}
        except Exception as e:  # noqa: BLE001
            return {"jsonrpc": "2.0", "id": rpc_id, "result": text_result({"ok": False, "error": str(e)}, is_error=True)}

    def authorized(self, tool_name: str) -> bool:
        if not MCP_AUTH_TOKEN:
            return True
        auth = self.headers.get("Authorization") or ""
        return auth == f"Bearer {MCP_AUTH_TOKEN}" or tool_name in READ_ONLY_TOOLS

    def add_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization,Mcp-Session-Id")

    def write_json(self, payload: Any, status: int = 200) -> None:
        body = json_dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.add_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (utc_now(), fmt % args))


def main() -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"medical-coverage-mcp listening on :{PORT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
