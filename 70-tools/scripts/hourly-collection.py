#!/usr/bin/env python3
"""Hourly batch: Wikidata patents + Cloudflare DNS → vertex_repo_record.

State file: /tmp/hourly-collection-state.json
Output (stdout, final line): JSON {collected, inserted, next_patent_offset, next_dns_offset}
"""
import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

# ── Config ────────────────────────────────────────────────────────────────────
RW_HOST = "<vendor-rw-host>"
RW_PORT = 4566
RW_USER = "root"
RW_DB   = "dev"

REPO               = "did:plc:etzhayyim-collector"
PATENT_COLLECTION  = "com.etzhayyim.apps.patent.patent"
DNS_COLLECTION     = "com.etzhayyim.apps.dns.observation"

STATE_FILE         = "/tmp/hourly-collection-state.json"
TRANCO_CACHE       = "/tmp/tranco_top1m.csv"
TRANCO_CACHE_TTL   = 86400   # seconds — refresh once per day

WIKIDATA_SPARQL    = "https://query.wikidata.org/sparql"
CF_DOH_URL         = "https://cloudflare-dns.com/dns-query"

PATENT_STEP        = 1000    # offset advances by this amount each run
PATENT_LIMIT       = 3000    # SPARQL LIMIT per run — rolling window for ~3k rows
PATENT_MAX_OFFSET  = 100_000  # rotate back to 0 after exhausting
DNS_STEP           = 500
DNS_START          = 10_000

TIMEOUT_S          = 50 * 60   # 50-min hard budget

_UA = "etzhayyim-collect/1.0 (https://etzhayyim.com; ops@etzhayyim.com) python-urllib/3"


# ── State ──────────────────────────────────────────────────────────────────────
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"patent_offset": 0, "dns_offset": DNS_START}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


# ── DB ─────────────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=RW_HOST, port=RW_PORT, user=RW_USER, dbname=RW_DB, connect_timeout=30
    )


def bulk_insert(conn, rows: list) -> None:
    cur = conn.cursor()
    try:
        cur.execute("SET dml_rate_limit TO 2000")
    except Exception:
        pass
    # RisingWave PK on uri — duplicate inserts overwrite with identical data (idempotent)
    psycopg2.extras.execute_values(
        cur,
        "INSERT INTO vertex_repo_record "
        "(uri,cid,collection,rkey,repo,repo_rev,value_json,indexed_at,takedown_ref,ts_ms,created_at) "
        "VALUES %s",
        rows,
        template="(%s,'',%s,%s,%s,'',%s,%s,NULL,%s,%s)",
        page_size=500,
    )
    conn.commit()
    cur.close()


