#!/usr/bin/env python3
"""yabai — ACTIVE CTI / passive-DNS collector → kotoba EAVT (ADR-2605301400 §T3).

Defensive threat-intel collector. Actively pulls PUBLIC CTI surfaces and normalizes
them into the passive-dns-cti kotoba vocabulary (:domain/* :pdns/* :tlscert/*
:indicator/* …), dedup-merges with the curated seed (seed wins on id), and writes a
merged EAVT graph analyze.py can consume. Replaces the legacy yabai RisingWave SQL
graph (WhoisRecord / DnsRecord / IpHostingHistory / TlsCertificate / IocIndicator …).

ACTIVE COLLECTION (能動的) — authorized & real, but operator-gated + offline-default:
  --source ct     Certificate Transparency logs via crt.sh JSON API for a domain →
                  :tlscert/* + :domain/* records (CT logs are public, :authoritative).
  --source pdns   bridge a passive-DNS-shaped JSON file offline (domain→IP history).
  --source vendor bridge a SecurityTrails/DNSDB/Recorded-Future-shaped file as
                  :feature-flagged-input — NEVER :system-of-record (mirrors tadori).

  A live network pull (--live) is GATE-G7: it runs ONLY when YABAI_OPERATOR_GATE is
  set. Without --live the command is fully offline: it bridges any --in file and
  otherwise re-emits the seed. yabai does NOT de-anonymise adherents or run untargeted
  mass surveillance (G10); access-audit PII stays in encrypted envelopes (G6).

stdlib only. Usage:
    python3 ingest.py                                   # offline: seed → merged graph
    python3 ingest.py --source pdns --in pdns.json      # bridge passive-DNS file (offline)
    python3 ingest.py --source ct --domain example.com --live   # G7: live crt.sh pull
"""
from __future__ import annotations
import sys
import os
import re
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yabai_edn import load_edn, classify, to_edn  # noqa: E402

OPERATOR_GATE = bool(os.environ.get("YABAI_OPERATOR_GATE"))
ACTOR = pathlib.Path(__file__).resolve().parent.parent
CRTSH = "https://crt.sh/?q={q}&output=json"
VENDOR_FAMILIES = {"securitytrails", "dnsdb", "recordedfuture"}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")


def _ip_id(addr: str) -> str:
    return f"ip.{'v6.' if ':' in addr else 'v4.'}{addr.replace('.', '-').replace(':', '-')}"


def fetch(url: str) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "etzhayyim-yabai/0.1 (+did:web:etzhayyim.com:actor:yabai)"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (public CT log only)
        return resp.read().decode("utf-8", "replace")


def parse_crtsh(text: str, sourcing: str = "authoritative"):
    """crt.sh JSON → (:domain/* + :tlscert/* dicts). Public Certificate Transparency."""
    rows = json.loads(text)
    domains, certs, seen_dom = {}, [], set()
    for r in rows:
        cn = (r.get("common_name") or "").strip().lstrip("*.")
        sans = [s.strip().lstrip("*.") for s in (r.get("name_value") or "").splitlines() if s.strip()]
        for d in {cn, *sans}:
            if not d or d in seen_dom:
                continue
            seen_dom.add(d)
            tld = d.rsplit(".", 1)[-1] if "." in d else d
            domains[f"domain.{_slug(d)}"] = {
                ":domain/id": f"domain.{_slug(d)}", ":domain/fqdn": d, ":domain/tld": tld,
                ":domain/sourcing": f":{sourcing}"}
        sha = str(r.get("serial_number") or r.get("id") or "")
        certs.append({
            ":tlscert/id": f"cert.{_slug(cn)}.{sha[:8] or 'x'}",
            ":tlscert/sha256": sha,
            ":tlscert/issuer": r.get("issuer_name", "?"),
            ":tlscert/subject": cn,
            ":tlscert/san": sans or [cn],
            ":tlscert/not-before": (r.get("not_before") or "")[:10],
            ":tlscert/not-after": (r.get("not_after") or "")[:10],
            ":tlscert/ct-log": "crt.sh",
            ":tlscert/anomaly": ":none",
            ":tlscert/sourcing": f":{sourcing}"})
    return list(domains.values()), certs


