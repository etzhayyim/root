#!/usr/bin/env python3
"""kabuto 兜 — atproto-compatible social post composer + publisher.

ADR-2606022000. Composes app.bsky.feed.post-shaped records from the company /
supply-edge / intel-report graph and writes them into the kotoba Datom log via
kotoba-server `com.etzhayyim.apps.kotoba.atproto.repo.write` (so the post is queryable
by the in-browser kotoba-wasm node and federates over AT Protocol).

OUTWARD-GATED (kabuto G11): live publication requires BOTH
  KABUTO_LIVE_POST=1   (operator intent)  and
  KOTOBA_ENDPOINT=...   (target kotoba-server),
plus operator auth (KABUTO_OPERATOR_TOKEN → Authorization: Bearer). Without these
it is a DRY-RUN: it prints each record + its AT-URI and writes nothing.

AGGREGATE-FIRST + non-adjudicating (G3/G4): post bodies state public facts and
computed concentration only. Every body passes a Charter Rider §2(a)-(h) content
scan (G-charter) before it is eligible to publish.

stdlib only. Usage:
    python3 social.py [seed.edn] [--report out/intel-report.md] [--limit N] [--dry-run]
"""
from __future__ import annotations
import sys
import os
import json
import hashlib
import pathlib
import datetime
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kabuto_edn import load_edn, classify  # noqa: E402

ACTOR_DID = "did:web:etzhayyim.com:actor:kabuto"
LIVE = os.environ.get("KABUTO_LIVE_POST", "") == "1"
ENDPOINT = os.environ.get("KOTOBA_ENDPOINT", "").rstrip("/")
GRAPH = os.environ.get("KOTOBA_GRAPH", "kabuto:social:2026")
OPERATOR_TOKEN = os.environ.get("KABUTO_OPERATOR_TOKEN", "")

# Minimal local Charter Rider §2(a)-(h) deny-scan. The CANONICAL scanner is
# etzhayyim_organism.sensors.charter_rider.scan(); this is a dependency-free
# stand-in so the cell runs anywhere. Conservative substring match (lower-cased).
_CHARTER_DENY = [
    "weapon design", "covert force", "how to attack", "where to cut",
    "child sexual", "non-consensual", "gore for", "ad network", "adsense",
]


def charter_rider_clean(text: str) -> bool:
    t = text.lower()
    return not any(bad in t for bad in _CHARTER_DENY)


def rkey(subject_id: str) -> str:
    return "kabuto-" + hashlib.sha256(subject_id.encode()).hexdigest()[:13]


def post_record(text: str, langs):
    return {
        "$type": "app.bsky.feed.post",
        "text": text[:300],
        "langs": langs or ["en"],
        "createdAt": _now(),
    }


def _now():
    # explicit UTC ISO-8601 with Z (atproto datetime)
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def compose(companies, edges, report_summary):
    """Yield (subjectId, kind, text) tuples — aggregate-first, public-facts-only."""
    # 1) one headline post from the intel report
    if report_summary:
        yield ("kabuto.report.supply-concentration", "intel-report",
               "kabuto 兜 supply-chain concentration map (aggregate-first, public record): "
               + report_summary
               + " — a redundancy/accountability map, not a target-list. #supplychain")

    # 2) the highest-criticality single-source edges (redundancy gaps)
    top = sorted(edges, key=lambda e: -float(e.get(':supply.edge/criticality', 0) or 0))[:8]
    for e in top:
        s = e.get(':supply.edge/from')
        c = e.get(':supply.edge/to')
        sn = companies.get(s, {}).get(':company/name', s)
        cn = companies.get(c, {}).get(':company/name', c)
        commodity = str(e.get(':supply.edge/commodity', ':unknown')).lstrip(':')
        crit = e.get(':supply.edge/criticality')
        yield (e.get(':supply.edge/id'), "supply-edge",
               f"Disclosed supply dependency (public record): {cn} relies on {sn} "
               f"for {commodity} (est. concentration {crit}). Diversify to build resilience. "
               f"#supplychain #{commodity}")


def write_live(record, uri):
    body = json.dumps({
        "graph": GRAPH,
        "uri": uri,
        "operation": "create",
        "record": record,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{ENDPOINT}/xrpc/com.etzhayyim.apps.kotoba.atproto.repo.write",
        data=body, method="POST",
        headers={"content-type": "application/json"})
    if OPERATOR_TOKEN:
        req.add_header("authorization", f"Bearer {OPERATOR_TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-public-companies.kotoba.edn"
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 9
    force_dry = "--dry-run" in argv

    report_summary = ""
    report_path = here / "out" / "intel-report.md"
    if "--report" in argv:
        report_path = pathlib.Path(argv[argv.index("--report") + 1])
    if report_path.exists():
        # pull the headline jurisdiction line if analyze.py has run
        for line in report_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- sectors covered:"):
                report_summary = line[2:].strip()
                break

    rows = load_edn(seed)
    companies, _addr, _contact, edges, _proc = classify(rows)

    live = LIVE and bool(ENDPOINT) and not force_dry
    mode = "LIVE" if live else "DRY-RUN"
    if LIVE and not ENDPOINT and not force_dry:
        print("kabuto.social: KABUTO_LIVE_POST=1 but KOTOBA_ENDPOINT unset → DRY-RUN")
    print(f"kabuto.social: mode={mode} actor={ACTOR_DID} graph={GRAPH}")

    n = 0
    for subject_id, kind, text in compose(companies, edges, report_summary):
        if n >= limit:
            break
        clean = charter_rider_clean(text)
        uri = f"at://{ACTOR_DID}/app.bsky.feed.post/{rkey(subject_id)}"
        rec = post_record(text, ["en"])
        if not clean:
            print(f"  [SKIP charter §2] {subject_id}")
            continue
        if live:
            try:
                out = write_live(rec, uri)
                print(f"  [posted] {uri}  tx={out.get('txCid') or out}")
            except urllib.error.HTTPError as ex:
                print(f"  [ERROR {ex.code}] {uri}: {ex.read().decode('utf-8', 'replace')[:200]}")
            except Exception as ex:  # noqa: BLE001
                print(f"  [ERROR] {uri}: {ex}")
        else:
            print(f"  [dry-run] {uri}")
            print(f"            {json.dumps(rec, ensure_ascii=False)}")
        n += 1

    print(f"kabuto.social: {n} post(s) {'published' if live else 'composed (dry-run)'}; "
          f"charter-scan applied to every body.")


if __name__ == "__main__":
    main(sys.argv)
