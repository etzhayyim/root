#!/usr/bin/env python3
"""
Medical coverage ingester.

Writes canonical healthcare records into vertex_medical and loops by cursor
until mv_world_collection_coverage_live reports coverage_rate >= 1.0 for each
configured target.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import boto3
import psycopg2
import psycopg2.extras
import requests


REPO = "did:web:iryo.etzhayyim.com"
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "50"))
MAX_RECORDS_PER_RUN = int(os.environ.get("MAX_RECORDS_PER_RUN", "5000"))
DEADLINE_SECONDS = int(os.environ.get("DEADLINE_SECONDS", "1320"))
RW_DML_RETRIES = int(os.environ.get("RW_DML_RETRIES", "5"))
RW_RETRY_BASE_SECONDS = float(os.environ.get("RW_RETRY_BASE_SECONDS", "2"))
RW_DML_RATE_LIMIT = int(os.environ.get("RW_DML_RATE_LIMIT", "25"))
RW_DEGRADED_DML_RATE_LIMIT = int(os.environ.get("RW_DEGRADED_DML_RATE_LIMIT", "5"))
RW_STATEMENT_TIMEOUT_SECONDS = int(os.environ.get("RW_STATEMENT_TIMEOUT_SECONDS", "20"))
RW_HEALTH_GATE = (
    os.environ.get("RW_HEALTH_GATE", "true").lower() not in ("0", "false", "no")
    or os.environ.get("ALLOW_UNSAFE_RW_HEALTH_GATE_DISABLE", "").lower() not in ("1", "true", "yes")
)
RW_ALLOW_SINGLE_COMPUTE_RECOVERY = os.environ.get(
    "RW_ALLOW_SINGLE_COMPUTE_RECOVERY", ""
).lower() in ("1", "true", "yes")
RW_MIN_COMPUTE_READY_FLOOR = 1 if RW_ALLOW_SINGLE_COMPUTE_RECOVERY else 2
RW_MIN_COMPUTE_AGE_SECONDS_FLOOR = 0 if RW_ALLOW_SINGLE_COMPUTE_RECOVERY else 1800
RW_MIN_COMPUTE_READY = max(
    int(os.environ.get("RW_MIN_COMPUTE_READY", "2")),
    RW_MIN_COMPUTE_READY_FLOOR,
)
RW_MIN_COMPUTE_AGE_SECONDS = max(
    int(os.environ.get("RW_MIN_COMPUTE_AGE_SECONDS", "1800")),
    RW_MIN_COMPUTE_AGE_SECONDS_FLOOR,
)
RW_COLD_START_POLICY = os.environ.get("RW_COLD_START_POLICY", "degraded-write")
RW_SLOWDOWN_WINDOW_SECONDS = int(os.environ.get("RW_SLOWDOWN_WINDOW_SECONDS", "60"))
RW_SLOWDOWN_MAX = int(os.environ.get("RW_SLOWDOWN_MAX", "10"))
RW_SKIP_DELETE_BEFORE_INSERT = os.environ.get("RW_SKIP_DELETE_BEFORE_INSERT", "false").lower() in (
    "1",
    "true",
    "yes",
)
FACILITY_REPLAY_SKIP_COVERAGE = os.environ.get("FACILITY_REPLAY_SKIP_COVERAGE", "false").lower() in (
    "1",
    "true",
    "yes",
)
RW_COMPUTE_SELECTOR = os.environ.get("RW_COMPUTE_SELECTOR", "risingwave.risingwavelabs.com/component=compute")
RW_META_SELECTOR = os.environ.get("RW_META_SELECTOR", "risingwave.risingwavelabs.com/component=meta")
RW_NAMESPACE = os.environ.get("RW_NAMESPACE", "risingwave")
RW_IMPLICIT_FLUSH = os.environ.get("RW_IMPLICIT_FLUSH", "false").lower() in ("1", "true", "yes")
B2_BUCKET = os.environ.get("B2_BUCKET", "etzhayyim-nats")
B2_ENDPOINT = os.environ.get("B2_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
B2_REGION = os.environ.get("B2_REGION", "us-west-004")
B2_PREFIX = os.environ.get("B2_PREFIX", "medical-sources/iryo-shisetsu").strip("/")
FACILITY_RAW_ONLY = os.environ.get("FACILITY_RAW_ONLY", "false").lower() in ("1", "true", "yes")
FACILITY_REPLAY_FROM_B2 = os.environ.get("FACILITY_REPLAY_FROM_B2", "false").lower() in ("1", "true", "yes")
FACILITY_REPLAY_LEASE_TTL_SECONDS = int(os.environ.get("FACILITY_REPLAY_LEASE_TTL_SECONDS", "600"))
PUBMED_TERM = os.environ.get("PUBMED_TERM", "medicine[MeSH Terms] OR clinical medicine")
PUBMED_RETMAX = int(os.environ.get("PUBMED_RETMAX", "100"))
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")
K8S_TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
K8S_CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")

TARGETS = {
    "pubmed": {
        "domain": "gakujutsu_ronbun",
        "collection": "com.etzhayyim.apps.iryo.pubmedPaper",
    },
    "clinical_trials": {
        "domain": "rinshou_shiken",
        "collection": "com.etzhayyim.apps.iryo.rinshou",
    },
    "dsm": {
        "domain": "dsm_shikkan",
        "collection": "com.etzhayyim.apps.iryo.dsmCategory",
    },
    "facilities_csv": {
        "domain": "iryo_shisetsu",
        "collection": "com.etzhayyim.apps.iryo.shisetsu",
    },
}

FACILITY_SOURCES = [
    {
        "label": "cms-pos-clinical-labs",
        "kind": "cms-data-api",
        "url": "https://data.cms.gov/data-api/v1/dataset/d3eb38ac-d8e9-40d3-b7b7-6205d3d1dc16/data",
        "id_fields": ["CLIA_MDCR_NUM", "PRVDR_NUM", "CROSS_REF_PROVIDER_NUMBER", "FAC_NAME"],
        "name_fields": ["FAC_NAME", "ADDTNL_FAC_NAME"],
    },
    {
        "label": "cms-pos-iqies",
        "kind": "cms-data-api",
        "url": "https://data.cms.gov/data-api/v1/dataset/086e48c4-87a6-4be1-8823-29e8da8f225b/data",
        "id_fields": ["prvdr_num", "fac_name"],
        "name_fields": ["fac_name"],
    },
    {
        "label": "cms-pos-qies",
        "kind": "cms-data-api",
        "url": "https://data.cms.gov/data-api/v1/dataset/8ba0f9b4-9493-4aa0-9f82-44ea9468d1b5/data",
        "id_fields": ["prvdr_num", "fac_name"],
        "name_fields": ["fac_name"],
    },
]

DSM_CATEGORIES = [
    "Neurodevelopmental Disorders",
    "Schizophrenia Spectrum and Other Psychotic Disorders",
    "Bipolar and Related Disorders",
    "Depressive Disorders",
    "Anxiety Disorders",
    "Obsessive-Compulsive and Related Disorders",
    "Trauma- and Stressor-Related Disorders",
    "Dissociative Disorders",
    "Somatic Symptom and Related Disorders",
    "Feeding and Eating Disorders",
    "Elimination Disorders",
    "Sleep-Wake Disorders",
    "Sexual Dysfunctions",
    "Gender Dysphoria",
    "Disruptive, Impulse-Control, and Conduct Disorders",
    "Substance-Related and Addictive Disorders",
    "Neurocognitive Disorders",
    "Personality Disorders",
    "Paraphilic Disorders",
    "Medication-Induced Movement Disorders and Other Adverse Effects",
    "Other Conditions That May Be a Focus of Clinical Attention",
]

START = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - START:7.1f}s] {message}", flush=True)


def within_deadline() -> bool:
    return time.time() - START < DEADLINE_SECONDS


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ts_ms() -> int:
    return int(time.time() * 1000)


def retry_delay(attempt: int) -> float:
    return min(RW_RETRY_BASE_SECONDS * (2 ** attempt), 30.0)


def is_retryable_rw_error(exc: Exception) -> bool:
    message = str(exc).lower()
    needles = (
        "cluster recovery",
        "table reader closed",
        "batch service failed",
        "scheduler error",
        "internal error",
        "connection refused",
        "connection reset",
        "timeout",
    )
    return any(needle in message for needle in needles)


def make_rkey(seed: str) -> str:
    alphabet = "234567abcdefghijklmnopqrstuvwxyz"
    n = int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big")
    out = []
    for _ in range(13):
        out.append(alphabet[n & 0x1F])
        n >>= 5
    return "".join(reversed(out))


def make_cid(value_json: str) -> str:
    return "bafyreib" + hashlib.sha256(value_json.encode()).hexdigest()[:46]


def b2_client():
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        region_name=B2_REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )


def connect():
    dsn = os.environ.get("RW_DSN")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=os.environ.get("RW_HOST", "risingwave.risingwave.svc.cluster.local"),
        port=int(os.environ.get("RW_PORT", "4566")),
        dbname=os.environ.get("RW_DBNAME", "dev"),
        user=os.environ.get("RW_USER", "root"),
        password=os.environ.get("RW_PASS", ""),
    )


def parse_k8s_time(value: str) -> float:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def k8s_get(path: str, params: dict[str, Any] | None = None) -> requests.Response:
    host = os.environ.get("KUBERNETES_SERVICE_HOST")
    port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
    if not host or not K8S_TOKEN_PATH.exists():
        raise RuntimeError("Kubernetes API is unavailable")
    token = K8S_TOKEN_PATH.read_text(encoding="utf-8").strip()
    verify: str | bool = str(K8S_CA_PATH) if K8S_CA_PATH.exists() else True
    return requests.get(
        f"https://{host}:{port}{path}",
        params=params,
        headers={"Authorization": f"Bearer {token}"},
        verify=verify,
        timeout=10,
    )


def assert_rw_health_gate() -> str:
    if not RW_HEALTH_GATE:
        log("[rw-health] disabled by RW_HEALTH_GATE")
        return "normal"

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '5s'")
            cur.execute("SELECT 1")
            row = cur.fetchone()
            if not row or row[0] != 1:
                raise RuntimeError("SELECT 1 failed")
            cur.execute(
                """
                SELECT count(*)
                FROM rw_recovery_info
                WHERE recovery_state <> 'RUNNING' OR in_global_recovering
                """
            )
            bad_recovery = int(cur.fetchone()[0])
            if bad_recovery:
                raise RuntimeError(f"rw_recovery_info has {bad_recovery} recovering database(s)")

    pods_resp = k8s_get(
        f"/api/v1/namespaces/{RW_NAMESPACE}/pods",
        {"labelSelector": RW_COMPUTE_SELECTOR},
    )
    if pods_resp.status_code != 200:
        raise RuntimeError(f"Kubernetes pod probe failed: HTTP {pods_resp.status_code} {pods_resp.text[:256]}")
    pods = pods_resp.json().get("items", [])
    if not pods:
        raise RuntimeError(f"no compute pods found for selector {RW_COMPUTE_SELECTOR}")

    ready = 0
    youngest_age = 10**9
    not_running: list[str] = []
    now = time.time()
    for pod in pods:
        name = pod.get("metadata", {}).get("name", "?")
        phase = pod.get("status", {}).get("phase")
        statuses = pod.get("status", {}).get("containerStatuses") or []
        started_at = ""
        if statuses:
            started_at = statuses[0].get("state", {}).get("running", {}).get("startedAt", "")
        if phase != "Running" or not started_at:
            not_running.append(f"{name}:{phase}")
            continue
        ready += 1
        youngest_age = min(youngest_age, int(now - parse_k8s_time(started_at)))

    if ready < RW_MIN_COMPUTE_READY:
        raise RuntimeError(f"only {ready}/{RW_MIN_COMPUTE_READY} compute pods Running")
    if not_running:
        raise RuntimeError(f"compute pod(s) not Running: {', '.join(not_running)}")
    mode = "normal"
    if youngest_age < RW_MIN_COMPUTE_AGE_SECONDS:
        if RW_COLD_START_POLICY == "degraded-write":
            mode = "degraded"
        else:
            raise RuntimeError(
                f"youngest compute pod age {youngest_age}s < {RW_MIN_COMPUTE_AGE_SECONDS}s"
            )

    patterns = (
        "SlowDown",
        "RateLimited",
        "NoSuchUpload",
        "write part timeout",
        "cluster is under recovering",
        "DML is not permitted during cluster recovery",
    )
    meta_resp = k8s_get(
        f"/api/v1/namespaces/{RW_NAMESPACE}/pods",
        {"labelSelector": RW_META_SELECTOR},
    )
    if meta_resp.status_code != 200:
        raise RuntimeError(f"Kubernetes meta pod probe failed: HTTP {meta_resp.status_code} {meta_resp.text[:256]}")
    log_pods = pods + meta_resp.json().get("items", [])

    error_count = 0
    for pod in log_pods:
        name = pod.get("metadata", {}).get("name", "")
        if not name:
            continue
        log_resp = k8s_get(
            f"/api/v1/namespaces/{RW_NAMESPACE}/pods/{name}/log",
            {"sinceSeconds": str(RW_SLOWDOWN_WINDOW_SECONDS)},
        )
        if log_resp.status_code != 200:
            raise RuntimeError(f"Kubernetes log probe failed for {name}: HTTP {log_resp.status_code}")
        error_count += sum(1 for line in log_resp.text.splitlines() if any(p in line for p in patterns))
    if error_count >= RW_SLOWDOWN_MAX:
        raise RuntimeError(
            f"object-store/recovery errors {error_count} in {RW_SLOWDOWN_WINDOW_SECONDS}s"
        )
    if mode == "degraded":
        log(
            f"[rw-health] degraded-write ready={ready} youngest_age={youngest_age}s "
            f"log_errors={error_count}"
        )
    else:
        log(f"[rw-health] healthy ready={ready} youngest_age={youngest_age}s log_errors={error_count}")
    return mode


def get_cursor(conn, key: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT cursor_value
            FROM vertex_medical_coverage_cursor
            WHERE target_key = %s
            LIMIT 1
            """,
            (key,),
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return ""
    return str(row[0])


