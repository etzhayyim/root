#!/usr/bin/env python3
"""Phase 5b: Inject page records + link edges from Phase 3 Cypher batches to the Kagami graph adapter.

Reads batch_*.cypher → extracts PageRecord, HOSTS_PAGE, LINKS_TO →
writes directly to the graph adapter /write endpoint (P10v2 per-label tables).

Filters to only domains that have been registered via Phase 5 (DID exists in vertex_did).

Usage:
  python3 phase5b_inject_pages.py --limit 10 --dry-run
  python3 phase5b_inject_pages.py --domain github.com
  python3 phase5b_inject_pages.py --all-registered
"""

import json
import os
import re
import sys
import time
import logging
import argparse
import signal
from pathlib import Path

import requests

BASE_DIR = Path(os.environ.get("CC_DATA_DIR", "/Volumes/251220/CC/2603"))
GRAPH_DIR = BASE_DIR / "graph"
STATE_FILE = BASE_DIR / "scripts" / ".phase5b_state.json"
ADAPTER_URL = os.environ.get("ADAPTER_URL", "http://172-236-135-21.ip.linodeusercontent.com")
ADAPTER_TOKEN = os.environ.get("ADAPTER_TOKEN", "kagami-linode-2604")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "scripts" / "phase5b.log"),
    ],
)
log = logging.getLogger(__name__)

shutdown_requested = False


def handle_signal(signum, frame):
    global shutdown_requested
    shutdown_requested = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def adapter_query(sql: str) -> list[dict]:
    """Execute SQL via adapter /query."""
    resp = requests.post(
        f"{ADAPTER_URL}/query",
        json={"sql": sql},
        headers={"Authorization": f"Bearer {ADAPTER_TOKEN}"},
        timeout=15,
    )
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("rows", [])


def adapter_write(records: list[dict], retries: int = 2) -> dict:
    """Write records via adapter /write (P10v2 _table routing)."""
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                f"{ADAPTER_URL}/write",
                json={"records": records},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ADAPTER_TOKEN}",
                },
                timeout=60,
            )
            return resp.json()
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
            else:
                raise


def get_registered_domains() -> set[str]:
    """Get domains already registered in vertex_did."""
    rows = adapter_query(
        "SELECT did FROM vertex_did WHERE did LIKE 'did:web:site.etzhayyim.com:%'"
    )
    domains = set()
    for r in rows:
        did = r.get("did", "")
        if did.startswith("did:web:site.etzhayyim.com:"):
            slug = did.split("did:web:site.etzhayyim.com:")[1]
            domains.add(slug)
    return domains


def parse_cypher_page(line: str) -> dict | None:
    """Extract PageRecord data from Cypher MERGE statement (full or short format)."""
    # Full metadata format (from page scan)
    m = re.match(
        r'MERGE \(p:PageRecord \{rkey: "([^"]+)"\}\) ON CREATE SET '
        r'p\.url = "([^"]*)", '
        r'p\.domainDid = "([^"]*)", '
        r'p\.domain = "([^"]*)", '
        r'p\.title = "([^"]*)", '
        r'p\.description = "([^"]*)", '
        r'p\.language = "([^"]*)", '
        r'p\.contentType = "([^"]*)", '
        r'p\.statusCode = "([^"]*)", '
        r'p\.outlinkCount = (\d+), '
        r'p\.crawl = "([^"]*)"',
        line,
    )
    if m:
        return {
            "rkey": m.group(1), "url": m.group(2), "domain_did": m.group(3),
            "domain": m.group(4), "title": m.group(5), "description": m.group(6),
            "language": m.group(7), "content_type": m.group(8),
            "outlink_count": int(m.group(10)), "crawl": m.group(11),
        }
    # Short format (outlink target — tp:PageRecord)
    m2 = re.match(
        r'MERGE \(tp:PageRecord \{rkey: "([^"]+)"\}\) ON CREATE SET '
        r'tp\.url = "([^"]*)", '
        r'tp\.domainDid = "([^"]*)", '
        r'tp\.domain = "([^"]*)"',
        line,
    )
    if m2:
        return {
            "rkey": m2.group(1), "url": m2.group(2), "domain_did": m2.group(3),
            "domain": m2.group(4), "title": "", "description": "",
            "language": "", "content_type": "", "outlink_count": 0, "crawl": "",
        }
    return None


def parse_cypher_hosts_page(line: str) -> tuple[str, str] | None:
    """Extract HOSTS_PAGE edge from Cypher."""
    m = re.match(
        r'MATCH \(d:DomainDID \{did: "([^"]+)"\}\), \(p:PageRecord \{rkey: "([^"]+)"\}\) MERGE \(d\)-\[:HOSTS_PAGE\]->\(p\)',
        line,
    )
    return (m.group(1), m.group(2)) if m else None


def parse_cypher_links_to(line: str) -> tuple[str, str] | None:
    """Extract LINKS_TO edge from Cypher."""
    m = re.match(
        r'MATCH \(s:PageRecord \{rkey: "([^"]+)"\}\), \(t:PageRecord \{rkey: "([^"]+)"\}\) MERGE \(s\)-\[:LINKS_TO\]->\(t\)',
        line,
    )
    return (m.group(1), m.group(2)) if m else None


