#!/usr/bin/env python3
"""Phase 5: Inject Common Crawl domains as DID actors + site.domain records to PDS.

Reads Phase 3 output (domains_for_classification.jsonl.gz or Cypher batch files),
creates DID actors (com.atproto.identity.create) and domain metadata records
(com.etzhayyim.apps.site.domain) in PDS via XRPC.

DID hierarchy:
  did:web:site.etzhayyim.com                          (APP primary, existing)
  did:web:site.etzhayyim.com:{domain-slug}            (domain DID, created here)

Usage:
  python3 phase5_inject_did.py --limit 100 --dry-run
  python3 phase5_inject_did.py --limit 500 --batch-size 50
  python3 phase5_inject_did.py --min-pages 10

TODO(substrate-boundary): remove any RW integration that reads domain intelligence
from RW before PDS injection. Phase 5 should read from MST via @etzhayyim/sdk
per ADR-2605172000 (already mostly PDS-side, just drop RW fallback).
"""

import gzip
import json
import os
import sys
import time
import logging
import argparse
import signal
from pathlib import Path
from urllib.parse import quote

import requests

# ── Config ──

BASE_DIR = Path(os.environ.get("CC_DATA_DIR", "/Volumes/251220/CC/2603"))
GRAPH_DIR = BASE_DIR / "graph"
# State file falls back to /tmp when CC_DATA_DIR doesn't exist
_state_dir = BASE_DIR / "scripts" if (BASE_DIR / "scripts").exists() else Path("/tmp")
STATE_FILE = _state_dir / ".phase5_state.json"
PDS_URL = os.environ.get("PDS_URL", "https://atproto.etzhayyim.com")
SITE_APP_DID = "did:web:site.etzhayyim.com"

# Auth token from etzhayyim auth
AUTH_TOKEN_FILE = Path.home() / ".etzhayyim" / "auth.json"

_log_handlers = [logging.StreamHandler()]
_phase5_log = BASE_DIR / "scripts" / "phase5.log"
if _phase5_log.parent.exists():
    _log_handlers.append(logging.FileHandler(_phase5_log))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=_log_handlers,
)
log = logging.getLogger(__name__)

shutdown_requested = False


def handle_signal(signum, frame):
    """Set graceful shutdown flag."""
    global shutdown_requested
    log.info("Shutdown requested...")
    shutdown_requested = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def get_auth_token() -> str:
    """Resolve auth token from etzhayyim_TOKEN env or ~/.etzhayyim/auth.json."""
    token = os.environ.get("etzhayyim_TOKEN", "")
    if token:
        return token
    if AUTH_TOKEN_FILE.exists():
        try:
            data = json.loads(AUTH_TOKEN_FILE.read_text())
            return data.get("id_token", data.get("access_token", ""))
        except Exception:
            pass
    return ""


def xrpc_call(nsid: str, body: dict, token: str) -> dict:
    """Call PDS XRPC endpoint via internal auth + active DID override."""
    url = f"{PDS_URL}/xrpc/{nsid}"
    headers = {
        "Content-Type": "application/json",
        "x-kotodama-verified": "true",
        "X-Active-DID": SITE_APP_DID,
    }
    resp = requests.post(url, json=body, headers=headers, timeout=120)
    if resp.status_code >= 400:
        log.error(f"XRPC {nsid} failed: {resp.status_code} {resp.text[:200]}")
        return {"error": resp.text[:200]}
    try:
        return resp.json()
    except Exception:
        return {"ok": True}


def load_domains_from_jsonl(jsonl_path: Path, min_pages: int = 0, limit: int = 0) -> list[dict]:
    """Load domain records from Phase 3 JSONL output."""
    domains = []
    opener = gzip.open if str(jsonl_path).endswith(".gz") else open
    with opener(jsonl_path, "rt") as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            if min_pages > 0 and d.get("pageCount", 0) < min_pages:
                continue
            domains.append(d)
            if limit > 0 and len(domains) >= limit:
                break
    # Sort by page count descending (inject most important first)
    domains.sort(key=lambda x: x.get("pageCount", 0), reverse=True)
    return domains


