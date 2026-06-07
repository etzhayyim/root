#!/usr/bin/env python3
"""sukashi 透かし — ad-tech supply-chain ingest bridge (R1 scaffold; offline default).

ADR-2606071600. Normalizes the PUBLIC ad-tech web-standard files into the kotoba EAVT
ad-supply-chain vocabulary and dedup-merges with the curated seed (seed wins). The
real parsers below are genuinely functional (ads.txt / sellers.json are simple public
formats); what is GATED is LIVE FETCH at web scale. Live crawl of any source is G7
Council + operator gated and is a NO-OP unless SUKASHI_OPERATOR_GATE=1. Default offline
run bridges any local --in file (a downloaded ads.txt / sellers.json / WHOIS JSON) and
re-emits the merged graph so downstream cells have a stable input.

sukashi is an OBSERVATORY (G2): fetch is observational only (GET/HEAD of a PUBLIC file);
it never places/clicks an ad, never submits a form, never bypasses anti-bot. ads.txt /
sellers.json / RDAP-WHOIS are public records by design.

Sources (all PUBLIC record):
  --source adstxt    a publisher's /ads.txt or /app-ads.txt (IAB Tech Lab spec)
  --source sellersjson  an exchange's /sellers.json (IAB Tech Lab spec)
  --source whois      an RDAP / WHOIS JSON record (registrant ORG only; PII dropped)
  --in PATH           the local file to bridge offline (ads.txt text, or .json)

stdlib only. Usage:
    python3 ingest.py [--source adstxt|sellersjson|whois] [--in PATH] [--publisher ID] [--seller ID] [--out PATH]
"""
from __future__ import annotations
import sys
import os
import re
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sukashi_edn import load_edn, classify, edn_str  # noqa: E402

OPERATOR_GATE = os.environ.get("SUKASHI_OPERATOR_GATE", "") == "1"

# Documented full-web endpoints — NOT fetched unless the operator gate is set.
SOURCES = {
    "adstxt": "https://<publisher>/ads.txt + /app-ads.txt (IAB Tech Lab ads.txt 1.1)",
    "sellersjson": "https://<exchange>/sellers.json (IAB Tech Lab sellers.json 1.0)",
    "whois": "RDAP (https://rdap.org/domain/<d>) / WHOIS — registrant ORG only (G9 PII guard)",
}

# WHOIS/RDAP fields that may carry a natural person — never ingested (G9).
_PII_DROP = ("registrant_name", "registrantName", "name", "email", "phone", "street", "address")


def _seller_id_from_domain(domain):
    return "adtech." + "ssp." + re.sub(r'[^a-z0-9]+', '-', str(domain).lower()).strip('-')


def parse_ads_txt(text, publisher_id):
    """Parse an ads.txt / app-ads.txt body → :adtech (sellers) + :adauth.edge dicts.

    Each non-comment line: <domain>, <account_id>, <DIRECT|RESELLER>[, <cert_authority>].
    Sourcing is :authoritative — ads.txt is a public file the publisher itself signs.
    """
    sellers, edges = {}, []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" in line.split(",")[0]:  # skip comments + variables (CONTACT=, SUBDOMAIN=)
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        domain, account, rel = parts[0], parts[1], parts[2].lower()
        cert = parts[3] if len(parts) > 3 else None
        seller_id = _seller_id_from_domain(domain)
        sellers.setdefault(seller_id, {
            ":adtech/id": seller_id, ":adtech/name": domain, ":adtech/role": ":ssp",
            ":adtech/domain": domain, ":adtech/sourcing": ":authoritative"})
        edge = {
            ":adauth.edge/id": f"adauth.{publisher_id}->{domain}:{account}:{rel}",
            ":adauth.edge/publisher": publisher_id,
            ":adauth.edge/seller": seller_id,
            ":adauth.edge/account-id": account,
            ":adauth.edge/relationship": ":" + ("direct" if rel == "direct" else "reseller"),
            ":adauth.edge/declared": True,
            ":adauth.edge/confirmed": False,  # set true only after a sellers.json cross-check
            ":adauth.edge/sourcing": ":authoritative"}
        if cert:
            edge[":adauth.edge/cert-authority"] = cert
        edges.append(edge)
    return sellers, edges


def parse_sellers_json(obj):
    """Parse a sellers.json object → :adtech seller dicts (the other side of the handshake).

    Each entry: {seller_id, name?, domain?, seller_type}. seller_type ∈ PUBLISHER|INTERMEDIARY|BOTH.
    Confidential sellers (is_confidential=1) carry no name/domain — we keep only the id (G9).
    """
    out = {}
    for s in obj.get("sellers", []):
        sid = str(s.get("seller_id", "")).strip()
        if not sid:
            continue
        dom = s.get("domain", "")
        aid = "adtech.ssp." + re.sub(r'[^a-z0-9]+', '-', str(dom or sid).lower()).strip('-')
        rec = {":adtech/id": aid, ":adtech/role": ":ssp",
               ":adtech/seller-id": sid, ":adtech/sourcing": ":authoritative"}
        if not s.get("is_confidential"):
            if s.get("name"):
                rec[":adtech/name"] = s["name"]
            if dom:
                rec[":adtech/domain"] = dom
        st = str(s.get("seller_type", "")).lower()
        if st in ("publisher", "intermediary", "both"):
            rec[":adtech/seller-type"] = ":" + st
        out[aid] = rec
    return out