def set_cursor(conn, key: str, cursor_value: str, count: int, coverage: float, error: str | None = None) -> None:
    updated_at = now_iso()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM vertex_medical_coverage_cursor WHERE target_key = %s", (key,))
        cur.execute(
            """
            INSERT INTO vertex_medical_coverage_cursor (
              target_key, cursor_value, records_ingested, last_coverage_rate,
              last_error, updated_at, actor_did, org_did
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (key, cursor_value, count, coverage, error, updated_at, REPO, "anon"),
        )


def coverage_rate(conn, target: dict[str, str]) -> float:
    for attempt in range(RW_DML_RETRIES + 1):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT coverage_rate
                    FROM mv_world_collection_coverage_live
                    WHERE domain = %s AND collection = %s
                    """,
                    (target["domain"], target["collection"]),
                )
                row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else 0.0
        except Exception as exc:
            conn.rollback()
            if attempt >= RW_DML_RETRIES or not is_retryable_rw_error(exc):
                raise
            delay = retry_delay(attempt)
            log(f"[rw] coverage read retry {attempt + 1}/{RW_DML_RETRIES} after {delay:.1f}s: {exc}")
            time.sleep(delay)
    return 0.0


def record_tuple(collection: str, business_key: str, value: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, int, str]:
    rkey = make_rkey(f"{collection}:{business_key}")
    uri = f"at://{REPO}/{collection}/{rkey}"
    value.setdefault("$type", collection)
    value_json = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return (uri, make_cid(value_json), collection, rkey, REPO, value_json, now_iso(), ts_ms(), now_iso())