def load_domains_from_cypher(graph_dir: Path, limit: int = 0) -> list[dict]:
    """Extract unique domains from Phase 3 Cypher batch files."""
    import re
    domains: dict[str, dict] = {}
    pattern = re.compile(r'MERGE \(d:CcDomain \{name: "([^"]+)"\}\).*d\.did = "([^"]+)".*d\.slug = "([^"]+)"')
    topic_pattern = re.compile(r'd\.topics = (\[.*?\])')

    cypher_files = sorted(graph_dir.glob("batch_*.cypher"))
    for cf in cypher_files:
        for line in open(cf):
            m = pattern.search(line)
            if m:
                name, did, slug = m.group(1), m.group(2), m.group(3)
                if name not in domains:
                    topics = []
                    tm = topic_pattern.search(line)
                    if tm:
                        try:
                            topics = json.loads(tm.group(1))
                        except Exception:
                            pass
                    domains[name] = {"domain": name, "did": did, "slug": slug, "topics": topics, "pageCount": 1}
                else:
                    domains[name]["pageCount"] = domains[name].get("pageCount", 0) + 1
        if limit > 0 and len(domains) >= limit:
            break

    result = sorted(domains.values(), key=lambda x: x.get("pageCount", 0), reverse=True)
    return result[:limit] if limit > 0 else result


def load_state() -> dict:
    """Load inject resume state."""
    if STATE_FILE.exists():
        try:
            return json.load(open(STATE_FILE))
        except Exception:
            pass
    return {}


def save_state(state: dict):
    """Save inject resume state atomically."""
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.rename(STATE_FILE)


