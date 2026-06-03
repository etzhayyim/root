#!/usr/bin/env python3
"""yabai — atproto-compatible status-post composer + publisher.

ADR-2605301400 §T3 + 2606031600. Composes app.bsky.feed.post-shaped records from the
CTI / passive-DNS graph + analyze output and writes them into the kotoba Datom log via
kotoba-server `com.etzhayyim.apps.kotoba.atproto.repo.write`, so the actor's operational
status is visible on etzhayyim.com (did:web:etzhayyim.com:actor:yabai) and federates over
AT Protocol.

OUTWARD-GATED (G11): live publication requires BOTH
  YABAI_LIVE_POST=1   (operator intent)  and
  KOTOBA_ENDPOINT=...   (target kotoba-server),
plus operator auth (YABAI_OPERATOR_TOKEN → Authorization: Bearer). Otherwise DRY-RUN.

DEFENSIVE + aggregate-first: bodies state defensive CTI signals only (fast-flux counts,
hosting concentration, IOC distribution, the G6/G10 encryption posture). NO per-target
naming of private parties, no de-anon, no "go attack X" framing. Illustrative example.*
indicators are NOT presented as real-entity attribution. Every body passes a Charter
Rider §2(a)-(h) content scan before it is eligible to publish.

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
from yabai_edn import load_edn, classify  # noqa: E402
from analyze import analyze  # noqa: E402

ACTOR_DID = "did:web:etzhayyim.com:actor:yabai"
LIVE = os.environ.get("YABAI_LIVE_POST", "") == "1"
ENDPOINT = os.environ.get("KOTOBA_ENDPOINT", "").rstrip("/")
GRAPH = os.environ.get("KOTOBA_GRAPH", "yabai:social:2026")
OPERATOR_TOKEN = os.environ.get("YABAI_OPERATOR_TOKEN", "")

_CHARTER_DENY = [
    "weapon design", "covert force", "how to attack", "go attack", "child sexual",
    "non-consensual", "gore for", "ad network", "adsense", "de-anonymize", "doxx",
]


def charter_rider_clean(text: str) -> bool:
    t = text.lower()
    return not any(bad in t for bad in _CHARTER_DENY)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def rkey(subject_id: str) -> str:
    return "yabai-" + hashlib.sha256(subject_id.encode()).hexdigest()[:13]


def post_record(text, langs=None):
    return {"$type": "app.bsky.feed.post", "text": text[:300],
            "langs": langs or ["en"], "createdAt": _now()}


def compose(b, a):
    # 1) operational-status headline + G6/G10 posture (defensive, aggregate-first)
    enc = f"{a['access_encrypted']}/{a['access_total']}"
    yield ("yabai.status.cti", "status",
           f"yabai — defensive CTI / passive-DNS risk graph (kotoba Datom log): "
           f"{a['n_domains']} domains · {a['n_pdns']} passive-DNS obs · {a['n_certs']} certs · "
           f"{a['n_ioc']} IOCs. Access-audit encryption {enc} (PII never plaintext; G6/G10). "
           f"Defensive only — scores risk, never enforces. #threatintel #privacy")
    # 2) fast-flux defensive signal (count only, no naming a private target)
    if a["fast_flux"]:
        yield ("yabai.signal.fastflux", "fast-flux",
               f"Defensive signal: {len(a['fast_flux'])} fast-flux candidate domain(s) "
               f"(low-TTL × many-IP churn) flagged for takedown / abuse reporting — "
               f"never for offensive targeting. #threatintel #defense")
    # 3) IOC TLP distribution (aggregate)
    tlp = sorted(a["tlp_load"].items(), key=lambda kv: -kv[1])
    if tlp:
        dist = ", ".join(f"{str(k).lstrip(':')} {v}" for k, v in tlp)
        yield ("yabai.ioc.tlp", "ioc-tlp",
               f"IOC store by TLP (aggregate, defensive sharing): {dist}. "
               f"Shared for protection, not pursuit. #IOC #threatintel")
    # 4) hosting concentration (provider-type aggregate)
    pt = sorted(a["ptype_load"].items(), key=lambda kv: -kv[1])[:1]
    for cls, nobs in pt:
        yield ("yabai.hosting.concentration", "hosting",
               f"Observed-infra hosting concentration: most observations sit behind "
               f"`{str(cls).lstrip(':')}` ({nobs}). Defensive context for resilience. #infra")


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
        else (here / "data" / "passive-dns.merged.kotoba.edn"
              if (here / "data" / "passive-dns.merged.kotoba.edn").exists()
              else here / "data" / "seed-passive-dns.kotoba.edn")
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 8
    force_dry = "--dry-run" in argv

    b = classify(load_edn(graph))
    a = analyze(b)
    live = LIVE and bool(ENDPOINT) and not force_dry
    if LIVE and not ENDPOINT and not force_dry:
        print("yabai.social: YABAI_LIVE_POST=1 but KOTOBA_ENDPOINT unset → DRY-RUN")
    print(f"yabai.social: mode={'LIVE' if live else 'DRY-RUN'} actor={ACTOR_DID} graph={GRAPH}")

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
    print(f"yabai.social: {n} post(s) {'published' if live else 'composed (dry-run)'}; "
          f"charter-scan applied to every body.")


if __name__ == "__main__":
    main(sys.argv)