def bridge_pdns(records, sourcing: str = "representative"):
    """passive-DNS-shaped JSON [{domain, rrtype, rrdata[], ttl, first_seen, last_seen}]
    → (:domain/* + :pdns/* dicts)."""
    domains, pdns = {}, []
    for r in records:
        d = str(r.get("domain", "")).strip()
        if not d:
            continue
        did = f"domain.{_slug(d)}"
        domains[did] = {":domain/id": did, ":domain/fqdn": d,
                        ":domain/tld": d.rsplit(".", 1)[-1] if "." in d else d,
                        ":domain/sourcing": f":{sourcing}"}
        rrtype = str(r.get("rrtype", "a")).lower()
        rrdata = r.get("rrdata") or ([r["value"]] if r.get("value") else [])
        rec = {":pdns/id": f"pdns.{_slug(d)}.{rrtype}.{_slug(str(rrdata[:1]))}",
               ":pdns/domain": did, ":pdns/rrtype": f":{rrtype}",
               ":pdns/rrdata": rrdata, ":pdns/sourcing": f":{sourcing}"}
        if rrtype in ("a", "aaaa") and rrdata:
            rec[":pdns/ip"] = _ip_id(rrdata[0])
        if r.get("ttl") is not None:
            rec[":pdns/ttl"] = int(r["ttl"])
        if r.get("first_seen"):
            rec[":pdns/first-seen-at"] = r["first_seen"]
        if r.get("last_seen"):
            rec[":pdns/last-seen-at"] = r["last_seen"]
        pdns.append(rec)
    return list(domains.values()), pdns


_ID_KEYS = (
    ":domain/id", ":pdns/id", ":iphist/id", ":tlscert/id",
    ":indicator/id", ":access/id", ":btobs/id",
)


def _key(rec):
    for k in _ID_KEYS:
        if k in rec:
            return rec[k]
    return None


def main(argv):
    seed_path = ACTOR / "data" / "seed-passive-dns.kotoba.edn"
    out_path = ACTOR / "data" / "passive-dns.merged.kotoba.edn"
    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    infile = argv[argv.index("--in") + 1] if "--in" in argv else None
    domain = argv[argv.index("--domain") + 1] if "--domain" in argv else None
    family = argv[argv.index("--family") + 1] if "--family" in argv else None
    live = "--live" in argv

    bridged = []
    if source == "ct":
        if not domain:
            sys.exit("--source ct needs --domain <fqdn>")
        if not live:
            print(f"yabai.ingest: source ct = {CRTSH.format(q=domain)}")
            print("  → offline default (no --live): not fetched. Emitting seed only. "
                  "Pass --live (requires YABAI_OPERATOR_GATE) for a real CT-log pull.")
        elif not OPERATOR_GATE:
            sys.exit("REFUSED: --live CT-log pull is G7 operator-gated. Set "
                     "YABAI_OPERATOR_GATE=<council/operator-token> to actively query crt.sh "
                     "(public Certificate Transparency data only).")
        else:
            print(f"yabai.ingest: LIVE crt.sh pull for {domain} …")
            ds, cs = parse_crtsh(fetch(CRTSH.format(q=domain)), "authoritative")
            bridged = ds + cs
            print(f"  pulled {len(ds)} domains + {len(cs)} certs (:authoritative)")
    elif source == "pdns" and infile:
        recs = json.loads(pathlib.Path(infile).read_text(encoding="utf-8"))
        recs = recs.get("records", recs) if isinstance(recs, dict) else recs
        ds, ps = bridge_pdns(recs)
        bridged = ds + ps
        print(f"yabai.ingest: bridged {len(ds)} domains + {len(ps)} passive-DNS obs from {infile} (:representative)")
    elif source == "vendor" and infile:
        if family not in VENDOR_FAMILIES:
            sys.exit(f"--source vendor needs --family <{'|'.join(VENDOR_FAMILIES)}>")
        recs = json.loads(pathlib.Path(infile).read_text(encoding="utf-8"))
        recs = recs.get("records", recs) if isinstance(recs, dict) else recs
        ds, ps = bridge_pdns(recs, sourcing="feature-flagged-input")
        bridged = ds + ps
        print(f"yabai.ingest: bridged {len(ps)} obs from vendor '{family}' as "
              ":feature-flagged-input (NEVER system-of-record; tadori G4 discipline)")
    elif source:
        sys.exit(f"unknown --source '{source}'. Known: ct, pdns, vendor.")

    seed_rows = load_edn(seed_path)
    merged, seen = [], set()
    for rec in seed_rows + bridged:
        if not isinstance(rec, dict):
            continue
        k = _key(rec)
        if k is None or k in seen:
            continue
        seen.add(k)
        merged.append(rec)

    out_path.write_text(to_edn(merged, [
        ";; yabai — GENERATED merged CTI / passive-DNS graph (seed + active ingest).",
        ";; DO NOT hand-edit. dedup by id, seed wins. kotoba EAVT (ADR-2605301400 §T3).",
    ]), encoding="utf-8")

    b = classify(merged)
    print(f"= merged graph: {len(b['domains'])} domains · {len(b['pdns'])} passive-DNS · "
          f"{len(b['certs'])} certs · {len(b['indicators'])} IOCs · "
          f"{len(b['btobs'])} BitTorrent obs · {len(merged)} records")
    print(f"✓ wrote {out_path.relative_to(ACTOR)}")
    print(f"→ next: python3 methods/analyze.py {out_path.relative_to(ACTOR)} --out out")


if __name__ == "__main__":
    main(sys.argv)
