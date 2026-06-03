"""
ip_enrich — GeoIP enrichment for shadow-level IP addresses.

Pulls IPs from vertex_ip_address that haven't been updated recently,
queries ipinfo.io (free tier, no key required for basic fields),
and writes enriched rows back.

Task type: netintel.ip.enrich
Env: IPINFO_TOKEN — optional ipinfo.io API token for higher rate limits
"""

from __future__ import annotations

import json
import logging
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
import os

LOG = logging.getLogger(__name__)

INGEST_ACTOR = "did:web:ingest.etzhayyim.com"
SOURCE_ID = "netintel-ip-enrich"
_IPINFO_BASE = "https://ipinfo.io"
_TIMEOUT = 10


def _ipinfo(ip: str, token: str) -> dict[str, Any]:
    url = f"{_IPINFO_BASE}/{ip}/json"
    if token:
        url += f"?token={token}"
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "etzhayyim-ingest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return {}

    loc = data.get("loc", "")
    lat, lon = 0.0, 0.0
    if loc and "," in loc:
        parts = loc.split(",", 1)
        try:
            lat, lon = float(parts[0]), float(parts[1])
        except ValueError:
            pass

    org_raw = data.get("org", "")
    asn, asn_org = "", ""
    if org_raw:
        parts = org_raw.split(" ", 1)
        asn = parts[0].lstrip("AS")
        asn_org = parts[1] if len(parts) > 1 else ""

    return {
        "country_code": data.get("country", ""),
        "city": data.get("city", ""),
        "region": data.get("region", ""),
        "lat": lat,
        "lon": lon,
        "asn": asn,
        "asn_org": asn_org,
        "isp": asn_org,
        "ptr_record": data.get("hostname", ""),
    }


def _stale_ips(batch_size: int) -> list[str]:
    sql = (
        "SELECT address FROM vertex_ip_address "
        "WHERE observed_at::timestamptz < NOW() - INTERVAL '30 days' "
        f"ORDER BY observed_at ASC LIMIT {int(batch_size)}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in (cur.fetchall() or []) if row[0]]
    except Exception as e:
        LOG.warning("stale_ips query failed: %s", e)
        return []


def _upsert_ip(ip: str, geo: dict, run_id: str) -> bool:
    ts = now_iso()
    vertex_id = f"at://did:web:ingest.etzhayyim.com/com.etzhayyim.apps.collector.ipAddress/{ip}"
    sql = (
        "INSERT INTO vertex_ip_address "
        "(vertex_id, owner_did, address, country_code, city, region, lat, lon, "
        "asn, asn_org, isp, ptr_record, observed_at, sensitivity_ord, created_date) "
        "SELECT %s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::double precision, %s::double precision, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, 1::bigint, CURRENT_DATE "
        "WHERE NOT EXISTS (SELECT 1 FROM vertex_ip_address WHERE vertex_id = %s::varchar)"
    )
    params = (
        vertex_id, INGEST_ACTOR, ip,
        geo.get("country_code", ""),
        geo.get("city", ""),
        geo.get("region", ""),
        geo.get("lat", 0.0),
        geo.get("lon", 0.0),
        geo.get("asn", ""),
        geo.get("asn_org", ""),
        geo.get("isp", ""),
        geo.get("ptr_record", ""),
        ts,
        vertex_id,
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return (cur.rowcount or 0) > 0
    except Exception as e:
        LOG.warning("ip upsert failed ip=%s: %s", ip, e)
        return False


def ingest_ip_enrich(
    run_id: str = "",
    target_tier: str = "shadow",
    batch_size: int = 50,
) -> dict[str, Any]:
    if not run_id:
        run_id = stable_run_id("netintel", SOURCE_ID, "delta")

    token = os.environ.get("IPINFO_TOKEN", "")

    run = IngestRun(ingest_family="netintel", source_id=SOURCE_ID, run_id=run_id, status="running")
    upsert_run(run)

    ips = _stale_ips(batch_size)
    ips_read = len(ips)
    rows_written = 0
    errors = 0

    for ip in ips:
        try:
            geo = _ipinfo(ip, token)
            if geo and _upsert_ip(ip, geo, run_id):
                rows_written += 1
        except Exception as e:
            LOG.warning("ip enrich failed ip=%s: %s", ip, e)
            errors += 1
        time.sleep(0.05)

    mark_run_finished(run_id, status="completed",
                      records_read=ips_read,
                      records_written=rows_written,
                      records_skipped=0,
                      error_count=errors)

    return {
        "ok": True,
        "runId": run_id,
        "ipsRead": ips_read,
        "rowsWritten": rows_written,
        "errorCount": errors,
    }
