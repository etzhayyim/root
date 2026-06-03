#!/usr/bin/env python3
"""
Hourly data collection batch.

Sources
-------
  Wikidata SPARQL  — patents with inventors
                     LIMIT 1000 per run, offset advances by 1000 each run
  Cloudflare DoH   — A/AAAA/MX/NS/TXT for 500 Tranco top-1M domains
                     offset advances by 500 each run, starting at 10 000

Sink
----
  RisingWave vertex_repo_record (direct psycopg2 to <vendor-rw-host>:4566)

State
-----
  /tmp/hourly-collection-state.json  { patent_offset, dns_offset }

Stdout
------
  JSON: { collected, inserted, next_patent_offset, next_dns_offset }
"""

import io
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras

# ── config ────────────────────────────────────────────────────────────────────

STATE_FILE       = "/tmp/hourly-collection-state.json"
TRANCO_CACHE     = "/tmp/tranco_top1m.txt"
TRANCO_URL       = "https://tranco-list.eu/top-1m.csv.zip"
MAJESTIC_URL     = "https://downloads.majestic.com/majestic_million.csv"
MAJESTIC_CACHE   = "/tmp/majestic_million.txt"
UMBRELLA_URL     = "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"
UMBRELLA_CACHE   = "/tmp/umbrella_top1m.txt"
TRANCO_CACHE_TTL = 86_400      # 24 h
WIKIDATA_SPARQL  = "https://query.wikidata.org/sparql"
DOH_URLS         = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/resolve",
]
DOH_URL          = DOH_URLS[0]
DNS_RTYPES       = ["A", "AAAA", "MX", "NS", "TXT"]

RW_HOST     = "<vendor-rw-host-deprecated>"
RW_PORT     = 4566
RW_USER     = "root"
RW_DATABASE = "dev"
RW_PASSWORD = ""

REPO_DID    = "did:plc:etzhayyim-collector"
PATENT_COL  = "com.etzhayyim.apps.patent.patent"
DNS_COL     = "com.etzhayyim.apps.dns.observation"

TIMEOUT_SECS   = 50 * 60   # 50-min hard deadline; 10-min margin for next cron
PATENT_STEP    = 1_000
PATENT_MAX     = 100_000   # rotate offset to 0 after exhausting
DNS_STEP       = 500
DNS_START      = 10_000
DNS_WORKERS    = 20
INSERT_PAGE    = 500
SPARQL_TIMEOUT = 90        # Wikidata server timeout is ~60s; give some headroom

_UA = "etzhayyim-collector/1.0 (contact: ops@etzhayyim.com)"

# ── logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

_start    = time.monotonic()
_deadline = _start + TIMEOUT_SECS


def time_ok() -> bool:
    return time.monotonic() < _deadline


def elapsed() -> float:
    return time.monotonic() - _start


# ── state ─────────────────────────────────────────────────────────────────────

def load_state() -> Dict[str, int]:
    try:
        with open(STATE_FILE) as f:
            s = json.load(f)
            return {
                "patent_offset": int(s.get("patent_offset", 0)),
                "dns_offset":    int(s.get("dns_offset",    DNS_START)),
            }
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return {"patent_offset": 0, "dns_offset": DNS_START}


def save_state(s: Dict) -> None:
    s["last_run"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)


# ── helpers ───────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_ms() -> int:
    return int(time.time() * 1_000)


def make_uri(collection: str, rkey: str) -> str:
    return f"at://{REPO_DID}/{collection}/{rkey}"


def make_row(collection: str, rkey: str, payload: Any, t: str) -> Tuple:
    return (
        make_uri(collection, rkey),              # uri
        "",                                       # cid
        collection,                               # collection
        rkey,                                     # rkey
        REPO_DID,                                 # repo
        "",                                       # repo_rev
        json.dumps(payload, ensure_ascii=False),  # value_json
        t,                                        # indexed_at
        None,                                     # takedown_ref
        ts_ms(),                                  # ts_ms
        t,                                        # created_at
    )