def process_batch_file(
    cypher_path: Path,
    registered_slugs: set[str],
    dry_run: bool,
    batch_size: int = 500,
) -> dict:
    """Process a single Cypher batch file → graph adapter writes."""
    pages = []
    hosts_edges = []
    links_edges = []
    seen_rkeys = set()

    with open(cypher_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # PageRecord with full metadata
            page = parse_cypher_page(line)
            if page:
                # Filter: only pages belonging to registered domains
                slug = page["domain_did"].replace("did:web:site.etzhayyim.com:", "")
                if slug not in registered_slugs:
                    continue
                if page["rkey"] in seen_rkeys:
                    continue
                seen_rkeys.add(page["rkey"])
                pages.append(page)
                continue

            # HOSTS_PAGE edge
            hp = parse_cypher_hosts_page(line)
            if hp:
                slug = hp[0].replace("did:web:site.etzhayyim.com:", "")
                if slug in registered_slugs:
                    hosts_edges.append(hp)
                continue

            # LINKS_TO edge
            lt = parse_cypher_links_to(line)
            if lt:
                links_edges.append(lt)

    if dry_run:
        return {"pages": len(pages), "hosts": len(hosts_edges), "links": len(links_edges)}

    # Write pages
    records = []
    for p in pages:
        records.append({
            "_table": "graphar.vertex_page",
            "vertex_id": p["rkey"],
            "rkey": p["rkey"],
            "repo": p["domain_did"],
            "did": p["domain_did"],
            "label": "Page",
            "url": p["url"][:2048],
            "domain": p["domain"],
            "title": p["title"][:1024],
            "description": p["description"][:2048],
            "language": p["language"],
            "content_type": p["content_type"],
            "outlink_count": p["outlink_count"],
            "crawl": p["crawl"],
            "_alive": True,
            "_seq": 0,
        })
        if len(records) >= batch_size:
            adapter_write(records)
            records = []
    if records:
        adapter_write(records)

    # Write HOSTS_PAGE edges
    records = []
    for src_did, dst_rkey in hosts_edges:
        records.append({
            "_table": "graphar.edge_hosts_page",
            "edge_id": f"{src_did}::{dst_rkey}",
            "src_vid": src_did,
            "dst_vid": dst_rkey,
            "_alive": True,
            "_seq": 0,
        })
        if len(records) >= batch_size:
            adapter_write(records)
            records = []
    if records:
        adapter_write(records)

    # Write LINKS_TO edges
    records = []
    for src_rkey, dst_rkey in links_edges:
        records.append({
            "_table": "graphar.edge_links_to",
            "edge_id": f"{src_rkey}::{dst_rkey}",
            "src_vid": src_rkey,
            "dst_vid": dst_rkey,
            "_alive": True,
            "_seq": 0,
        })
        if len(records) >= batch_size:
            adapter_write(records)
            records = []
    if records:
        adapter_write(records)

    return {"pages": len(pages), "hosts": len(hosts_edges), "links": len(links_edges)}


def main():
    parser = argparse.ArgumentParser(description="Phase 5b: Inject pages + links to the Kagami graph adapter")
    parser.add_argument("--limit", type=int, default=0, help="Max batch files to process (0=all)")
    parser.add_argument("--domain", type=str, default="", help="Filter to specific domain slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=500, help="Records per write batch")
    parser.add_argument("--graph-dir", type=str, default="", help="Override graph directory (default: $CC_DATA_DIR/graph)")
    args = parser.parse_args()

    graph_dir = Path(args.graph_dir) if args.graph_dir else GRAPH_DIR

    # Get registered domains
    registered = get_registered_domains()
    log.info(f"Registered domain slugs: {len(registered)}")
    if args.domain:
        slug = args.domain.replace(".", "-")
        if slug not in registered:
            log.error(f"Domain slug '{slug}' not registered. Run phase5 first.")
            sys.exit(1)
        registered = {slug}

    # Find Cypher batch files
    batch_files = sorted(graph_dir.glob("batch_*.cypher"))
    log.info(f"Cypher batch files: {len(batch_files)}")
    if args.limit > 0:
        batch_files = batch_files[: args.limit]

    log.info(f"Processing {len(batch_files)} batch files for {len(registered)} domains")

    total_pages = 0
    total_hosts = 0
    total_links = 0
    t0 = time.time()

    for i, bf in enumerate(batch_files):
        if shutdown_requested:
            break
        try:
            stats = process_batch_file(bf, registered, args.dry_run, args.batch_size)
            total_pages += stats["pages"]
            total_hosts += stats["hosts"]
            total_links += stats["links"]
        except Exception as e:
            log.error(f"Error processing {bf.name}: {e}")

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            log.info(
                f"Progress: {i+1}/{len(batch_files)} batches, "
                f"pages={total_pages}, hosts={total_hosts}, links={total_links}, "
                f"{elapsed:.0f}s"
            )

    elapsed = time.time() - t0
    log.info(
        f"Phase 5b complete: {total_pages} pages, {total_hosts} hosts, "
        f"{total_links} links from {len(batch_files)} batches in {elapsed:.0f}s"
    )


if __name__ == "__main__":
    main()
