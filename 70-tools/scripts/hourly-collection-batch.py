#!/usr/bin/env python3
"""
Hourly data collection batch.
Collects patents from Wikidata SPARQL and DNS observations via Cloudflare DoH.
Inserts directly into RisingWave vertex_repo_record table.

Sources
-------
  Wikidata SPARQL  — patents with inventors (wdt:P61)
                     LIMIT 3000 rolling window, offset advances 1000 each run
  Cloudflare DoH   — A/AAAA/MX records for 500 Tranco top-1M domains
                     offset advances 500 each run, starting at 10 000

Sink
----
  RisingWave vertex_repo_record (psycopg2 → <vendor-rw-host-deprecated>:4566)

State
-----
  /tmp/hourly-collection-state.json  { patent_offset, dns_offset }

Stdout (final line)
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

# ── config ────────────────────────────────────────────────────────────────────────────

STATE_FILE     = "/tmp/hourly-collection-state.json"

RW_HOST     = "<vendor-rw-host-deprecated>"
RW_PORT     = 4566
RW_USER     = "root"
RW_DB       = "dev"
RW_PASSWORD = ""

REPO_DID    = "did:plc:etzhayyim-collector"
PATENT_COL  = "com.etzhayyim.apps.patent.patent"
DNS_COL     = "com.etzhayyim.apps.dns.observation"

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
DOH_URL         = "https://cloudflare-dns.com/dns-query"
DOH_FALLBACK    = "https://dns.google/resolve"

# Domain list sources: tried in order until one succeeds
_DOMAIN_SOURCES = [
    ("Tranco top-1M",         "https://tranco-list.eu/top-1m.csv.zip",
     "/tmp/tranco_top1m.txt",      0, 1, False),
    ("Majestic Million",      "https://downloads.majestic.com/majestic_million.csv",
     "/tmp/majestic_million.txt",  0, 2, True),
    ("Cisco Umbrella top-1M", "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip",
     "/tmp/umbrella_top1m.txt",    0, 1, False),
]
DOMAIN_CACHE_TTL = 86_400   # 24 h

TIMEOUT_SECS = 50 * 60      # 50-min hard deadline (10-min margin for next cron)
PATENT_STEP  = 1_000        # SPARQL OFFSET advances by this each run
PATENT_LIMIT = 3_000        # SPARQL LIMIT per run — rolling window for ~3k rows
PATENT_MAX   = 100_000      # wrap offset back to 0 after this
DNS_STEP     = 500
DNS_START    = 10_000
DNS_WORKERS  = 20
INSERT_PAGE  = 500
SPARQL_TIMEOUT = 90         # seconds

_UA = "etzhayyim-collector/1.0 (https://etzhayyim.com; ops@etzhayyim.com)"

# ── logging ─────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

_t0       = time.monotonic()
_deadline = _t0 + TIMEOUT_SECS


def time_ok() -> bool:
    return time.monotonic() < _deadline


def elapsed() -> float:
    return time.monotonic() - _t0


# ── state ─────────────────────────────────────────────────────────────────────────────

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


# ── row helpers ───────────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_ms() -> int:
    return int(time.time() * 1_000)


_COLS = (
    "uri", "cid", "collection", "rkey", "repo", "repo_rev",
    "value_json", "indexed_at", "takedown_ref", "ts_ms", "created_at",
)


def make_row(collection: str, rkey: str, payload: Any, t: str, ms: int) -> Tuple:
    vj = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return (
        f"at://{REPO_DID}/{collection}/{rkey}",  # uri
        "",                                        # cid (synthetic)
        collection,
        rkey,
        REPO_DID,                                  # repo
        "",                                        # repo_rev
        vj,                                        # value_json
        t,                                         # indexed_at
        None,                                      # takedown_ref
        ms,                                        # ts_ms
        t,                                         # created_at
    )


# ── database ───────────────────────────────────────────────────────────────────────────

def db_connect():
    return psycopg2.connect(
        host=RW_HOST, port=RW_PORT, user=RW_USER,
        password=RW_PASSWORD, dbname=RW_DB, connect_timeout=30,
    )


def bulk_insert(conn, rows: List[Tuple]) -> int:
    if not rows:
        return 0
    cur = conn.cursor()
    # Throttle bulk inserts — protects B2 Hummock quota (ADR-0048 / rw-bulk-insert-throttle)
    try:
        cur.execute("SET dml_rate_limit TO 2000")
    except Exception:
        pass
    col_str = ",".join(f'"{c}"' for c in _COLS)
    psycopg2.extras.execute_values(
        cur,
        f"INSERT INTO vertex_repo_record ({col_str}) VALUES %s",
        rows,
        page_size=INSERT_PAGE,
    )
    conn.commit()
    cur.close()
    return len(rows)


# ── Wikidata SPARQL ───────────────────────────────────────────────────────────────────

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
    post_body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    qs_params = urllib.parse.urlencode({"query": query, "format": "json"})
    get_url   = f"{WIKIDATA_SPARQL}?{qs_params}"

    for attempt in range(4):
        use_post = attempt % 2 == 1  # alternate GET / POST on retries
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
                headers={"User-Agent": _UA, "Accept": "application/sparql-results+json"},
            )
        try:
            with urllib.request.urlopen(req, timeout=SPARQL_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))["results"]["bindings"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = 2 ** (attempt + 3)
                log.warning("SPARQL %s — retry in %ds", e.code, wait)
                time.sleep(wait)
                continue
            log.error("SPARQL HTTP %s (attempt %d, %s): %s",
                      e.code, attempt + 1, "POST" if use_post else "GET", e.reason)
            if e.code == 403 and not use_post:
                continue   # retry with POST
            return None
        except Exception as exc:
            log.error("SPARQL error (attempt %d): %s", attempt + 1, exc)
            if attempt < 3:
                time.sleep(2 ** attempt)
    return None


def collect_patents(offset: int) -> Optional[List[Tuple]]:
    log.info("Patents SPARQL offset=%d limit=%d", offset, PATENT_LIMIT)
    bindings = sparql_query(_PATENT_QUERY.format(limit=PATENT_LIMIT, offset=offset))
    if bindings is None:
        return None

    log.info("SPARQL returned %d bindings", len(bindings))
    t  = now_iso()
    ms = ts_ms()
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
        rows.append(make_row(PATENT_COL, rkey, payload, t, ms))

    log.info("Patents: %d rows (after dedup)", len(rows))
    return rows


# ── domain list cache ──────────────────────────────────────────────────────────────────

def _download_domain_list(url: str, cache: str, label: str,
                          col_rank: int, col_domain: int,
                          skip_header: bool) -> bool:
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
        with open(cache, "w") as f:
            f.write("\n".join(lines))
        log.info("%s cached — %d domains", label, len(lines))
        return True
    except Exception as exc:
        log.warning("%s download failed: %s", label, exc)
        return False


def _active_cache() -> Optional[str]:
    for label, url, cache, cr, cd, hdr in _DOMAIN_SOURCES:
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < DOMAIN_CACHE_TTL:
            log.info("%s cache hit", label)
            return cache
        if _download_domain_list(url, cache, label, cr, cd, hdr):
            return cache
        log.warning("%s unavailable — trying next source", label)
    log.error("All domain-list sources exhausted")
    return None


def load_domains(offset: int, count: int) -> List[Tuple[int, str]]:
    cache = _active_cache()
    if not cache:
        return []
    result: List[Tuple[int, str]] = []
    try:
        with open(cache) as f:
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
    except Exception as exc:
        log.error("Domain cache read error: %s", exc)
    return result


# ── Cloudflare DNS-over-HTTPS ─────────────────────────────────────────────────────────

def _doh_lookup(domain: str, rtype: str) -> Optional[Dict]:
    qs = urllib.parse.urlencode({"name": domain, "type": rtype})
    for base in (DOH_URL, DOH_FALLBACK):
        req = urllib.request.Request(
            f"{base}?{qs}",
            headers={"Accept": "application/dns-json", "User-Agent": _UA},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception:
            pass
    return None


def _collect_domain(rank_domain: Tuple[int, str]) -> List[Tuple]:
    rank, domain = rank_domain
    t    = now_iso()
    ms   = ts_ms()
    hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    rows: List[Tuple] = []

    for rtype in ("A", "AAAA", "MX"):
        result = _doh_lookup(domain, rtype)
        if not result:
            continue
        answers = result.get("Answer", [])
        if not answers:
            continue
        safe = domain.replace(".", "-")[:50]
        rkey = f"dns-{rank}-{safe}-{rtype.lower()}-{hour}"
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
            "resolver":   "cloudflare-doh",
            "observedAt": t,
        }
        rows.append(make_row(DNS_COL, rkey, payload, t, ms))
    return rows


def collect_dns(dns_offset: int) -> List[Tuple]:
    domains = load_domains(dns_offset, DNS_STEP)
    if not domains:
        log.warning("No domains loaded — skipping DNS collection")
        return []
    log.info("DNS collection: %d domains @ offset %d", len(domains), dns_offset)

    rows: List[Tuple] = []
    with ThreadPoolExecutor(max_workers=DNS_WORKERS) as ex:
        futs = {ex.submit(_collect_domain, d): d for d in domains}
        for fut in as_completed(futs):
            if not time_ok():
                log.warning("DNS: deadline reached, stopping early")
                ex.shutdown(wait=False, cancel_futures=True)
                break
            try:
                rows.extend(fut.result())
            except Exception as exc:
                log.warning("DNS error for %s: %s", futs[fut], exc)

    log.info("DNS: %d rows from %d domains", len(rows), len(domains))
    return rows


# ── main ──────────────────────────────────────────────────────────────────────────────

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

    # 1. Collect patents from Wikidata
    patent_rows = collect_patents(patent_offset)
    if patent_rows is None:
        log.warning("Patent SPARQL failed — offset retained for retry")
        patent_ok = False
        patent_rows = []
    collected += len(patent_rows)

    # 2. Collect DNS observations
    dns_rows: List[Tuple] = []
    if time_ok():
        dns_rows = collect_dns(dns_offset)
        collected += len(dns_rows)
    else:
        log.warning("Deadline reached before DNS collection — skipping")

    # 3. Insert all rows
    all_rows = patent_rows + dns_rows
    if all_rows:
        log.info("Inserting %d rows into vertex_repo_record…", len(all_rows))
        try:
            conn = db_connect()
            try:
                inserted = bulk_insert(conn, all_rows)
                log.info("Inserted %d rows", inserted)
            except Exception as exc:
                log.error("DB insert failed: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()
        except psycopg2.OperationalError as exc:
            log.error("DB connect failed (data collected but not inserted): %s", exc)

    # 4. Advance offsets
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
