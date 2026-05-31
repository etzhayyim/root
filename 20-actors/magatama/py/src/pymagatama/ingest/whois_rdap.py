"""
whois_rdap — WHOIS snapshot collection for shadow-level domains.

Pulls domains from vertex_dns_observation, queries RDAP (IANA + TLD-specific
endpoints), and writes structured snapshots to vertex_whois_record.

New table: vertex_whois_record (see migration 20260428180000)

Task type: netintel.whois.delta
Env: none required (uses public RDAP APIs)
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

LOG = logging.getLogger(__name__)

INGEST_ACTOR = "did:web:ingest.etzhayyim.com"
SOURCE_ID = "netintel-whois"
# rdap.org bootstraps to the correct registrar RDAP endpoint per RFC 7484.
# rdap.iana.org serves TLD info only and returns 404 for SLDs like cloudflare.com.
_RDAP_BOOTSTRAP = "https://rdap.org/domain/"
_TIMEOUT = 12


def _http_json(url: str, timeout: int = _TIMEOUT) -> dict | None:
    req = urllib.request.Request(url, headers={"Accept": "application/rdap+json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _rdap_fetch(domain: str) -> dict[str, Any]:
    data = _http_json(f"{_RDAP_BOOTSTRAP}{domain}")
    if not data:
        return {}

    registrar = ""
    registrar_iana_id = ""
    for ent in data.get("entities", []):
        roles = ent.get("roles", [])
        if "registrar" in roles:
            registrar_iana_id = str(ent.get("handle", "")).lstrip("IANA-")
            vcard = ent.get("vcardArray", [])
            if isinstance(vcard, list) and len(vcard) > 1:
                for prop in vcard[1]:
                    if isinstance(prop, list) and prop[0] == "fn":
                        registrar = str(prop[3] or "")
                        break
            break

    nameservers = []
    for ns in data.get("nameservers", []):
        ldhName = ns.get("ldhName", "")
        if ldhName:
            nameservers.append(ldhName.lower())

    events: dict[str, str] = {}
    for ev in data.get("events", []):
        act = ev.get("eventAction", "")
        dt = ev.get("eventDate", "")
        if act and dt:
            events[act] = dt

    status = [s for s in data.get("status", []) if isinstance(s, str)]
    dnssec = data.get("secureDNS", {})
    dnssec_str = "signed" if dnssec.get("delegationSigned") else "unsigned"

    raw_excerpt = json.dumps({
        "handle": data.get("handle", ""),
        "ldhName": data.get("ldhName", ""),
        "status": status[:5],
        "events": events,
    }, ensure_ascii=False)[:4096]

    return {
        "registrar": registrar[:512],
        "registrar_iana_id": registrar_iana_id[:64],
        "nameservers": ",".join(nameservers)[:2048],
        "created_date_rdap": events.get("registration", ""),
        "updated_date_rdap": events.get("last changed", ""),
        "expires_date_rdap": events.get("expiration", ""),
        "status": ",".join(status)[:512],
        "dnssec": dnssec_str,
        "raw_excerpt": raw_excerpt,
    }


def _stale_domains(batch_size: int) -> list[str]:
    # Domains not already snapshotted in vertex_whois_record within 30 days.
    # RisingWave rejects ORDER BY on a column not in the outer SELECT list when
    # using a derived table. Flatten to a single GROUP BY + ORDER BY MIN() to avoid
    # the "for SELECT DISTINCT, ORDER BY expressions must appear in select list" error.
    sql = (
        "SELECT d.domain "
        "FROM vertex_dns_observation d "
        "WHERE NOT EXISTS ("
        "  SELECT 1 FROM vertex_whois_record w "
        "  WHERE w.domain = d.domain "
        "  AND w.queried_at::timestamptz > NOW() - INTERVAL '30 days'"
        ") "
        "GROUP BY d.domain "
        f"ORDER BY MIN(d.observed_at) ASC LIMIT {int(batch_size)}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in (cur.fetchall() or []) if row[0]]
    except Exception as e:
        LOG.warning("stale_domains_for_whois failed: %s", e)
        return []


def _insert_whois(domain: str, rdap: dict, run_id: str) -> bool:
    import hashlib
    ts = now_iso()
    created_date = ts[:10]  # CURRENT_DATE unsupported in RW prepared statements
    snap_hash = hashlib.sha256(f"{domain}:{ts}".encode()).hexdigest()[:16]
    vertex_id = f"at://did:web:ingest.etzhayyim.com/app.etzhayyim.apps.ingest.whoisRecord/{domain}:{snap_hash}"
    sql = (
        "INSERT INTO vertex_whois_record "
        "(vertex_id, owner_did, domain, registrar, registrar_iana_id, nameservers, "
        "created_date_rdap, updated_date_rdap, expires_date_rdap, "
        "status, dnssec, raw_excerpt, queried_at, run_id, "
        "sensitivity_ord, created_date) "
        "SELECT %s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "1::bigint, %s::date "
        "WHERE NOT EXISTS (SELECT 1 FROM vertex_whois_record WHERE vertex_id = %s::varchar)"
    )
    params = (
        vertex_id, INGEST_ACTOR, domain,
        rdap.get("registrar", ""),
        rdap.get("registrar_iana_id", ""),
        rdap.get("nameservers", ""),
        rdap.get("created_date_rdap", ""),
        rdap.get("updated_date_rdap", ""),
        rdap.get("expires_date_rdap", ""),
        rdap.get("status", ""),
        rdap.get("dnssec", ""),
        rdap.get("raw_excerpt", ""),
        ts, run_id, created_date,
        vertex_id,
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return (cur.rowcount or 0) > 0
    except Exception as e:
        LOG.warning("whois insert failed domain=%s: %s", domain, e)
        return False


def ingest_whois_delta(
    run_id: str = "",
    target_tier: str = "shadow",
    batch_size: int = 50,
) -> dict[str, Any]:
    if not run_id:
        run_id = stable_run_id("netintel", SOURCE_ID, "delta")

    run = IngestRun(ingest_family="netintel", source_id=SOURCE_ID, run_id=run_id, status="running")
    upsert_run(run)

    domains = _stale_domains(batch_size)
    domains_read = len(domains)
    rows_written = 0
    errors = 0

    for domain in domains:
        try:
            rdap = _rdap_fetch(domain)
            if rdap and _insert_whois(domain, rdap, run_id):
                rows_written += 1
        except Exception as e:
            LOG.warning("whois enrich failed domain=%s: %s", domain, e)
            errors += 1
        time.sleep(0.15)

    mark_run_finished(run_id, status="completed",
                      records_read=domains_read,
                      records_written=rows_written,
                      records_skipped=0,
                      error_count=errors)

    return {
        "ok": True,
        "runId": run_id,
        "domainsRead": domains_read,
        "rowsWritten": rows_written,
        "errorCount": errors,
    }
