#!/usr/bin/env python3
"""Hourly data collection batch.
Collects patent works from OpenAlex API and DNS observations via Cloudflare DoH
from the Umbrella top-1M domain list.
Inserts directly to RisingWave vertex_repo_record table.

Data sources (egress-compatible substitutions):
  Patents: OpenAlex API (api.openalex.org) with patent-concept filter.
           Wikidata SPARQL (original spec) is blocked by egress policy.
  Domains: Umbrella top-1M (Cisco, S3 HTTP) + Cloudflare DoH.
           Tranco daily list server is inaccessible from this environment.

Usage: python3 hourly-data-collection.py
Returns JSON: {collected, inserted, next_patent_offset, next_dns_offset, elapsed_seconds}
"""

import json
import os
import sys
import time
import hashlib
import base64
import zipfile
import io
import concurrent.futures
from datetime import datetime, timezone

import requests
import psycopg2

# ── Configuration ──────────────────────────────────────────────────────────────
STATE_FILE     = "/tmp/hourly-collection-state.json"
UMBRELLA_CACHE = "/tmp/umbrella-top1m.csv"
UMBRELLA_ZIP   = "/tmp/umbrella-top1m.zip"

DB_CONFIG = {
    "host":    "<vendor-rw-host-deprecated>",
    "port":    4566,
    "dbname":  "dev",
    "user":    "root",
    "password": "",
    "connect_timeout": 30,
}

REPO              = "did:plc:etzhayyim-collector"
PATENT_COLLECTION = "com.etzhayyim.apps.patent.patent"
DNS_COLLECTION    = "com.etzhayyim.apps.dns.observation"

PATENT_LIMIT    = 3000   # target rows per run from OpenAlex
DNS_LIMIT       = 500    # domains from Umbrella list per run
DNS_CONCURRENCY = 25     # parallel DoH lookups

OPENALEX_URL  = "https://api.openalex.org/works"
# Concept C95457728 = "Patent" in OpenAlex (311K+ patent-concept works)
PATENT_CONCEPT = "C95457728"
UMBRELLA_URL  = "http://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
DOH_URL       = "https://cloudflare-dns.com/dns-query"

OPENALEX_MAILTO = "research@etzhayyim.com"   # polite API usage
# ──────────────────────────────────────────────────────────────────────────────


def log(tag: str, msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}][{tag}] {msg}", flush=True)


# ── TID-style rkey: base32-sortable 13-char timestamp ID ─────────────────────
_B32 = "234567abcdefghijklmnopqrstuvwxyz"
_rkey_counter = 0

def generate_rkey() -> str:
    global _rkey_counter
    ts_us = int(time.time() * 1_000_000)
    _rkey_counter = (_rkey_counter + 1) & 0x3FF
    n = (ts_us << 10) | _rkey_counter
    chars = []
    for _ in range(13):
        chars.append(_B32[n & 0x1F])
        n >>= 5
    return "".join(reversed(chars))


# ── Minimal CIDv1 for record cid field ────────────────────────────────────────
def _make_cid(value_json: str) -> str:
    digest = hashlib.sha256(value_json.encode()).digest()
    prefix = bytes([0x01, 0x55, 0x12, 0x20]) + digest  # v1, raw, sha2-256
    return "b" + base64.b32encode(prefix).decode().lower().rstrip("=")