# ── database ──────────────────────────────────────────────────────────────────

def db_connect():
    return psycopg2.connect(
        host=RW_HOST,
        port=RW_PORT,
        user=RW_USER,
        password=RW_PASSWORD,
        dbname=RW_DATABASE,
        connect_timeout=30,
    )


def bulk_insert(conn, rows: List[Tuple]) -> int:
    if not rows:
        return 0
    cur = conn.cursor()
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO vertex_repo_record "
        "(uri,cid,collection,rkey,repo,repo_rev,value_json,indexed_at,takedown_ref,ts_ms,created_at) "
        "VALUES %s",
        rows,
        page_size=INSERT_PAGE,
    )
    conn.commit()
    cur.close()
    return len(rows)


# ── Wikidata patents ───────────────────────────────────────────────────────────

_PATENT_QUERY = """\
SELECT ?patent ?patentLabel ?inventor ?inventorLabel ?filingDate ?pubDate WHERE {{
  ?patent wdt:P31 wd:Q253623 ;
          wdt:P61 ?inventor .
  OPTIONAL {{ ?patent wdt:P571 ?filingDate }}
  OPTIONAL {{ ?patent wdt:P577 ?pubDate }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?patent
LIMIT {limit}
OFFSET {offset}"""


def sparql_query(query: str) -> Optional[List[Dict]]:
    # GET preferred by Wikidata for cachability; POST as fallback
    qs = urllib.parse.urlencode({"query": query, "format": "json"})
    get_url = f"{WIKIDATA_SPARQL}?{qs}"
    post_body = urllib.parse.urlencode({"query": query}).encode("utf-8")

    for attempt in range(4):
        use_post = attempt % 2 == 1  # alternate GET/POST on retries
        if use_post:
            req = urllib.request.Request(
                WIKIDATA_SPARQL,
                data=post_body,
                headers={
                    "User-Agent": _UA,
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        else:
            req = urllib.request.Request(
                get_url,
                headers={
                    "User-Agent": _UA,
                    "Accept": "application/sparql-results+json",
                },
            )
        try:
            with urllib.request.urlopen(req, timeout=SPARQL_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = 2 ** (attempt + 3)
                log.warning("SPARQL rate-limit %s, retry in %ds", e.code, wait)
                time.sleep(wait)
                continue
            log.error("SPARQL HTTP %s (attempt %d, %s): %s",
                      e.code, attempt + 1, "POST" if use_post else "GET", e.reason)
            if e.code == 403 and not use_post:
                log.info("SPARQL GET 403 — will retry with POST")
                continue
            return None
        except Exception as e:
            log.error("SPARQL error (attempt %d): %s", attempt + 1, e)
            if attempt < 3:
                time.sleep(2 ** attempt)
    return None


def collect_patents(offset: int) -> Optional[List[Tuple]]:
    """Return rows ready for bulk_insert, or None on SPARQL failure."""
    log.info("Patents SPARQL offset=%d limit=%d", offset, PATENT_STEP)
    bindings = sparql_query(_PATENT_QUERY.format(limit=PATENT_STEP, offset=offset))
    if bindings is None:
        return None

    log.info("SPARQL returned %d bindings", len(bindings))
    t = now_iso()
    rows: List[Tuple] = []
    seen: set = set()

    for b in bindings:
        patent_uri   = b.get("patent",   {}).get("value", "")
        inventor_uri = b.get("inventor", {}).get("value", "")
        if not patent_uri:
            continue
        qid          = patent_uri.rsplit("/", 1)[-1]
        inventor_qid = inventor_uri.rsplit("/", 1)[-1] if inventor_uri else "none"
        rkey = f"{qid}-{inventor_qid}"
        if rkey in seen:
            continue
        seen.add(rkey)
        payload = {
            "$type":         PATENT_COL,
            "patentQid":     qid,
            "patentLabel":   b.get("patentLabel",   {}).get("value", ""),
            "inventorQid":   inventor_qid,
            "inventorLabel": b.get("inventorLabel", {}).get("value", ""),
            "filingDate":    b.get("filingDate",    {}).get("value", ""),
            "pubDate":       b.get("pubDate",       {}).get("value", ""),
            "source":        "wikidata",
            "sourceLicense": "CC0",
            "collectedAt":   t,
        }
        rows.append(make_row(PATENT_COL, rkey, payload, t))

    log.info("Patents: %d rows after dedup", len(rows))
    return rows


# ── Tranco + Cloudflare DoH ───────────────────────────────────────────────────

def _download_zip_list(url: str, cache_path: str, label: str,
                       col_rank: int = 0, col_domain: int = 1,
                       skip_header: bool = False) -> bool:
    """Download a zip or plain CSV domain list, normalise to 'rank,domain' lines."""
    log.info("Downloading %s…", label)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = resp.read()
        if url.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                raw = zf.read(zf.namelist()[0]).decode("utf-8", errors="replace")
        else:
            raw = data.decode("utf-8", errors="replace")
        lines = []
        for i, line in enumerate(raw.splitlines()):
            if skip_header and i == 0:
                continue
            parts = line.split(",")
            if len(parts) > max(col_rank, col_domain):
                try:
                    lines.append(f"{int(parts[col_rank])},{parts[col_domain].strip()}")
                except ValueError:
                    pass
        with open(cache_path, "w") as f:
            f.write("\n".join(lines))
        log.info("%s cached (%d domains)", label, len(lines))
        return True
    except Exception as exc:
        log.warning("%s download failed: %s", label, exc)
        return False


def ensure_tranco() -> bool:
    """Return True if a domain-list cache is ready (Tranco → Majestic → Umbrella)."""
    candidates = [
        (TRANCO_CACHE,   TRANCO_URL,   "Tranco top-1M",      0, 1, False),
        (MAJESTIC_CACHE, MAJESTIC_URL, "Majestic Million",   0, 2, True),
        (UMBRELLA_CACHE, UMBRELLA_URL, "Cisco Umbrella top-1M", 0, 1, False),
    ]
    for cache, url, label, cr, cd, hdr in candidates:
        if (
            os.path.exists(cache)
            and time.time() - os.path.getmtime(cache) < TRANCO_CACHE_TTL
        ):
            log.info("%s cache hit", label)
            return True
        if _download_zip_list(url, cache, label, cr, cd, hdr):
            return True
        log.warning("%s unavailable — trying next fallback", label)
    log.error("All domain-list sources exhausted — skipping DNS collection")
    return False


def _active_domain_cache() -> str:
    """Return the path of whichever domain-list cache is freshest."""
    for cache in (TRANCO_CACHE, MAJESTIC_CACHE, UMBRELLA_CACHE):
        if os.path.exists(cache):
            return cache
    return TRANCO_CACHE  # will fail gracefully in caller


def load_tranco_domains(offset: int, count: int) -> List[Tuple[int, str]]:
    result: List[Tuple[int, str]] = []
    with open(_active_domain_cache()) as f:
        for i, line in enumerate(f):
            if i < offset:
                continue
            if len(result) >= count:
                break
            parts = line.strip().split(",", 1)
            if len(parts) == 2:
                try:
                    result.append((int(parts[0]), parts[1].strip()))
                except ValueError:
                    pass
    return result


def doh_lookup(domain: str, rtype: str) -> Optional[Dict]:
    qs = urllib.parse.urlencode({"name": domain, "type": rtype})
    for base_url in DOH_URLS:
        url = f"{base_url}?{qs}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/dns-json", "User-Agent": _UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception as e:
            log.debug("DoH %s/%s via %s: %s", domain, rtype, base_url, e)
    return None


def collect_dns_domain(rank_domain: Tuple[int, str]) -> List[Tuple]:
    rank, domain = rank_domain
    t        = now_iso()
    hour_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    rows: List[Tuple] = []
    for rtype in DNS_RTYPES:
        result = doh_lookup(domain, rtype)
        if not result:
            continue
        answers = result.get("Answer", [])
        if not answers:
            continue
        safe_domain = domain.replace(".", "-")[:60]
        rkey = f"dns-{rank}-{safe_domain}-{rtype.lower()}-{hour_tag}"
        payload = {
            "$type":      DNS_COL,
            "domain":     domain,
            "rank":       rank,
            "recordType": rtype,
            "status":     result.get("Status", 0),
            "answers":    [
                {"name": a.get("name"), "ttl": a.get("TTL"), "data": a.get("data")}
                for a in answers
            ],
            "resolver":   "1.1.1.1",
            "source":     "cloudflare-doh",
            "observedAt": t,
        }
        rows.append(make_row(DNS_COL, rkey, payload, t))
    return rows


def collect_dns(dns_offset: int) -> List[Tuple]:
    if not ensure_tranco():
        log.warning("Tranco unavailable — skipping DNS collection")
        return []
    domains = load_tranco_domains(dns_offset, DNS_STEP)
    log.info("DNS collection: %d domains @ offset %d", len(domains), dns_offset)

    rows: List[Tuple] = []
    with ThreadPoolExecutor(max_workers=DNS_WORKERS) as ex:
        futs = {ex.submit(collect_dns_domain, d): d for d in domains}
        for fut in as_completed(futs):
            if not time_ok():
                log.warning("DNS: deadline reached, stopping early")
                ex.shutdown(wait=False, cancel_futures=True)
                break
            try:
                rows.extend(fut.result())
            except Exception as e:
                log.warning("DNS error for %s: %s", futs[fut], e)

    log.info("DNS collected %d rows from %d domains", len(rows), len(domains))
    return rows


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> Dict:
    state         = load_state()
    patent_offset = state["patent_offset"]
    dns_offset    = state["dns_offset"]

    log.info(
        "Run start — patent_offset=%d dns_offset=%d deadline=%.0fs",
        patent_offset, dns_offset, TIMEOUT_SECS,
    )

    collected = 0
    inserted  = 0
    patent_ok = True

    # 1. Patents — collect before touching DB so a DB outage doesn't lose the run
    patent_rows = collect_patents(patent_offset)
    if patent_rows is None:
        log.warning("Patent collection failed — offset not advanced")
        patent_ok = False
        patent_rows = []

    collected += len(patent_rows)

    # 2. DNS (skip if deadline already close)
    dns_rows: List[Tuple] = []
    if time_ok():
        dns_rows = collect_dns(dns_offset)
        collected += len(dns_rows)
    else:
        log.warning("Deadline reached before DNS collection — skipping")

    # 3. Insert all collected rows
    all_rows = patent_rows + dns_rows
    if all_rows:
        log.info("Inserting %d rows into vertex_repo_record…", len(all_rows))
        try:
            conn = db_connect()
            try:
                inserted += bulk_insert(conn, all_rows)
            except Exception as exc:
                log.error("DB insert failed: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()
        except psycopg2.OperationalError as exc:
            log.error("DB connection failed (data collected but not inserted): %s", exc)

    # Advance offsets; rotate patent at PATENT_MAX; reset to 0 if dataset exhausted
    if patent_ok:
        next_patent_offset = (patent_offset + PATENT_STEP) % PATENT_MAX
        if not patent_rows:
            log.info("Wikidata returned 0 results — resetting patent_offset to 0")
            next_patent_offset = 0
    else:
        next_patent_offset = patent_offset   # retry same page next run

    next_dns_offset = dns_offset + DNS_STEP

    save_state({"patent_offset": next_patent_offset, "dns_offset": next_dns_offset})

    result = {
        "collected":          collected,
        "inserted":           inserted,
        "next_patent_offset": next_patent_offset,
        "next_dns_offset":    next_dns_offset,
    }
    log.info(
        "Run complete in %.1fs — collected=%d inserted=%d "
        "next_patent_offset=%d next_dns_offset=%d",
        elapsed(), collected, inserted, next_patent_offset, next_dns_offset,
    )
    print(json.dumps(result))
    return result


if __name__ == "__main__":
    main()