def medical_row(record: tuple[str, str, str, str, str, str, str, int, str]) -> tuple[Any, ...]:
    uri, _cid, collection, rkey, repo, value_json, indexed_at, _ts_ms, created_at = record
    try:
        value = json.loads(value_json)
    except Exception:
        value = {}
    source = str(value.get("source") or "")
    category = collection.rsplit(".", 1)[-1]
    code = str(
        value.get("pmid")
        or value.get("trialId")
        or value.get("facilityId")
        or value.get("categoryName")
        or rkey
    )


def medical_source_edge(record: tuple[str, str, str, str, str, str, str, int, str]) -> tuple[Any, ...]:
    uri, cid, collection, rkey, _repo, value_json, indexed_at, _ts_ms, _created_at = record
    try:
        value = json.loads(value_json)
    except Exception:
        value = {}
    source_id = str(value.get("source") or "unknown")
    edge_id = f"medical-source-record:{source_id}:{cid or rkey}"
    return (edge_id, source_id, uri, collection, "emits_record", indexed_at, indexed_at)
    name = str(
        value.get("title")
        or value.get("briefTitle")
        or value.get("officialTitle")
        or value.get("name")
        or value.get("categoryName")
        or code
        or ""
    )
    description = str(value.get("fullJournalName") or value.get("taxonomy") or value.get("overallStatus") or "")
    standard = {
        "com.etzhayyim.apps.iryo.pubmedPaper": "PubMed",
        "com.etzhayyim.apps.iryo.rinshou": "ClinicalTrials.gov",
        "com.etzhayyim.apps.iryo.dsmCategory": "DSM",
        "com.etzhayyim.apps.iryo.shisetsu": "Healthcare facility",
    }.get(collection, "medical")
    return (
        uri,
        None,
        created_at[:10],
        2,
        repo,
        rkey,
        repo,
        name[:256],
        uri,
        name[:1024],
        name[:1024],
        description[:4096],
        category,
        code[:512],
        standard,
        str(value.get("pubDate") or value.get("ingestedAt") or ""),
        value_json,
        collection,
        source,
        source,
        str(value.get("ingestedAt") or indexed_at),
        created_at,
        repo,
        "anon",
    )