# ── Wikidata SPARQL ────────────────────────────────────────────────────────────
def sparql_query(query: str) -> dict | None:
    # Wikidata requires POST for SPARQL; GET with query params often triggers 403
    body = urllib.parse.urlencode({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        WIKIDATA_SPARQL,
        data=body,
        headers={
            "User-Agent": _UA,
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = 2 ** (attempt + 3)
                print(f"  Wikidata rate-limit ({e.code}), waiting {wait}s…")
                time.sleep(wait)
                continue
            print(f"  Wikidata HTTP {e.code}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  Wikidata error (attempt {attempt+1}): {e}", file=sys.stderr)
            if attempt < 3:
                time.sleep(2 ** attempt)
    return None


def fetch_patents(offset: int, limit: int = PATENT_LIMIT) -> list:
    """Return rows ready for bulk_insert from Wikidata patent+inventor results."""
    query = f"""
SELECT ?patent ?patentLabel ?inventor ?inventorLabel ?filingDate ?pubDate WHERE {{
  ?patent wdt:P31 wd:Q253623 ;
          wdt:P61 ?inventor .
  OPTIONAL {{ ?patent wdt:P571 ?filingDate }}
  OPTIONAL {{ ?patent wdt:P577 ?pubDate }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?patent
LIMIT {limit}
OFFSET {offset}
"""
    result = sparql_query(query)
    if not result:
        return []

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_ms  = int(time.time() * 1000)
    rows    = []
    seen    = set()

    for b in result.get("results", {}).get("bindings", []):
        patent_uri  = b.get("patent", {}).get("value", "")
        inventor_uri = b.get("inventor", {}).get("value", "")
        if not patent_uri:
            continue

        qid          = patent_uri.rsplit("/", 1)[-1]
        inventor_qid = inventor_uri.rsplit("/", 1)[-1] if inventor_uri else "none"
        rkey         = f"{qid}-{inventor_qid}"
        if rkey in seen:
            continue
        seen.add(rkey)

        val = {
            "$type":         PATENT_COLLECTION,
            "patentQid":     qid,
            "patentLabel":   b.get("patentLabel",   {}).get("value", ""),
            "inventorQid":   inventor_qid,
            "inventorLabel": b.get("inventorLabel", {}).get("value", ""),
            "filingDate":    b.get("filingDate",    {}).get("value", ""),
            "pubDate":       b.get("pubDate",       {}).get("value", ""),
            "source":        "wikidata",
            "sourceLicense": "CC0",
            "collectedAt":   now_iso,
        }
        uri = f"at://{REPO}/{PATENT_COLLECTION}/{rkey}"
        rows.append((uri, PATENT_COLLECTION, rkey, REPO,
                     json.dumps(val, ensure_ascii=False), now_iso, now_ms, now_iso))

    return rows


# ── Tranco + Cloudflare DNS ────────────────────────────────────────────────────
def refresh_tranco_cache() -> bool:
    if os.path.exists(TRANCO_CACHE):
        age = time.time() - os.path.getmtime(TRANCO_CACHE)
        if age < TRANCO_CACHE_TTL:
            return True

    print("  Downloading Tranco top-1M list…")
    url = "https://tranco-list.eu/top-1m.csv.zip"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        z = zipfile.ZipFile(io.BytesIO(data))
        with z.open(z.namelist()[0]) as src, open(TRANCO_CACHE, "wb") as dst:
            dst.write(src.read())
        print(f"  Tranco cached → {TRANCO_CACHE}")
        return True
    except Exception as e:
        print(f"  Tranco download failed: {e}", file=sys.stderr)
        return False


def read_tranco_slice(offset: int, count: int) -> list[tuple[int, str]]:
    domains: list[tuple[int, str]] = []
    try:
        with open(TRANCO_CACHE) as f:
            for i, line in enumerate(f):
                if i < offset:
                    continue
                if len(domains) >= count:
                    break
                parts = line.strip().split(",", 1)
                if len(parts) == 2:
                    try:
                        domains.append((int(parts[0]), parts[1].strip()))
                    except ValueError:
                        pass
    except Exception as e:
        print(f"  Tranco read error: {e}", file=sys.stderr)
    return domains


def cf_dns_lookup(domain: str, qtype: str = "A") -> dict | None:
    url = f"{CF_DOH_URL}?name={urllib.parse.quote(domain)}&type={qtype}"
    req = urllib.request.Request(
        url, headers={"Accept": "application/dns-json", "User-Agent": _UA}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def fetch_dns(dns_offset: int) -> list:
    """Return rows for bulk_insert from Cloudflare DNS observations."""
    if not refresh_tranco_cache():
        return []

    domains = read_tranco_slice(dns_offset, DNS_STEP)
    print(f"  DNS lookups: {len(domains)} domains (offset={dns_offset})…")

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_ms  = int(time.time() * 1000)
    hour_tag = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    rows    = []

    for rank, domain in domains:
        result_a = cf_dns_lookup(domain, "A")
        a_records = []
        status    = -1
        if result_a is not None:
            status = result_a.get("Status", -1)
            for ans in result_a.get("Answer", []):
                if ans.get("type") == 1:   # A record
                    a_records.append(ans.get("data", ""))

        # rkey encodes rank + hour so each hourly run is a distinct observation
        safe_domain = domain.replace(".", "-")[:60]
        rkey = f"dns-{rank}-{safe_domain}-{hour_tag}"

        val = {
            "$type":      DNS_COLLECTION,
            "domain":     domain,
            "rank":       rank,
            "aRecords":   a_records,
            "dnsStatus":  status,
            "resolver":   "cloudflare-dns.com",
            "source":     "cloudflare-doh",
            "observedAt": now_iso,
        }
        uri = f"at://{REPO}/{DNS_COLLECTION}/{rkey}"
        rows.append((uri, DNS_COLLECTION, rkey, REPO,
                     json.dumps(val, ensure_ascii=False), now_iso, now_ms, now_iso))

        time.sleep(0.05)   # ≤20 req/s toward Cloudflare DoH

    return rows


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    t0    = time.time()
    state = load_state()

    patent_offset = int(state.get("patent_offset", 0))
    dns_offset    = int(state.get("dns_offset",    DNS_START))

    print(f"[{datetime.now(timezone.utc).isoformat()}] hourly-collection start")
    print(f"  patent_offset={patent_offset}  dns_offset={dns_offset}")

    all_rows: list = []

    # 1. Wikidata patents
    print(f"  Fetching patents (offset={patent_offset}, limit={PATENT_LIMIT})…")
    patent_rows = fetch_patents(patent_offset)
    print(f"  Patents collected: {len(patent_rows)}")
    all_rows.extend(patent_rows)

    # Advance patent offset; rotate at PATENT_MAX_OFFSET
    # If Wikidata returned 0 rows, the offset is past the dataset end — reset to 0
    next_patent_offset = (patent_offset + PATENT_STEP) % PATENT_MAX_OFFSET
    if not patent_rows:
        print("  No patent rows returned — resetting patent offset to 0")
        next_patent_offset = 0

    # 2. Cloudflare DNS (only if time budget allows)
    if time.time() - t0 < TIMEOUT_S - 600:
        dns_rows = fetch_dns(dns_offset)
        print(f"  DNS observations collected: {len(dns_rows)}")
        all_rows.extend(dns_rows)
    else:
        print("  DNS skipped — approaching time budget")
        dns_rows = []

    next_dns_offset = dns_offset + DNS_STEP

    # 3. Insert to RisingWave
    inserted = 0
    if all_rows:
        print(f"  Inserting {len(all_rows)} rows into vertex_repo_record…")
        try:
            conn = get_conn()
            try:
                bulk_insert(conn, all_rows)
                inserted = len(all_rows)
            except Exception as e:
                print(f"  DB insert error: {e}", file=sys.stderr)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                conn.close()
        except psycopg2.OperationalError as e:
            print(f"  DB connection failed (rows collected but not inserted): {e}", file=sys.stderr)

    # 4. Persist state
    new_state = {
        "patent_offset": next_patent_offset,
        "dns_offset":    next_dns_offset,
        "last_run":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_state(new_state)

    elapsed = round(time.time() - t0, 1)
    result  = {
        "collected":          len(all_rows),
        "inserted":           inserted,
        "next_patent_offset": next_patent_offset,
        "next_dns_offset":    next_dns_offset,
        "elapsed_s":          elapsed,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
