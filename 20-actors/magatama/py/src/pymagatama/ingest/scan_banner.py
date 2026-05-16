"""
scan_banner — port scan + banner grab for shadow-level IPs.

Pulls IPs from vertex_ip_address, submits scan jobs to an external proxy
service (SCAN_PROXY_URL), and writes results to vertex_scan_result.

Scanning is NEVER performed direct-socket from the Vultr VKE cluster to
avoid abuse reports. All traffic routes through SCAN_PROXY_URL.

Task type: netintel.scan.banner
Env:
  SCAN_PROXY_URL — external scan service base URL (required; skips if absent)
  SCAN_PROXY_KEY — Bearer token for scan service (optional)
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any

from pymagatama.ingest.core import (
    IngestRun,
    mark_run_finished,
    now_iso,
    stable_run_id,
    upsert_run,
)
from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger(__name__)

INGEST_ACTOR = "did:web:ingest.gftd.ai"
SOURCE_ID = "netintel-scan"
_COMMON_PORTS = [21, 22, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995,
                 3306, 5432, 6379, 8080, 8443, 27017]
_TIMEOUT = 30


def _proxy_scan(ip: str, ports: list[int], proxy_url: str, key: str) -> list[dict]:
    url = proxy_url.rstrip("/") + "/scan"
    payload = json.dumps({"ip": ip, "ports": ports}).encode()
    headers: dict = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
            return data.get("results", []) if isinstance(data, dict) else []
    except Exception as e:
        LOG.debug("proxy_scan failed ip=%s: %s", ip, e)
        return []


def _stale_ips(batch_size: int) -> list[str]:
    sql = (
        "SELECT DISTINCT address FROM vertex_ip_address "
        "WHERE observed_at::timestamptz < NOW() - INTERVAL '30 days' "
        f"ORDER BY observed_at ASC LIMIT {int(batch_size)}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in (cur.fetchall() or []) if row[0]]
    except Exception as e:
        LOG.warning("stale_ips_scan query failed: %s", e)
        return []


def _insert_scan_result(ip: str, port: int, result: dict, run_id: str) -> bool:
    ts = now_iso()
    proto = result.get("protocol", "tcp")
    vertex_id = (
        f"at://did:web:ingest.gftd.ai/ai.gftd.apps.collector.scanResult"
        f"/{ip}:{port}:{proto}"
    )
    sql = (
        "INSERT INTO vertex_scan_result "
        "(vertex_id, owner_did, ip, port, protocol, state, service, software, version, "
        "banner, tls_version, tls_cipher, cert_subject, cert_issuer, cert_expires, "
        "os_guess, scanner_host, scanned_at, sensitivity_ord, created_date) "
        "SELECT %s::varchar, %s::varchar, %s::varchar, %s::bigint, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, 1::bigint, CURRENT_DATE "
        "WHERE NOT EXISTS (SELECT 1 FROM vertex_scan_result WHERE vertex_id = %s::varchar)"
    )
    params = (
        vertex_id, INGEST_ACTOR, ip, int(port), proto,
        result.get("state", ""),
        result.get("service", ""),
        result.get("software", ""),
        result.get("version", ""),
        str(result.get("banner", ""))[:512],
        result.get("tls_version", ""),
        result.get("tls_cipher", ""),
        result.get("cert_subject", ""),
        result.get("cert_issuer", ""),
        result.get("cert_expires", ""),
        result.get("os_guess", ""),
        "proxy",
        ts,
        vertex_id,
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return (cur.rowcount or 0) > 0
    except Exception as e:
        LOG.warning("scan_result insert failed ip=%s port=%s: %s", ip, port, e)
        return False


def ingest_scan_banner(
    run_id: str = "",
    target_tier: str = "shadow",
    batch_size: int = 8,
) -> dict[str, Any]:
    proxy_url = os.environ.get("SCAN_PROXY_URL", "").strip()
    proxy_key = os.environ.get("SCAN_PROXY_KEY", "")
    if not proxy_url:
        LOG.warning("SCAN_PROXY_URL not set — scan_banner skipped")
        return {"ok": False, "error": "SCAN_PROXY_URL not configured",
                "ipsScanned": 0, "rowsWritten": 0}

    if not run_id:
        run_id = stable_run_id("netintel", SOURCE_ID, "delta")

    run = IngestRun(ingest_family="netintel", source_id=SOURCE_ID, run_id=run_id, status="running")
    upsert_run(run)

    ips = _stale_ips(batch_size)
    ips_scanned = len(ips)
    rows_written = 0
    errors = 0

    for ip in ips:
        try:
            results = _proxy_scan(ip, _COMMON_PORTS, proxy_url, proxy_key)
            for r in results:
                port = int(r.get("port", 0))
                if port and _insert_scan_result(ip, port, r, run_id):
                    rows_written += 1
        except Exception as e:
            LOG.warning("scan_banner failed ip=%s: %s", ip, e)
            errors += 1
        time.sleep(0.2)

    mark_run_finished(run_id, status="completed",
                      records_read=ips_scanned,
                      records_written=rows_written,
                      records_skipped=0,
                      error_count=errors)

    return {
        "ok": True,
        "runId": run_id,
        "ipsScanned": ips_scanned,
        "rowsWritten": rows_written,
        "errorCount": errors,
    }