def rec_get(rec: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in rec and rec[name] not in (None, "", "Not Available", "Not Applicable"):
            return rec[name]
    lower = {str(k).lower(): v for k, v in rec.items()}
    for name in names:
        value = lower.get(name.lower())
        if value not in (None, "", "Not Available", "Not Applicable"):
            return value
    return None


def datasource_tables_available(conn) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_name = 'vertex_medical_ingest_cursor'
                """
            )
            return int(cur.fetchone()[0]) > 0
    except Exception:
        conn.rollback()
        return False


def get_facility_cursor(conn) -> str:
    if datasource_tables_available(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cursor_json
                FROM vertex_medical_ingest_cursor
                WHERE vertex_id = 'medical-ingest-cursor:facilities_csv'
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row and row[0]:
                return str(row[0])
    return get_cursor(conn, "facilities_csv") or "0"


def upsert_facility_cursor(
    conn,
    cursor_json: str,
    source_id: str,
    offset: int,
    run_id: str | None,
    asset_id: str | None,
    b2_key: str | None,
    status: str,
    error: str | None = None,
) -> None:
    if not datasource_tables_available(conn):
        return
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM vertex_medical_ingest_cursor WHERE vertex_id = 'medical-ingest-cursor:facilities_csv'"
        )
        cur.execute(
            """
            INSERT INTO vertex_medical_ingest_cursor (
              vertex_id, source_id, target_collection, cursor_json, source_offset,
              last_run_id, last_asset_id, last_b2_key, last_success_at, status, error, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "medical-ingest-cursor:facilities_csv",
                source_id,
                TARGETS["facilities_csv"]["collection"],
                cursor_json,
                offset,
                run_id,
                asset_id,
                b2_key,
                now_iso() if status == "ok" else None,
                status,
                error,
                now_iso(),
            ),
        )


def upsert_facility_run(
    conn,
    run_id: str,
    source_id: str,
    status: str,
    started_at: str,
    records_fetched: int,
    records_inserted: int,
    source_offset: int,
    next_offset: int,
    b2_key: str | None,
    b2_bytes: int | None,
    checksum_sha256: str | None,
    error: str | None = None,
) -> None:
    if not datasource_tables_available(conn):
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM vertex_medical_ingest_run WHERE vertex_id = %s", (f"medical-ingest-run:{run_id}",))
        cur.execute(
            """
            INSERT INTO vertex_medical_ingest_run (
              vertex_id, run_id, source_id, target_collection, status, started_at, finished_at,
              records_fetched, records_inserted, source_offset, next_offset, b2_bucket,
              b2_key, b2_bytes, checksum_sha256, error, metadata_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"medical-ingest-run:{run_id}",
                run_id,
                source_id,
                TARGETS["facilities_csv"]["collection"],
                status,
                started_at,
                now_iso(),
                records_fetched,
                records_inserted,
                source_offset,
                next_offset,
                B2_BUCKET if b2_key else None,
                b2_key,
                b2_bytes,
                checksum_sha256,
                error,
                json.dumps({"worker": "medical-coverage-ingester"}, separators=(",", ":")),
            ),
        )


def upsert_facility_asset(
    conn,
    asset_id: str,
    source_id: str,
    run_id: str,
    b2_key: str,
    byte_size: int,
    checksum_sha256: str,
    source_url: str,
    record_count: int,
    source_offset: int,
) -> None:
    if not datasource_tables_available(conn):
        return
    with conn.cursor() as cur:
        cur.execute("DELETE FROM vertex_medical_source_asset WHERE vertex_id = %s", (f"medical-source-asset:{asset_id}",))
        cur.execute(
            """
            INSERT INTO vertex_medical_source_asset (
              vertex_id, asset_id, source_id, run_id, asset_role, media_type, format,
              b2_bucket, b2_key, byte_size, checksum_sha256, source_url,
              record_count, source_offset, metadata_json, status, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"medical-source-asset:{asset_id}",
                asset_id,
                source_id,
                run_id,
                "rawPage",
                "application/x-ndjson",
                "jsonl.gz",
                B2_BUCKET,
                b2_key,
                byte_size,
                checksum_sha256,
                source_url,
                record_count,
                source_offset,
                json.dumps({"contentEncoding": "gzip"}, separators=(",", ":")),
                "stored",
                now_iso(),
                now_iso(),
            ),
        )


