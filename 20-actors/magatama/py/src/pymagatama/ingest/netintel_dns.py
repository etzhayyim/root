"""
netintel_dns — DNS / RDAP enrichment for shadow-level domains.

Pulls stale domains from vertex_dns_observation (not updated in last 30 days),
re-queries RDAP (IANA endpoint) + Cloudflare DoH for A/AAAA/NS/MX/TXT,
and writes updated rows back.

Task type: netintel.dns.delta
Env: none required (uses public RDAP/DoH APIs)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.parse
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
SOURCE_ID = "netintel-dns"
_DOH_URL = "https://cloudflare-dns.com/dns-query"
# rdap.org bootstraps to the correct registrar per RFC 7484.
# rdap.iana.org serves TLD info only and returns 404 for SLDs.
_RDAP_BOOTSTRAP = "https://rdap.org/domain/"
_TIMEOUT = 10


def _http_json(url: str, headers: dict | None = None, timeout: int = _TIMEOUT) -> dict | None:
    req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _rdap_domain(domain: str) -> dict[str, Any]:
    data = _http_json(f"{_RDAP_BOOTSTRAP}{domain}")
    if not data:
        return {}
    entities = data.get("entities", [])
    registrar = ""
    for ent in entities:
        roles = ent.get("roles", [])
        if "registrar" in roles:
            vcard = ent.get("vcardArray", [])
            if isinstance(vcard, list) and len(vcard) > 1:
                for prop in vcard[1]:
                    if isinstance(prop, list) and prop[0] == "fn":
                        registrar = str(prop[3] or "")
                        break
            if not registrar:
                registrar = ent.get("handle", "")
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

    status = []
    for s in data.get("status", []):
        if isinstance(s, str):
            status.append(s)

    dnssec = data.get("secureDNS", {})
    dnssec_str = "unsigned"
    if dnssec.get("delegationSigned"):
        dnssec_str = "signed"

    return {
        "registrar": registrar,
        "nameservers": ",".join(nameservers),
        "registration_date": events.get("registration", ""),
        "expiration_date": events.get("expiration", ""),
        "last_changed_date": events.get("last changed", ""),
        "status": ",".join(status),
        "dnssec": dnssec_str,
    }


def _doh_records(domain: str) -> dict[str, Any]:
    types = {"A": [], "AAAA": [], "MX": [], "NS": [], "TXT": []}
    for rtype in types:
        url = f"{_DOH_URL}?name={urllib.parse.quote(domain)}&type={rtype}"
        data = _http_json(url, headers={"Accept": "application/dns-json"})
        if not data:
            continue
        for answer in data.get("Answer", []):
            val = str(answer.get("data", "")).strip().rstrip(".")
            if val:
                types[rtype].append(val)
    return {k: ",".join(v) for k, v in types.items()}


def _stale_domains(batch_size: int) -> list[str]:
    sql = (
        "SELECT DISTINCT domain, observed_at FROM vertex_dns_observation "
        "WHERE observed_at::timestamptz < NOW() - INTERVAL '30 days' "
        f"ORDER BY observed_at ASC LIMIT {int(batch_size)}"
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql)
            return [row[0] for row in (cur.fetchall() or []) if row[0]]
    except Exception as e:
        LOG.warning("stale_domains query failed: %s", e)
        return []


def _insert_dns_row(domain: str, rdap: dict, doh: dict, run_id: str) -> bool:
    ts = now_iso()
    vertex_id = f"at://did:web:ingest.etzhayyim.com/ai.gftd.apps.collector.dnsObservation/{domain}"
    sql = (
        "INSERT INTO vertex_dns_observation "
        "(vertex_id, owner_did, domain, registrar, nameservers, "
        "registration_date, expiration_date, last_changed_date, dnssec, status, "
        "run_id, observed_at, sensitivity_ord, created_date) "
        "SELECT %s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, %s::varchar, %s::varchar, %s::varchar, "
        "%s::varchar, %s::varchar, 1::bigint, CURRENT_DATE "
        "WHERE NOT EXISTS (SELECT 1 FROM vertex_dns_observation WHERE vertex_id = %s::varchar)"
    )
    params = (
        vertex_id, INGEST_ACTOR, domain,
        rdap.get("registrar", ""),
        rdap.get("nameservers", "") or doh.get("NS", ""),
        rdap.get("registration_date", ""),
        rdap.get("expiration_date", ""),
        rdap.get("last_changed_date", ""),
        rdap.get("dnssec", ""),
        rdap.get("status", ""),
        run_id, ts,
        vertex_id,
    )
    try:
        with sync_cursor() as cur:
            cur.execute(sql, params)
            return (cur.rowcount or 0) > 0
    except Exception as e:
        LOG.warning("dns insert failed domain=%s: %s", domain, e)
        return False


def ingest_dns_delta(
    run_id: str = "",
    target_tier: str = "shadow",
    batch_size: int = 30,
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
            rdap = _rdap_domain(domain)
            doh = _doh_records(domain)
            if _insert_dns_row(domain, rdap, doh, run_id):
                rows_written += 1
        except Exception as e:
            LOG.warning("dns enrich failed domain=%s: %s", domain, e)
            errors += 1
        time.sleep(0.1)

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
