#!/usr/bin/env python3
"""yabai — CTI / passive-DNS concentration + anomaly analyzer (ADR-2605301400 §T3).

Reads a kotoba-EDN CTI graph (:domain/* :pdns/* :iphist/* :tlscert/* :indicator/*
:access/*) and emits, AGGREGATE-FIRST:

  1. out/intel-report.md — defensive threat-intel signals: fast-flux candidate
     domains, hosting-provider concentration, IOC TLP/category load, IP-movement
     churn, TLS cert-SAN pivots, plus a G6/G10 encryption self-audit.
  2. out/cti-signals.kotoba.edn — derived :cti/* datoms, flagged :derived.

CONSTITUTIONAL framing (yabai = risk organ, NOT enforcement): this scores DEFENSIVE
risk context (whose infra, how it moved, which IOCs). Enforcement is the Council's;
evidence is tadori's. No adherent is de-anonymised; access-audit PII stays encrypted.

stdlib only. Usage:
    python3 analyze.py [graph.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yabai_edn import load_edn, classify, edn_str  # noqa: E402

FAST_FLUX_TTL = 300       # TTL ≤ this …
FAST_FLUX_MIN_IPS = 3     # … with ≥ this many distinct A answers = fast-flux candidate


def analyze(b):
    domains, pdns, iphist = b["domains"], b["pdns"], b["iphist"]
    certs, indicators, access = b["certs"], b["indicators"], b["access"]

    # fast-flux candidates: low TTL + many distinct A/AAAA answers in one observation
    fast_flux = []
    for p in pdns:
        if p.get(":pdns/rrtype") in (":a", ":aaaa"):
            ips = p.get(":pdns/rrdata") or []
            ttl = int(p.get(":pdns/ttl", 999999) or 999999)
            if ttl <= FAST_FLUX_TTL and len(ips) >= FAST_FLUX_MIN_IPS:
                dom = domains.get(p.get(":pdns/domain"), {}).get(":domain/fqdn", p.get(":pdns/domain"))
                fast_flux.append((dom, len(ips), ttl))
    fast_flux.sort(key=lambda r: (r[2], -r[1]))

    # hosting concentration: Σ observed infra per provider + per provider-type
    prov_load = defaultdict(int)
    ptype_load = defaultdict(int)
    ip_moves = defaultdict(int)
    for h in iphist:
        prov_load[h.get(":iphist/provider", "?")] += 1
        ptype_load[h.get(":iphist/provider-type", ":unknown")] += 1
        ip_moves[h.get(":iphist/ip", "?")] += 1
    ip_movement = sorted(ip_moves.items(), key=lambda kv: -kv[1])

    # IOC load per TLP + category
    tlp_load = defaultdict(int)
    cat_load = defaultdict(int)
    for i in indicators:
        tlp_load[i.get(":indicator/tlp", ":unknown")] += 1
        cat_load[i.get(":indicator/category", ":unknown")] += 1

    # cert-SAN pivots: SANs bridging multiple domains (shared-infra signal)
    cert_pivot = []
    for c in certs:
        sans = c.get(":tlscert/san") or []
        if isinstance(sans, list) and len(sans) >= 2:
            cert_pivot.append((c.get(":tlscert/subject", c.get(":tlscert/id")), len(sans),
                               c.get(":tlscert/anomaly", ":none")))
    cert_pivot.sort(key=lambda r: -r[1])

    # G6/G10 encryption self-audit: access records MUST be encrypted; count violations.
    access_total = len(access)
    access_encrypted = sum(1 for x in access if x.get(":cti.attr/encrypted") is True)
    plaintext_violations = access_total - access_encrypted

    return dict(
        fast_flux=fast_flux, prov_load=prov_load, ptype_load=ptype_load,
        ip_movement=ip_movement, tlp_load=tlp_load, cat_load=cat_load,
        cert_pivot=cert_pivot, access_total=access_total,
        access_encrypted=access_encrypted, plaintext_violations=plaintext_violations,
        n_domains=len(domains), n_pdns=len(pdns), n_iphist=len(iphist),
        n_certs=len(certs), n_ioc=len(indicators),
    )


def render_report(b, a):
    L = []
    P = L.append
    P("# yabai — passive-DNS + CTI threat-intel report")
    P("")
    P("> ADR-2605301400 §T3 · **kotoba-native** (Datom log; NO RisingWave) · **aggregate-first** · "
      "DEFENSIVE risk context (whose infra, how it moved, which IOCs). yabai SCORES risk; the "
      "Council authorizes enforcement; tadori holds case-anchored evidence. No adherent is "
      "de-anonymised; access-audit PII stays in encrypted envelopes (G6/G10).")
    P("")
    P(f"- domains: **{a['n_domains']}**  ·  passive-DNS obs: **{a['n_pdns']}**  ·  "
      f"IP-history obs: **{a['n_iphist']}**  ·  TLS certs: **{a['n_certs']}**  ·  IOCs: **{a['n_ioc']}**")
    P("")

    # ── G6/G10 encryption self-audit (headline invariant) ──
    P("## Confidentiality self-audit — G6/G10 (access-audit encryption)")
    P("")
    status = "✅ PASS" if a["plaintext_violations"] == 0 else "❌ FAIL"
    P(f"Access-audit records carry accessor identity / IP / device — PII that MUST live in a "
      f"`com.etzhayyim.encrypted.*` envelope, never plaintext. **{status}** — "
      f"{a['access_encrypted']}/{a['access_total']} access records encrypted, "
      f"**{a['plaintext_violations']}** plaintext-PII violation(s).")
    P("")

    P("## Fast-flux candidate domains — low TTL × many A answers")
    P("")
    P(f"Domains whose A/AAAA set churns across ≥{FAST_FLUX_MIN_IPS} IPs at TTL ≤{FAST_FLUX_TTL}s "
      "in one observation — a classic resilient-malware / phishing hosting signal. Routed to "
      "takedown / abuse reporting, never to offensive targeting.")
    P("")
    P("| domain | distinct IPs | TTL (s) |")
    P("|---|---:|---:|")
    for dom, nips, ttl in a["fast_flux"]:
        P(f"| `{dom}` | {nips} | {ttl} |")
    if not a["fast_flux"]:
        P("| (none in graph) | | |")
    P("")

    P("## Hosting concentration — observed infra by provider type")
    P("")
    P("Σ observed IP-history records per hosting provider-type. Surfaces how much observed "
      "infra sits behind cloud/CDN vs bulletproof/residential — a defensive context signal.")
    P("")
    P("| provider-type | observations |")
    P("|---|---:|")
    for pt, n in sorted(a["ptype_load"].items(), key=lambda kv: -kv[1]):
        P(f"| `{str(pt).lstrip(':')}` | {n} |")
    P("")
    P("| hosting provider | observations |")
    P("|---|---:|")
    for pv, n in sorted(a["prov_load"].items(), key=lambda kv: -kv[1])[:12]:
        P(f"| {pv} | {n} |")
    P("")

    P("## IOC load — TLP and category distribution")
    P("")
    P("| TLP | indicators |  | category | indicators |")
    P("|---|---:|---|---|---:|")
    tlp = sorted(a["tlp_load"].items(), key=lambda kv: -kv[1])
    cat = sorted(a["cat_load"].items(), key=lambda kv: -kv[1])
    for i in range(max(len(tlp), len(cat))):
        lt = f"`{str(tlp[i][0]).lstrip(':')}` | {tlp[i][1]}" if i < len(tlp) else " | "
        rc = f"`{str(cat[i][0]).lstrip(':')}` | {cat[i][1]}" if i < len(cat) else " | "
        P(f"| {lt} |  | {rc} |")
    P("")

    P("## IP-movement churn — most-relocated addresses")
    P("")
    P("IPs with the most hosting/location-history observations (migration churn = a "
      "re-hosting / evasion signal). Defensive context, never a target-list.")
    P("")
    P("| IP | history observations |")
    P("|---|---:|")
    for ip, n in a["ip_movement"][:12]:
        P(f"| `{str(ip).lstrip(':')}` | {n} |")
    if not a["ip_movement"]:
        P("| (none in graph) | |")
    P("")

    P("## TLS cert-SAN pivots — shared-infrastructure surface")
    P("")
    P("Certs whose SAN set spans multiple names bridge domains onto shared infra (a CT-log "
      "pivot). `short-lived` / `self-signed` anomalies flagged for review.")
    P("")
    P("| cert subject | SAN count | anomaly |")
    P("|---|---:|---|")
    for subj, nsan, anom in a["cert_pivot"][:12]:
        P(f"| `{subj}` | {nsan} | `{str(anom).lstrip(':')}` |")
    if not a["cert_pivot"]:
        P("| (none in graph) | | |")
    P("")

    P("---")
    P("*Generated by `yabai/methods/analyze.py`. HONEST: R0 bounded `:representative` seed; "
      "malicious examples use illustrative example.* names, NOT real-entity attribution; full CTI "
      "ingest (crt.sh CT logs / passive-DNS feeds) is `methods/ingest.py --live` (G7 operator-gated); "
      "vendor feeds are `:feature-flagged-input`, never system-of-record. kotoba Datom log is the "
      "canonical store (ADR-2605262130); the legacy RisingWave CTI graph is retired.*")
    return "\n".join(L) + "\n"


def render_datoms(b, a):
    L = []
    P = L.append
    P(";; yabai — DERIVED CTI signals (ADR-2605301400 §T3). :derived — NOT re-ingested as fact.")
    P("[")
    for dom, nips, ttl in a["fast_flux"]:
        P(f' {{:cti/fast-flux-domain {edn_str(dom)} :cti/distinct-ips {nips} :cti/ttl {ttl} :cti/derived true}}')
    for pt, n in sorted(a["ptype_load"].items(), key=lambda kv: -kv[1]):
        P(f' {{:cti/hosting-concentration {pt} :cti/observations {n} :cti/derived true}}')
    for tlp, n in sorted(a["tlp_load"].items(), key=lambda kv: -kv[1]):
        P(f' {{:cti/ioc-tlp-load {tlp} :cti/indicators {n} :cti/derived true}}')
    for cat, n in sorted(a["cat_load"].items(), key=lambda kv: -kv[1]):
        P(f' {{:cti/ioc-category-load {cat} :cti/indicators {n} :cti/derived true}}')
    for ip, n in a["ip_movement"]:
        P(f' {{:cti/ip-movement {edn_str(ip)} :cti/history-observations {n} :cti/derived true}}')
    for subj, nsan, anom in a["cert_pivot"]:
        P(f' {{:cti/cert-pivot {edn_str(subj)} :cti/san-count {nsan} :cti/anomaly {anom} :cti/derived true}}')
    P(f' {{:cti/access-audit-total {a["access_total"]} :cti/access-encrypted {a["access_encrypted"]} '
      f':cti/plaintext-violations {a["plaintext_violations"]} :cti/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    default = here / "data" / "passive-dns.merged.kotoba.edn"
    if not default.exists():
        default = here / "data" / "seed-passive-dns.kotoba.edn"
    graph = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else default
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    b = classify(load_edn(graph))
    a = analyze(b)
    (outdir / "intel-report.md").write_text(render_report(b, a), encoding="utf-8")
    (outdir / "cti-signals.kotoba.edn").write_text(render_datoms(b, a), encoding="utf-8")

    print(f"yabai: {a['n_domains']} domains · {a['n_pdns']} passive-DNS · {a['n_certs']} certs · "
          f"{a['n_ioc']} IOCs · fast-flux {len(a['fast_flux'])} · "
          f"encryption {a['access_encrypted']}/{a['access_total']} (viol {a['plaintext_violations']})")
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'cti-signals.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
