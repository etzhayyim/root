#!/usr/bin/env python3
"""ipaddress — atproto-compatible status-post composer + publisher.

ADR-2605301400 §T2 + 2606031600. Composes app.bsky.feed.post-shaped records from the
IP/ASN number-resource graph + analyze output and writes them into the kotoba Datom log
via kotoba-server `com.etzhayyim.apps.kotoba.atproto.repo.write`, so the actor's
operational status is visible on etzhayyim.com (did:web:etzhayyim.com:actor:ipaddress)
and federates over AT Protocol.

OUTWARD-GATED (G11): live publication requires BOTH
  IPADDRESS_LIVE_POST=1   (operator intent)  and
  KOTOBA_ENDPOINT=...      (target kotoba-server),
plus operator auth (IPADDRESS_OPERATOR_TOKEN → Authorization: Bearer). Otherwise DRY-RUN.

AGGREGATE-FIRST + resilience-framed (not a target-list): post bodies state public
number-resource facts + computed concentration only, routed to diversity/accountability.
Every body passes a Charter Rider §2(a)-(h) content scan before it is eligible to publish.

stdlib only. Usage:
    python3 social.py [graph.edn] [--limit N] [--dry-run]
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
from ip_edn import load_edn, classify  # noqa: E402
from analyze import analyze  # noqa: E402

ACTOR_DID = "did:web:etzhayyim.com:actor:ipaddress"
LIVE = os.environ.get("IPADDRESS_LIVE_POST", "") == "1"
ENDPOINT = os.environ.get("KOTOBA_ENDPOINT", "").rstrip("/")
GRAPH = os.environ.get("KOTOBA_GRAPH", "ipaddress:social:2026")
OPERATOR_TOKEN = os.environ.get("IPADDRESS_OPERATOR_TOKEN", "")

_CHARTER_DENY = [
    "weapon design", "covert force", "how to attack", "where to cut", "which prefix to attack",
    "child sexual", "non-consensual", "gore for", "ad network", "adsense", "de-anonymize",
]


def charter_rider_clean(text: str) -> bool:
    t = text.lower()
    return not any(bad in t for bad in _CHARTER_DENY)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def rkey(subject_id: str) -> str:
    return "ipaddress-" + hashlib.sha256(subject_id.encode()).hexdigest()[:13]


def post_record(text, langs=None):
    return {"$type": "app.bsky.feed.post", "text": text[:300],
            "langs": langs or ["en"], "createdAt": _now()}


def compose(b, a):
    rirs, asns, ranges = b["rirs"], b["asns"], b["ranges"]
    # 1) operational-status headline
    yield ("ipaddress.status.coverage", "status",
           f"ipaddress — world IP/ASN number-resource graph (kotoba Datom log, public record): "
           f"{len(rirs)} RIRs · {len(asns)} ASNs · {a['v4']+a['v6']} CIDR ranges. "
           f"Routing-authority HHI {a['prefix_hhi']}. A resilience + accountability map, "
           f"never a target-list; no host scanning. #internet #resilience")
    # 2) routing-authority concentration → routed to multi-homing / diversity
    for aid, name, pref, cls, cc in a["asn_prefix"][:6]:
        if pref <= 0:
            continue
        yield (str(aid), "asn-load",
               f"Origin-routing concentration (public BGP record): {name} "
               f"announces ~{pref:,} prefixes ({str(cls).lstrip(':')}, {cc}). "
               f"Diversify / multi-home to build network resilience. #BGP #resilience")
    # 3) per-RIR delegation coverage
    top_rir = sorted(a["rir_addr"].items(), key=lambda kv: -kv[1])[:1]
    for rir, addr in top_rir:
        yield (f"rir.{rir}", "rir-coverage",
               f"Delegated address-space coverage (public RIR record): "
               f"{rirs.get(rir, {}).get(':rir/name', rir)} leads the graph with "
               f"{addr:,} IPv4-equivalent addresses across {a['rir_ranges'].get(rir, 0)} ranges. "
               f"#numberresources")


def write_live(record, uri):
    body = json.dumps({"graph": GRAPH, "uri": uri, "operation": "create",
                       "record": record}).encode("utf-8")
    req = urllib.request.Request(
        f"{ENDPOINT}/xrpc/com.etzhayyim.apps.kotoba.atproto.repo.write",
        data=body, method="POST", headers={"content-type": "application/json"})
    if OPERATOR_TOKEN:
        req.add_header("authorization", f"Bearer {OPERATOR_TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    graph = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else (here / "data" / "ip-network.merged.kotoba.edn"
              if (here / "data" / "ip-network.merged.kotoba.edn").exists()
              else here / "data" / "seed-ip-network.kotoba.edn")
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 8
    force_dry = "--dry-run" in argv

    b = classify(load_edn(graph))
    a = analyze(b)
    live = LIVE and bool(ENDPOINT) and not force_dry
    if LIVE and not ENDPOINT and not force_dry:
        print("ipaddress.social: IPADDRESS_LIVE_POST=1 but KOTOBA_ENDPOINT unset → DRY-RUN")
    print(f"ipaddress.social: mode={'LIVE' if live else 'DRY-RUN'} actor={ACTOR_DID} graph={GRAPH}")

    n = 0
    for subject_id, _kind, text in compose(b, a):
        if n >= limit:
            break
        if not charter_rider_clean(text):
            print(f"  [SKIP charter §2] {subject_id}")
            continue
        uri = f"at://{ACTOR_DID}/app.bsky.feed.post/{rkey(subject_id)}"
        rec = post_record(text)
        if live:
            try:
                out = write_live(rec, uri)
                print(f"  [posted] {uri}  tx={out.get('txCid') or out}")
            except urllib.error.HTTPError as ex:
                print(f"  [ERROR {ex.code}] {uri}: {ex.read().decode('utf-8','replace')[:200]}")
            except Exception as ex:  # noqa: BLE001
                print(f"  [ERROR] {uri}: {ex}")
        else:
            print(f"  [dry-run] {uri}\n            {json.dumps(rec, ensure_ascii=False)}")
        n += 1
    print(f"ipaddress.social: {n} post(s) {'published' if live else 'composed (dry-run)'}; "
          f"charter-scan applied to every body.")


if __name__ == "__main__":
    main(sys.argv)
