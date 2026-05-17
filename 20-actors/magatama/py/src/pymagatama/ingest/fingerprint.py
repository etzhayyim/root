"""
fingerprint — TLS/HTTP fingerprinting for shadow-level hosts.

Pulls domains from vertex_dns_observation + IPs from vertex_ip_address,
probes TLS handshake (cert subject/issuer/SANs/expiry/cipher) and
HTTP response headers via external proxy, writes results to vertex_scan_result.

Task type: netintel.fingerprint.delta
Env:
  SCAN_PROXY_URL — external probe service base URL (required; skips if absent)
  SCAN_PROXY_KEY — Bearer token for probe service (optional)
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

INGEST_ACTOR = "did:web:ingest.etzhayyim.com"
SOURCE_ID = "netintel-fingerprint"
_HTTPS_PORT = 443
_HTTP_PORT = 80
_TIMEOUT = 30


def _proxy_fingerprint(host: str, port: int, proxy_url: str, key: str) -> dict:
    url = proxy_url.rstrip("/") + "/fingerprint"
    payload = json.dumps({"host": host, "port": port}).encode()
    headers: dict = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        LOG.debug("proxy_fingerprint failed host=%s:%s: %s", host, port, e)
        return {}


def _stale_hosts(batch_size: int) -> list[str]:
    """Return domains that haven't been fingerprinted recently."""
    sql = (
        "SELECT DISTINCT domain FROM vertex_dns_observation "
        "WHERE observed_at::timestamptz < NOW() - INTERVAL '30 days' "
        f"ORDER BY observed_at ASC LIMIT {int(batch_size)}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in (cur.fetchall() or []) if row[0]]
    except Exception as e:
        LOG.warning("stale_hosts_fingerprint query failed: %s", e)
        return []


def _insert_fingerprint(host: str, port: int, fp: dict, run_id: str) -> bool:
    ts = now_iso()
    proto = "tls" if port == _HTTPS_PORT else "tcp"
    vertex_id = (
        f"at://did:web:ingest.etzhayyim.com/ai.gftd.apps.collector.scanResult"
        f"/{host}:{port}:fp"
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
    banner_raw = fp.get("banner", "") or fp.get("http_server", "")
    params = (
        vertex_id, INGEST_ACTOR, host, int(port), proto,
        "open" if fp.get("open") else "filtered",
        fp.get("service", "https" if port == _HTTPS_PORT else "http"),
        fp.get("software", ""),
        fp.get("version", ""),
        str(banner_raw)[:512],
        fp.get("tls_version", ""),
        fp.get("tls_cipher", ""),
        str(fp.get("cert_subject", ""))[:512],
        str(fp.get("cert_issuer", ""))[:256],
        fp.get("cert_expires", ""),
        "",
        "proxy-fp",
        ts,
        vertex_id,
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return (cur.rowcount or 0) > 0
    except Exception as e:
        LOG.warning("fingerprint insert failed host=%s:%s: %s", host, port, e)
        return False


def ingest_fingerprint_delta(
    run_id: str = "",
    target_tier: str = "shadow",
    batch_size: int = 8,
) -> dict[str, Any]:
    proxy_url = os.environ.get("SCAN_PROXY_URL", "").strip()
    proxy_key = os.environ.get("SCAN_PROXY_KEY", "")
    if not proxy_url:
        LOG.warning("SCAN_PROXY_URL not set — fingerprint skipped")
        return {"ok": False, "error": "SCAN_PROXY_URL not configured",
                "hostsProbed": 0, "rowsWritten": 0}

    if not run_id:
        run_id = stable_run_id("netintel", SOURCE_ID, "delta")

    run = IngestRun(ingest_family="netintel", source_id=SOURCE_ID, run_id=run_id, status="running")
    upsert_run(run)

    hosts = _stale_hosts(batch_size)
    hosts_probed = len(hosts)
    rows_written = 0
    errors = 0

    for host in hosts:
        for port in (_HTTPS_PORT, _HTTP_PORT):
            try:
                fp = _proxy_fingerprint(host, port, proxy_url, proxy_key)
                if fp and _insert_fingerprint(host, port, fp, run_id):
                    rows_written += 1
            except Exception as e:
                LOG.warning("fingerprint failed host=%s port=%s: %s", host, port, e)
                errors += 1
        time.sleep(0.2)

    mark_run_finished(run_id, status="completed",
                      records_read=hosts_probed,
                      records_written=rows_written,
                      records_skipped=0,
                      error_count=errors)

    return {
        "ok": True,
        "runId": run_id,
        "hostsProbed": hosts_probed,
        "rowsWritten": rows_written,
        "errorCount": errors,
    }