def inject_domains(domains: list[dict], dry_run: bool, batch_size: int):
    """Create DID actors + site.domain records in PDS for each domain."""
    token = get_auth_token()
    if not token and not dry_run:
        log.error("No auth token. Run 'etzhayyim auth login' first or set etzhayyim_TOKEN.")
        sys.exit(1)

    state = load_state()
    last_injected = state.get("lastInjectedDomain", "")
    skip = bool(last_injected)

    created_count = 0
    error_count = 0
    skipped_count = 0
    start_time = time.time()

    for i, domain in enumerate(domains):
        if shutdown_requested:
            break

        domain_name = domain["domain"]
        slug = domain.get("slug", domain_name.replace(".", "-").replace("_", "-"))
        did = domain.get("did", f"did:web:site.etzhayyim.com:{slug}")
        topics = domain.get("topics", [])
        page_count = domain.get("pageCount", 0)
        sample_titles = domain.get("sampleTitles", [])

        # Resume: skip already-injected
        if skip:
            if domain_name == last_injected:
                skip = False
            skipped_count += 1
            continue

        display_name = domain_name
        description = f"[AI Agent — unofficial] Internet domain: {domain_name}"
        if sample_titles:
            description += f" | Sample: {sample_titles[0][:100]}"

        if dry_run:
            log.info(f"  [DRY-RUN] {i+1}/{len(domains)}: {did} ({page_count} pages, topics={topics})")
            created_count += 1
            continue

        # 1. Create DID actor (com.atproto.identity.create)
        # hostDid tells PDS to create the DID under site.etzhayyim.com namespace
        # documentJson carries displayName/description for profile auto-creation
        doc = {
            "displayName": display_name,
            "description": description,
            "domain": domain_name,
            "pageCount": page_count,
            "topics": topics,
        }
        result = xrpc_call("com.atproto.identity.create", {
            "path": slug,
            "hostDid": SITE_APP_DID,
            "documentJson": json.dumps(doc),
        }, token)

        if "error" in result:
            # DID may already exist — try to continue
            error_count += 1
            if error_count > 20:
                log.error("Too many errors, stopping")
                break
        else:
            log.info(f"  DID created: {result.get('did', did)}")

        # 2. Create site.domain record
        domain_record = {
            "domain": domain_name,
            "slug": slug,
            "did": did,
            "pageCount": page_count,
            "topics": topics,
            "source": "common-crawl",
            "crawl": "CC-MAIN-2026-12",
        }
        xrpc_call("com.atproto.repo.createRecord", {
            "repo": SITE_APP_DID,
            "collection": "com.etzhayyim.apps.site.domain",
            "rkey": domain_name,  # use domain as rkey so mv_cc_domain_coverage JOIN matches
            "record": domain_record,
        }, token)

        created_count += 1

        # Rate limit: ~5 req/s to avoid PDS overload
        if created_count % batch_size == 0:
            elapsed = time.time() - start_time
            rate = created_count / elapsed if elapsed > 0 else 0
            log.info(f"  Progress: {created_count}/{len(domains)} ({rate:.1f}/s), errors={error_count}")
            time.sleep(0.5)

        # Save state periodically
        if created_count % 10 == 0:
            save_state({
                "lastInjectedDomain": domain_name,
                "createdCount": created_count,
                "errorCount": error_count,
                "skippedCount": skipped_count,
                "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

    # Final state save
    elapsed = time.time() - start_time
    save_state({
        "lastInjectedDomain": domain_name if domains else "",
        "createdCount": created_count,
        "errorCount": error_count,
        "skippedCount": skipped_count,
        "completed": not shutdown_requested,
        "elapsedSeconds": round(elapsed, 1),
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    status = "interrupted" if shutdown_requested else "completed"
    log.info(f"Phase 5 {status}: {created_count} created, {error_count} errors, {skipped_count} skipped, {elapsed:.0f}s")


# CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
def load_domains_from_risingwave(limit: int = 0) -> list[dict]:
    """Load gap domains directly from RisingWave.

    Uses direct LEFT JOIN on vertex_actor (mv_cc_domain_coverage was removed).
    Topics are read from vertex_domain.topics (set by phase4 LLM extraction).
    """
    import psycopg2 as _pg
    RW_HOST = os.environ.get("RW_HOST", "45.32.79.245")
    RW_PORT = int(os.environ.get("RW_PORT", "4566"))
    conn = _pg.connect(host=RW_HOST, port=RW_PORT, user="root", dbname="dev", connect_timeout=10)
    cur = conn.cursor()

    sql = """
        SELECT vd.vertex_id, vd.domain, vd.topics
        FROM vertex_domain vd
        LEFT JOIN vertex_actor va
          ON va.collection = 'com.etzhayyim.apps.site.domain' AND va.rkey = vd.domain
        WHERE va.rkey IS NULL
          AND vd.domain LIKE '%.%'
          AND vd.domain ~ '^[a-zA-Z0-9]'
          AND length(vd.domain) <= 100
          AND vd.domain NOT LIKE '.%'
          AND vd.domain NOT LIKE '% %'
        ORDER BY vd.domain
    """
    if limit > 0:
        sql += f" LIMIT {limit}"
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()

    domains = []
    for vid, domain, topics_raw in rows:
        topics = []
        if topics_raw:
            try:
                parsed = json.loads(topics_raw)
                if isinstance(parsed, list):
                    topics = parsed
                elif isinstance(parsed, dict):
                    topics = parsed.get("services", [])
            except Exception:
                pass
        slug = domain.replace(".", "-")
        did = f"did:web:site.etzhayyim.com:{slug}"
        domains.append({
            "domain": domain,
            "did": did,
            "slug": slug,
            "pageCount": 0,
            "topics": topics,
        })
    return domains


def main():
    parser = argparse.ArgumentParser(description="Phase 5: Inject CC domains as DID actors to PDS")
    parser.add_argument("--source", choices=["jsonl", "cypher"], default="jsonl",
                        help="Data source: jsonl (domains_for_classification.jsonl.gz) or cypher (batch_*.cypher)")
    parser.add_argument("--from-rw", action="store_true",
                        help="Read gap domains directly from RisingWave mv_cc_domain_coverage (no local files needed)")
    parser.add_argument("--limit", type=int, default=0, help="Max domains to inject (0=all)")
    parser.add_argument("--min-pages", type=int, default=0, help="Only domains with >= N pages")
    parser.add_argument("--batch-size", type=int, default=50, help="Progress log interval")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no PDS writes")
    parser.add_argument("--reset", action="store_true", help="Reset inject state")
    parser.add_argument("--pds", default="", help="PDS URL override")
    args = parser.parse_args()

    global PDS_URL
    if args.pds:
        PDS_URL = args.pds

    if args.reset and STATE_FILE.exists():
        STATE_FILE.unlink()
        log.info("Inject state reset")

    # Load domains
    if args.from_rw:
        log.info("Loading gap domains from RisingWave mv_cc_domain_coverage…")
        domains = load_domains_from_risingwave(args.limit)
    elif args.source == "jsonl":
        jsonl_path = GRAPH_DIR / "domains_for_classification.jsonl.gz"
        if not jsonl_path.exists():
            log.error(f"JSONL not found: {jsonl_path}. Run phase3 first.")
            sys.exit(1)
        domains = load_domains_from_jsonl(jsonl_path, args.min_pages, args.limit)
    else:
        domains = load_domains_from_cypher(GRAPH_DIR, args.limit)

    log.info(f"Phase 5: {len(domains)} domains to inject (source={args.source}, dry_run={args.dry_run})")

    if not domains:
        log.warning("No domains to inject")
        return

    # Show top 5 domains
    for d in domains[:5]:
        log.info(f"  Top: {d['domain']} ({d.get('pageCount', 0)} pages, topics={d.get('topics', [])})")

    inject_domains(domains, args.dry_run, args.batch_size)


if __name__ == "__main__":
    main()