# ── State persistence ─────────────────────────────────────────────────────────
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"patent_cursor": "*", "patent_offset": 0, "dns_offset": 10000}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ── OpenAlex patent collection ────────────────────────────────────────────────
def collect_patents(cursor: str, limit: int = 3000) -> tuple[list[dict], str]:
    """
    Page through OpenAlex works with the Patent concept using cursor pagination.
    Returns (records, next_cursor).
    """
    log("openalex", f"Fetching {limit} works (Patent concept, cursor={cursor[:20]}…)")
    all_results: list[dict] = []
    next_cursor = cursor
    page_size = 200   # OpenAlex max per-page

    while len(all_results) < limit:
        remaining = limit - len(all_results)
        fetch = min(page_size, remaining)
        try:
            resp = requests.get(
                OPENALEX_URL,
                params={
                    "filter":  f"concepts.id:{PATENT_CONCEPT}",
                    "per-page": str(fetch),
                    "cursor":  next_cursor,
                    "select":  "id,title,publication_date,authorships,biblio,doi,keywords",
                },
                headers={
                    "User-Agent": f"etzhayyimCollector/1.0 (mailto:{OPENALEX_MAILTO})",
                    "Accept": "application/json",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            next_cursor = data.get("meta", {}).get("next_cursor", "*")

            if not results:
                log("openalex", "No more results from OpenAlex")
                next_cursor = "*"  # reset for next run
                break

            all_results.extend(results)
            log("openalex", f"  +{len(results)} → total={len(all_results)}")

            if next_cursor is None:
                next_cursor = "*"
                break
        except Exception as exc:
            log("openalex", f"  ERROR: {exc}")
            break

        time.sleep(0.2)   # stay within polite rate limit

    log("openalex", f"Collected {len(all_results)} patent works")
    return all_results, next_cursor or "*"


def _oa_val(obj: object, *keys: str) -> str:
    """Safe nested dict accessor returning empty string on miss."""
    for k in keys:
        if not isinstance(obj, dict):
            return ""
        obj = obj.get(k, "")
    return obj or ""


def build_patent_value(work: dict, now_iso: str) -> dict:
    authors = work.get("authorships", []) or []
    inventor_names = [
        _oa_val(a, "author", "display_name")
        for a in authors[:5]
        if _oa_val(a, "author", "display_name")
    ]
    biblio = work.get("biblio") or {}
    return {
        "$type":         PATENT_COLLECTION,
        "patentId":      _oa_val(work, "id").rsplit("/", 1)[-1],
        "patentUri":     _oa_val(work, "id"),
        "label":         _oa_val(work, "title"),
        "doi":           _oa_val(work, "doi"),
        "inventorLabel": "; ".join(inventor_names),
        "filingDate":    "",
        "publicationDate": _oa_val(work, "publication_date"),
        "patentNumber":  _oa_val(biblio, "volume") or "",
        "keywords":      [k.get("keyword", "") for k in (work.get("keywords") or [])[:10]],
        "collectedAt":   now_iso,
    }


# ── Umbrella top-1M download + cache ─────────────────────────────────────────
def ensure_umbrella_cache() -> bool:
    if os.path.exists(UMBRELLA_CACHE) and os.path.getsize(UMBRELLA_CACHE) > 5_000_000:
        log("umbrella", f"Using cached Umbrella list ({os.path.getsize(UMBRELLA_CACHE):,} bytes)")
        return True
    log("umbrella", "Downloading Umbrella top-1M from Cisco S3…")
    try:
        r = requests.get(UMBRELLA_URL, timeout=90, stream=True)
        r.raise_for_status()
        raw = b"".join(r.iter_content(65536))
        log("umbrella", f"Downloaded {len(raw):,} bytes (zip)")
        z = zipfile.ZipFile(io.BytesIO(raw))
        csv_name = z.namelist()[0]
        with z.open(csv_name) as src, open(UMBRELLA_CACHE, "wb") as dst:
            dst.write(src.read())
        log("umbrella", f"Cached to {UMBRELLA_CACHE}")
        return True
    except Exception as exc:
        log("umbrella", f"Download failed: {exc}")
        return False


def read_umbrella_slice(offset: int, count: int) -> list[tuple[int, str]]:
    domains: list[tuple[int, str]] = []
    try:
        with open(UMBRELLA_CACHE) as f:
            for i, line in enumerate(f):
                if i < offset:
                    continue
                if i >= offset + count:
                    break
                parts = line.strip().split(",", 1)
                if len(parts) == 2:
                    try:
                        domains.append((int(parts[0]), parts[1].strip()))
                    except ValueError:
                        pass
    except FileNotFoundError:
        pass
    return domains


# ── Cloudflare DoH lookup ─────────────────────────────────────────────────────
def _doh_lookup(rank_domain: tuple[int, str]) -> dict:
    rank, domain = rank_domain
    now = datetime.now(timezone.utc).isoformat()
    try:
        r = requests.get(
            DOH_URL,
            params={"name": domain, "type": "A"},
            headers={"Accept": "application/dns-json",
                     "User-Agent": "etzhayyimCollector/1.0"},
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            answers = data.get("Answer", [])
            ips = [a["data"] for a in answers if a.get("type") == 1]
            return {
                "rank": rank, "domain": domain, "ips": ips,
                "status": data.get("Status", -1),
                "ttl": answers[0]["TTL"] if answers else None,
                "observed_at": now,
            }
        return {"rank": rank, "domain": domain, "ips": [], "status": -1,
                "ttl": None, "observed_at": now, "error": f"HTTP {r.status_code}"}
    except Exception as exc:
        return {"rank": rank, "domain": domain, "ips": [], "status": -1,
                "ttl": None, "observed_at": now, "error": str(exc)[:200]}


def collect_dns(dns_offset: int, limit: int = 500) -> list[dict]:
    log("dns", f"Resolving {limit} domains from Umbrella offset={dns_offset}")
    ensure_umbrella_cache()
    domains = read_umbrella_slice(dns_offset, limit)

    if not domains:
        log("dns", "Umbrella cache empty — using fallback well-known domains")
        fallback = [
            "google.com","youtube.com","facebook.com","twitter.com","instagram.com",
            "baidu.com","wikipedia.org","yahoo.com","reddit.com","netflix.com",
            "microsoft.com","apple.com","amazon.com","linkedin.com","github.com",
        ]
        domains = [(dns_offset + i + 1, d) for i, d in enumerate(fallback[:limit])]

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=DNS_CONCURRENCY) as pool:
        for obs in pool.map(_doh_lookup, domains):
            results.append(obs)

    ok = sum(1 for r in results if not r.get("error"))
    log("dns", f"Resolved {len(results)} domains ({ok} OK, {len(results)-ok} errors)")
    return results


# ── Row building ──────────────────────────────────────────────────────────────
COLUMNS = [
    "uri", "cid", "collection", "rkey", "repo", "repo_rev",
    "value_json", "indexed_at", "takedown_ref", "ts_ms", "created_at",
]

def make_row(collection: str, value: dict, now_iso: str, ts_ms: int) -> dict:
    rkey       = generate_rkey()
    vj         = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    uri        = f"at://{REPO}/{collection}/{rkey}"
    return {
        "uri":          uri,
        "cid":          _make_cid(vj),
        "collection":   collection,
        "rkey":         rkey,
        "repo":         REPO,
        "repo_rev":     format(ts_ms, "016x"),
        "value_json":   vj,
        "indexed_at":   now_iso,
        "takedown_ref": None,
        "ts_ms":        ts_ms,
        "created_at":   now_iso,
    }


# ── DB insertion ──────────────────────────────────────────────────────────────
INSERT_SQL = (
    f"INSERT INTO vertex_repo_record ({','.join(COLUMNS)}) "
    f"SELECT {','.join(['%s']*len(COLUMNS))} "
    f"WHERE NOT EXISTS (SELECT 1 FROM vertex_repo_record WHERE uri = %s)"
)


def insert_rows(conn, rows: list[dict], batch_size: int = 200) -> int:
    inserted = 0
    with conn.cursor() as cur:
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            values = [tuple(r[c] for c in COLUMNS) + (r["uri"],) for r in batch]
            try:
                cur.executemany(INSERT_SQL, values)
                conn.commit()
                inserted += len(batch)
                log("db", f"  batch {start}–{start+len(batch)-1}: {len(batch)} rows OK")
            except Exception as exc:
                conn.rollback()
                log("db", f"  batch {start} ERROR: {exc}")
    return inserted


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> dict:
    t0      = time.time()
    state   = load_state()
    cursor  = state.get("patent_cursor", "*")
    patent_offset = int(state.get("patent_offset", 0))   # for reporting only
    dns_offset    = int(state.get("dns_offset", 10000))

    log("main", f"Starting — patent_cursor={cursor[:20]}… dns_offset={dns_offset}")

    now_iso = datetime.now(timezone.utc).isoformat()
    ts_ms   = int(time.time() * 1000)

    # ── Collect ────────────────────────────────────────────────────────────────
    patent_raw, next_cursor = collect_patents(cursor, PATENT_LIMIT)
    dns_raw                 = collect_dns(dns_offset, DNS_LIMIT)
    total_collected         = len(patent_raw) + len(dns_raw)
    log("main", f"Collected {len(patent_raw)} patents + {len(dns_raw)} DNS = {total_collected} total")

    # ── Build rows ─────────────────────────────────────────────────────────────
    rows: list[dict] = []
    for work in patent_raw:
        rows.append(make_row(PATENT_COLLECTION, build_patent_value(work, now_iso), now_iso, ts_ms))
    for obs in dns_raw:
        rows.append(make_row(DNS_COLLECTION, {"$type": DNS_COLLECTION, **obs}, now_iso, ts_ms))
    log("main", f"Built {len(rows)} rows for insertion")

    # ── Insert ─────────────────────────────────────────────────────────────────
    inserted = 0
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        log("db", "Connected to RisingWave")
        inserted = insert_rows(conn, rows)
        conn.close()
        log("db", f"Total inserted: {inserted}")
    except Exception as exc:
        log("db", f"Connection/insert error: {exc}")

    # ── Advance offsets ────────────────────────────────────────────────────────
    next_patent_offset = patent_offset + len(patent_raw)
    next_dns_offset    = dns_offset + DNS_LIMIT
    if next_dns_offset >= 1_000_000:
        next_dns_offset = 10_000

    new_state = {
        "patent_cursor":       next_cursor,
        "patent_offset":       next_patent_offset,
        "dns_offset":          next_dns_offset,
        "last_run":            now_iso,
        "last_collected":      total_collected,
        "last_inserted":       inserted,
    }
    save_state(new_state)
    log("main", f"State saved → next_cursor={next_cursor[:20]}… next_dns_offset={next_dns_offset}")

    elapsed = round(time.time() - t0, 1)
    result = {
        "collected":          total_collected,
        "inserted":           inserted,
        "next_patent_offset": next_patent_offset,
        "next_dns_offset":    next_dns_offset,
        "elapsed_seconds":    elapsed,
    }
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    main()