def upload_facility_raw_page(source: dict[str, Any], offset: int, records: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    payload = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records).encode("utf-8")
    compressed = gzip.compress(payload, compresslevel=6)
    checksum = hashlib.sha256(compressed).hexdigest()
    day = dt.datetime.now(dt.UTC).strftime("%Y/%m/%d")
    key = f"{B2_PREFIX}/{source['label']}/{day}/{run_id}-offset-{offset}.jsonl.gz"
    b2_client().put_object(
        Bucket=B2_BUCKET,
        Key=key,
        Body=compressed,
        ContentType="application/x-ndjson",
        ContentEncoding="gzip",
        Metadata={
            "source-id": source["label"],
            "source-offset": str(offset),
            "record-count": str(len(records)),
            "sha256": checksum,
        },
    )
    return {"bucket": B2_BUCKET, "key": key, "bytes": len(compressed), "sha256": checksum}


def b2_json_get(key: str, default: dict[str, Any]) -> dict[str, Any]:
    try:
        obj = b2_client().get_object(Bucket=B2_BUCKET, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return default


def b2_json_put(key: str, value: dict[str, Any]) -> None:
    body = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b2_client().put_object(
        Bucket=B2_BUCKET,
        Key=key,
        Body=body,
        ContentType="application/json",
    )


def acquire_b2_lease(name: str, ttl_seconds: int = 600) -> tuple[str, str]:
    lease_key = f"{B2_PREFIX}/_leases/{name}.json"
    lease = b2_json_get(lease_key, {})
    now = time.time()
    expires_at = float(lease.get("expiresAtEpoch") or 0)
    if expires_at > now:
        raise RuntimeError(f"B2 lease held for {name} until {lease.get('expiresAt')}")
    owner = f"{name}-{int(now)}-{os.getpid()}"
    b2_json_put(
        lease_key,
        {
            "owner": owner,
            "acquiredAt": now_iso(),
            "expiresAt": dt.datetime.fromtimestamp(now + ttl_seconds, dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "expiresAtEpoch": now + ttl_seconds,
        },
    )
    return lease_key, owner


def release_b2_lease(lease_key: str, owner: str) -> None:
    lease = b2_json_get(lease_key, {})
    if lease.get("owner") == owner:
        b2_json_put(lease_key, {"owner": "", "releasedAt": now_iso(), "expiresAtEpoch": 0})


def fetch_facility_source_page(source: dict[str, Any], offset: int, limit: int) -> tuple[list[dict[str, Any]], str]:
    if source["kind"] == "cms-data-api":
        r = requests.get(source["url"], params={"size": limit, "offset": offset}, timeout=180)
        r.raise_for_status()
        return r.json(), r.url

    r = requests.get(source["url"], timeout=180)
    r.raise_for_status()
    text = r.text
    if source["url"].endswith(".jsonl"):
        parsed = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        parsed = list(csv.DictReader(io.StringIO(text)))
    return parsed[offset : offset + limit], r.url


def archive_facilities_raw_to_b2() -> int:
    lease_key, lease_owner = acquire_b2_lease("facilities_csv")
    try:
        return archive_facilities_raw_to_b2_locked()
    finally:
        release_b2_lease(lease_key, lease_owner)


def archive_facilities_raw_to_b2_locked() -> int:
    cursor_key = f"{B2_PREFIX}/_cursors/facilities_csv.json"
    cursor = b2_json_get(cursor_key, {"sourceIndex": 0, "offset": 0, "source": FACILITY_SOURCES[0]["label"]})
    source_index = int(cursor.get("sourceIndex", 0))
    offset = int(cursor.get("offset", 0))
    total = 0

    while total < MAX_RECORDS_PER_RUN and source_index < len(FACILITY_SOURCES):
        source = FACILITY_SOURCES[source_index]
        limit = MAX_RECORDS_PER_RUN - total
        records, source_url = fetch_facility_source_page(source, offset, limit)
        if not records:
            log(f"[facilities_raw] source complete label={source['label']} offset={offset}")
            source_index += 1
            offset = 0
            continue
        run_id = f"{source['label']}-{int(time.time())}-{offset}"
        b2_info = upload_facility_raw_page(source, offset, records, run_id)
        total += len(records)
        offset += len(records)
        next_cursor = {
            "sourceIndex": source_index,
            "offset": offset,
            "source": source["label"],
            "lastRunId": run_id,
            "lastSourceUrl": source_url,
            "lastB2Bucket": b2_info["bucket"],
            "lastB2Key": b2_info["key"],
            "lastRecordCount": len(records),
            "lastSha256": b2_info["sha256"],
            "updatedAt": now_iso(),
        }
        b2_json_put(cursor_key, next_cursor)
        log(f"[facilities_raw] archived source={source['label']} records={len(records)} nextOffset={offset} b2Key={b2_info['key']}")

    return total


def b2_list_facility_raw_keys() -> list[str]:
    keys: list[str] = []
    client = b2_client()
    token = None
    while True:
        kwargs: dict[str, Any] = {"Bucket": B2_BUCKET, "Prefix": f"{B2_PREFIX}/"}
        if token:
            kwargs["ContinuationToken"] = token
        page = client.list_objects_v2(**kwargs)
        for item in page.get("Contents", []):
            key = item.get("Key", "")
            if key.endswith(".jsonl.gz") and "/_cursors/" not in key:
                keys.append(key)
        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")
    return sorted(keys)


def source_for_b2_key(key: str) -> dict[str, Any]:
    for source in FACILITY_SOURCES:
        if f"/{source['label']}/" in key:
            return source
    return {
        "label": "facility-b2-raw",
        "id_fields": ["id", "facility_id", "provider_id", "ccn", "name", "hospital_name", "FAC_NAME"],
        "name_fields": ["name", "hospital_name", "facility_name", "FAC_NAME"],
    }


def load_b2_raw_records(key: str) -> list[dict[str, Any]]:
    obj = b2_client().get_object(Bucket=B2_BUCKET, Key=key)
    body = obj["Body"].read()
    text = gzip.decompress(body).decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def replay_facilities_from_b2(conn) -> int:
    lease_key, lease_owner = acquire_b2_lease("facilities_replay", FACILITY_REPLAY_LEASE_TTL_SECONDS)
    try:
        return replay_facilities_from_b2_locked(conn)
    finally:
        release_b2_lease(lease_key, lease_owner)


def replay_facilities_from_b2_locked(conn) -> int:
    cursor_key = f"{B2_PREFIX}/_cursors/facilities_replay.json"
    cursor = b2_json_get(cursor_key, {"key": "", "recordOffset": 0})
    current_key = str(cursor.get("key") or "")
    record_offset = int(cursor.get("recordOffset") or 0)
    keys = b2_list_facility_raw_keys()
    if not keys:
        log("[facilities_replay] no B2 raw objects found")
        return 0

    key = current_key if current_key in keys else ""
    if not key:
        key = keys[0]
        record_offset = 0
    rows = []
    processed_key = key
    source = source_for_b2_key(processed_key)
    records = load_b2_raw_records(processed_key)
    while len(rows) < MAX_RECORDS_PER_RUN:
        if record_offset >= len(records):
            next_keys = [candidate for candidate in keys if candidate > processed_key]
            if not next_keys:
                break
            processed_key = next_keys[0]
            source = source_for_b2_key(processed_key)
            records = load_b2_raw_records(processed_key)
            record_offset = 0
            continue
        rec = records[record_offset]
        fid = rec_get(rec, *source["id_fields"]) or f"{source['label']}:{record_offset}"
        name = rec_get(rec, *source["name_fields"])
        rows.append(
            record_tuple(
                TARGETS["facilities_csv"]["collection"],
                f"{source['label']}:{fid}",
                {
                    "facilityId": str(fid),
                    "name": name,
                    "raw": rec,
                    "source": source["label"],
                    "sourceB2Bucket": B2_BUCKET,
                    "sourceB2Key": processed_key,
                    "sourceRecordOffset": record_offset,
                    "ingestedAt": now_iso(),
                },
            )
        )
        record_offset += 1

    inserted = insert_records(conn, rows)
    replay_cursor = {
        "key": processed_key,
        "recordOffset": record_offset,
        "recordsInserted": inserted,
        "updatedAt": now_iso(),
    }
    b2_json_put(cursor_key, replay_cursor)
    coverage = 0.0 if FACILITY_REPLAY_SKIP_COVERAGE else coverage_rate(conn, TARGETS["facilities_csv"])
    set_cursor(conn, "facilities_b2_replay", json.dumps(replay_cursor, separators=(",", ":")), inserted, coverage, None)
    log(f"[facilities_replay] key={processed_key} offset={record_offset} inserted={inserted}")
    return inserted


def insert_records(conn, rows: list[tuple[str, str, str, str, str, str, str, int, str]]) -> int:
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        uris = [r[0] for r in batch]
        medical_rows = [medical_row(r) for r in batch]
        edge_rows = [medical_source_edge(r) for r in batch]
        for attempt in range(RW_DML_RETRIES + 1):
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM vertex_medical WHERE vertex_id IN %s", (tuple(uris),))
                    edge_ids = tuple(r[0] for r in edge_rows)
                    if edge_ids:
                        cur.execute("DELETE FROM edge_medical_source_record WHERE edge_id IN %s", (edge_ids,))
                    psycopg2.extras.execute_batch(
                        cur,
                        """
                        INSERT INTO vertex_medical (
                          vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                          rkey, repo, label, did, name, display_name, description,
                          category, code, standard, effective_date, props, collection,
                          source, source_id, ingested_at, created_at, actor_did, org_did
                        )
                        VALUES (
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        medical_rows,
                        page_size=BATCH_SIZE,
                    )
                    psycopg2.extras.execute_batch(
                        cur,
                        """
                        INSERT INTO edge_medical_source_record (
                          edge_id, source_id, record_vid, collection, relation_kind, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        edge_rows,
                        page_size=BATCH_SIZE,
                    )
                conn.commit()
                break
            except Exception as exc:
                conn.rollback()
                if attempt >= RW_DML_RETRIES or not is_retryable_rw_error(exc):
                    raise
                delay = retry_delay(attempt)
                log(f"[rw] DML retry {attempt + 1}/{RW_DML_RETRIES} after {delay:.1f}s: {exc}")
                time.sleep(delay)
        total += len(batch)
    return total


def fetch_pubmed(conn) -> int:
    target = TARGETS["pubmed"]
    start = int(get_cursor(conn, "pubmed") or "0")
    rows = []
    retmax = min(PUBMED_RETMAX, MAX_RECORDS_PER_RUN)
    log(f"[pubmed] cursor={start} retmax={retmax}")
    params = {
        "db": "pubmed",
        "term": PUBMED_TERM,
        "retmode": "json",
        "retstart": start,
        "retmax": retmax,
        "sort": "pub+date",
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    log("[pubmed] esearch start")
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params, timeout=(10, 30))
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    log(f"[pubmed] esearch ids={len(ids)}")
    if not ids:
        set_cursor(conn, "pubmed", "0", 0, coverage_rate(conn, target), None)
        return 0
    for i in range(0, len(ids), 200):
        chunk = ids[i : i + 200]
        sparams = {"db": "pubmed", "id": ",".join(chunk), "retmode": "json"}
        if NCBI_API_KEY:
            sparams["api_key"] = NCBI_API_KEY
        log(f"[pubmed] esummary start chunk={i // 200 + 1} size={len(chunk)}")
        sr = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params=sparams, timeout=(10, 30))
        sr.raise_for_status()
        result = sr.json().get("result", {})
        log(f"[pubmed] esummary done chunk={i // 200 + 1}")
        for pmid in chunk:
            item = result.get(pmid, {})
            if not item:
                continue
            rows.append(
                record_tuple(
                    target["collection"],
                    pmid,
                    {
                        "pmid": pmid,
                        "title": item.get("title"),
                        "fullJournalName": item.get("fulljournalname"),
                        "pubDate": item.get("pubdate"),
                        "source": "pubmed-eutils",
                        "ingestedAt": now_iso(),
                    },
                )
            )
    log(f"[pubmed] dml start rows={min(len(rows), MAX_RECORDS_PER_RUN)}")
    inserted = insert_records(conn, rows[:MAX_RECORDS_PER_RUN])
    log(f"[pubmed] dml done inserted={inserted}")
    next_cursor = str(start + len(ids))
    set_cursor(conn, "pubmed", next_cursor, inserted, coverage_rate(conn, target), None)
    log(f"[pubmed] cursor updated {start}->{next_cursor}")
    return inserted


def fetch_clinical_trials(conn) -> int:
    target = TARGETS["clinical_trials"]
    token = get_cursor(conn, "clinical_trials")
    rows = []
    params = {"format": "json", "pageSize": min(1000, MAX_RECORDS_PER_RUN)}
    if token:
        params["pageToken"] = token
    r = requests.get("https://clinicaltrials.gov/api/v2/studies", params=params, timeout=90)
    r.raise_for_status()
    data = r.json()
    for study in data.get("studies", []):
        proto = study.get("protocolSection", {})
        ident = proto.get("identificationModule", {})
        status = proto.get("statusModule", {})
        design = proto.get("designModule", {})
        nct_id = ident.get("nctId")
        if not nct_id:
            continue
        rows.append(
            record_tuple(
                target["collection"],
                nct_id,
                {
                    "trialId": nct_id,
                    "briefTitle": ident.get("briefTitle"),
                    "officialTitle": ident.get("officialTitle"),
                    "overallStatus": status.get("overallStatus"),
                    "studyType": design.get("studyType"),
                    "source": "clinicaltrials-gov-v2",
                    "ingestedAt": now_iso(),
                },
            )
        )
    inserted = insert_records(conn, rows[:MAX_RECORDS_PER_RUN])
    next_token = data.get("nextPageToken") or ""
    set_cursor(conn, "clinical_trials", next_token, inserted, coverage_rate(conn, target), None)
    return inserted


def ingest_dsm_categories(conn) -> int:
    target = TARGETS["dsm"]
    rows = [
        record_tuple(
            target["collection"],
            name,
            {
                "categoryName": name,
                "taxonomy": "DSM category metadata",
                "criteriaIncluded": False,
                "source": "category-level-public-metadata",
                "ingestedAt": now_iso(),
            },
        )
        for name in DSM_CATEGORIES
    ]
    inserted = insert_records(conn, rows)
    set_cursor(conn, "dsm", "complete", inserted, coverage_rate(conn, target), None)
    return inserted


def ingest_facilities_csv(conn) -> int:
    url = os.environ.get("FACILITY_CSV_URL", "")
    target = TARGETS["facilities_csv"]
    raw_cursor = get_facility_cursor(conn)
    try:
        cursor = json.loads(raw_cursor)
        source_index = int(cursor.get("sourceIndex", 0))
        offset = int(cursor.get("offset", 0))
    except Exception:
        source_index = 0
        offset = int(raw_cursor or "0")
    rows = []

    if url:
        sources = [
            {
                "label": os.environ.get("FACILITY_SOURCE_LABEL", "facility-csv"),
                "kind": "csv-jsonl",
                "url": url,
                "id_fields": ["id", "facility_id", "provider_id", "ccn", "name", "hospital_name"],
                "name_fields": ["name", "hospital_name", "facility_name"],
            }
        ]
    else:
        sources = FACILITY_SOURCES

    while len(rows) < MAX_RECORDS_PER_RUN and source_index < len(sources):
        source = sources[source_index]
        source_label = source["label"]
        started_at = now_iso()
        run_id = f"{source_label}-{int(time.time())}-{offset}"
        page_records: list[dict[str, Any]] = []
        source_url = source["url"]
        if source["kind"] == "cms-data-api":
            limit = MAX_RECORDS_PER_RUN - len(rows)
            r = requests.get(source["url"], params={"size": limit, "offset": offset}, timeout=180)
            r.raise_for_status()
            records = r.json()
            if not records:
                log(f"[facilities_csv] source complete label={source_label} offset={offset}")
                source_index += 1
                offset = 0
                continue
            page_records = records
            source_url = r.url
            iterator = enumerate(records, start=offset)
        else:
            r = requests.get(source["url"], timeout=180)
            r.raise_for_status()
            text = r.text
            if source["url"].endswith(".jsonl"):
                parsed = [json.loads(line) for line in text.splitlines() if line.strip()]
            else:
                parsed = list(csv.DictReader(io.StringIO(text)))
            page_records = parsed[offset : offset + (MAX_RECORDS_PER_RUN - len(rows))]
            source_url = r.url
            iterator = ((idx, rec) for idx, rec in enumerate(parsed) if idx >= offset)

        b2_info = upload_facility_raw_page(source, offset, page_records, run_id)
        asset_id = f"{source_label}:{run_id}"
        upsert_facility_asset(
            conn,
            asset_id,
            source_label,
            run_id,
            b2_info["key"],
            b2_info["bytes"],
            b2_info["sha256"],
            source_url,
            len(page_records),
            offset,
        )

        for idx, rec in iterator:
            if len(rows) >= MAX_RECORDS_PER_RUN:
                break
            fid = rec_get(rec, *source["id_fields"]) or f"{source_label}:{idx}"
            name = rec_get(rec, *source["name_fields"])
            rows.append(
                record_tuple(
                    target["collection"],
                    f"{source_label}:{fid}",
                    {
                        "facilityId": str(fid),
                        "name": name,
                        "raw": rec,
                        "source": source_label,
                        "ingestedAt": now_iso(),
                    },
                )
            )
            offset = idx + 1
        log(f"[facilities_csv] source={source_label} nextOffset={offset} buffered={len(rows)}")

    inserted = insert_records(conn, rows)
    next_cursor = json.dumps(
        {"sourceIndex": source_index, "offset": offset, "source": sources[source_index]["label"] if source_index < len(sources) else "complete"},
        separators=(",", ":"),
    )
    upsert_facility_run(
        conn,
        run_id if "run_id" in locals() else f"facilities_csv-{int(time.time())}",
        sources[source_index]["label"] if source_index < len(sources) else "complete",
        "ok",
        started_at if "started_at" in locals() else now_iso(),
        len(page_records) if "page_records" in locals() else 0,
        inserted,
        max(0, offset - (len(page_records) if "page_records" in locals() else 0)),
        offset,
        b2_info["key"] if "b2_info" in locals() else None,
        b2_info["bytes"] if "b2_info" in locals() else None,
        b2_info["sha256"] if "b2_info" in locals() else None,
    )
    upsert_facility_cursor(
        conn,
        next_cursor,
        sources[source_index]["label"] if source_index < len(sources) else "complete",
        offset,
        run_id if "run_id" in locals() else None,
        asset_id if "asset_id" in locals() else None,
        b2_info["key"] if "b2_info" in locals() else None,
        "ok",
    )
    conn.commit()
    set_cursor(conn, "facilities_csv", next_cursor, inserted, coverage_rate(conn, target), None)
    return inserted


def run_target(conn, name: str) -> None:
    target = TARGETS[name]
    rate = coverage_rate(conn, target)
    if rate >= 1.0:
        log(f"[{name}] coverage already complete: {rate:.4f}")
        return
    log(f"[{name}] coverage={rate:.4f}; ingesting")
    if name == "pubmed":
        inserted = fetch_pubmed(conn)
    elif name == "clinical_trials":
        inserted = fetch_clinical_trials(conn)
    elif name == "dsm":
        inserted = ingest_dsm_categories(conn)
    elif name == "facilities_csv":
        inserted = ingest_facilities_csv(conn)
    else:
        raise ValueError(f"unknown target: {name}")
    log(f"[{name}] inserted={inserted}")


def main() -> int:
    selected = [x.strip() for x in os.environ.get("TARGETS", ",".join(TARGETS)).split(",") if x.strip()]
    if FACILITY_RAW_ONLY:
        if any(name != "facilities_csv" for name in selected):
            log("[facilities_raw] FACILITY_RAW_ONLY ignores non-facility targets")
        archived = archive_facilities_raw_to_b2()
        log(f"[facilities_raw] archived={archived}")
        return 0
    try:
        rw_mode = assert_rw_health_gate()
    except Exception as exc:
        log(f"[rw-health] degraded; skipping RW writes this run: {exc}")
        return 0
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET RW_IMPLICIT_FLUSH = {'true' if RW_IMPLICIT_FLUSH else 'false'}")
            cur.execute("SET statement_timeout = %s", (f"{RW_STATEMENT_TIMEOUT_SECONDS}s",))
            dml_rate_limit = RW_DEGRADED_DML_RATE_LIMIT if rw_mode == "degraded" else RW_DML_RATE_LIMIT
            cur.execute("SET dml_rate_limit = %s", (dml_rate_limit,))
            log(f"[rw-health] mode={rw_mode} dml_rate_limit={dml_rate_limit}")
        if FACILITY_REPLAY_FROM_B2:
            inserted = replay_facilities_from_b2(conn)
            log(f"[facilities_replay] inserted={inserted}")
            return 0
        for name in selected:
            if not within_deadline():
                log("deadline reached")
                return 0
            if name not in TARGETS:
                log(f"[warn] unknown target {name}; skipping")
                continue
            try:
                run_target(conn, name)
            except Exception as exc:
                conn.rollback()
                log(f"[{name}] ERROR {exc}")
                try:
                    set_cursor(conn, name, get_cursor(conn, name), 0, coverage_rate(conn, TARGETS[name]), str(exc)[:512])
                except Exception as cursor_exc:
                    conn.rollback()
                    log(f"[{name}] cursor error write skipped: {cursor_exc}")
                raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