def bridge_whois(records):
    """Map RDAP/WHOIS JSON → :addelivery.edge dicts (registrant ORG only; G9 drops PII)."""
    out = []
    for r in records:
        domain = r.get("domain") or r.get("ldhName")
        if not domain:
            continue
        org = r.get("registrant_org") or r.get("org") or r.get("registrantOrganization")
        # G9: never ingest a natural-person field
        if not org and any(k in r for k in _PII_DROP):
            org = None  # personal registrant → org-less, person excluded
        d = {":addelivery.edge/id": f"deliv.whois.{domain}",
             ":addelivery.edge/landing-domain": domain,
             ":addelivery.edge/sourcing": ":authoritative"}
        if org:
            d[":addelivery.edge/whois-org"] = org
        if r.get("registrar"):
            d[":addelivery.edge/registrar"] = r["registrar"]
        out.append(d)
    return out


def emit(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, bool):
            parts.append(f'{k} {"true" if v else "false"}')
        elif isinstance(v, (int, float)):
            parts.append(f'{k} {v}')
        elif isinstance(v, str) and v.startswith(':'):
            parts.append(f'{k} {v}')
        else:
            parts.append(f'{k} {edn_str(v)}')
    return "{" + " ".join(parts) + "}"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = here / "data" / "seed-ad-supply-chain.kotoba.edn"
    outp = here / "data" / "ad-supply-chain.merged.kotoba.edn"
    if "--out" in argv:
        outp = pathlib.Path(argv[argv.index("--out") + 1])

    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    infile = argv[argv.index("--in") + 1] if "--in" in argv else None
    publisher = argv[argv.index("--publisher") + 1] if "--publisher" in argv else "adtech.publisher.ingested"

    bridged = []
    if source in SOURCES and not infile and not OPERATOR_GATE:
        print(f"sukashi.ingest: source '{source}' = {SOURCES[source]}")
        print("  → G7 GATED: live full-web fetch requires SUKASHI_OPERATOR_GATE=1 (Council). "
              "Provide a local --in file to bridge offline; emitting seed only.")
    elif source == "adstxt" and infile:
        sellers, edges = parse_ads_txt(pathlib.Path(infile).read_text(encoding="utf-8"), publisher)
        bridged = list(sellers.values()) + edges
        print(f"sukashi.ingest: bridged {len(sellers)} sellers + {len(edges)} auth edges "
              f"from {infile} (:authoritative)")
    elif source == "sellersjson" and infile:
        obj = json.loads(pathlib.Path(infile).read_text(encoding="utf-8"))
        sellers = parse_sellers_json(obj)
        bridged = list(sellers.values())
        print(f"sukashi.ingest: bridged {len(sellers)} sellers.json entries from {infile} "
              f"(:authoritative)")
    elif source == "whois" and infile:
        recs = json.loads(pathlib.Path(infile).read_text(encoding="utf-8"))
        recs = recs if isinstance(recs, list) else recs.get("records", [recs])
        bridged = bridge_whois(recs)
        print(f"sukashi.ingest: bridged {len(bridged)} WHOIS records from {infile} "
              f"(registrant ORG only, PII dropped — G9)")
    elif source:
        print(f"sukashi.ingest: unknown source '{source}'. Known: {', '.join(SOURCES)}")

    # dedup-merge: seed wins on id collision (across all id keys)
    seed_rows = load_edn(seed)
    seed_ids = set()
    for r in seed_rows:
        if isinstance(r, dict):
            for k in (":adtech/id", ":adauth.edge/id", ":adcreative/id",
                      ":addelivery.edge/id", ":adfraud.signal/id"):
                if k in r:
                    seed_ids.add(r[k])
    extra = []
    for d in bridged:
        eid = next((d[k] for k in (":adtech/id", ":adauth.edge/id", ":adcreative/id",
                                   ":addelivery.edge/id", ":adfraud.signal/id") if k in d), None)
        if eid and eid not in seed_ids:
            extra.append(d)

    seed_text = seed.read_text(encoding="utf-8").rstrip()
    if extra:
        body = seed_text[:seed_text.rfind("]")].rstrip()
        lines = "\n".join(" " + emit(d) for d in extra)
        outp.write_text(body + "\n ;; ── bridged (ingest) ──\n" + lines + "\n]\n", encoding="utf-8")
    else:
        outp.write_text(seed_text + "\n", encoding="utf-8")

    print(f"sukashi.ingest: merged graph → {outp} "
          f"({len(seed_ids)} seed ids + {len(extra)} bridged)")


if __name__ == "__main__":
    main(sys.argv)
