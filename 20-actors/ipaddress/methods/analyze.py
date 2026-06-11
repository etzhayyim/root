#!/usr/bin/env python3
"""ipaddress — number-resource concentration analyzer (ADR-2605301400 §T2).

Reads a kotoba-EDN IP/ASN graph (:rir/* :asn/* :iprange/* :ip/* :net.announce/*
:geo/* :rdns/* :whois/*) and emits, AGGREGATE-FIRST:

  1. out/intel-report.md — where the world's IP number resources concentrate:
     RIR delegation coverage, ASN origin-prefix load, hosting-class address-space
     load, per-country address space, and an address-space Herfindahl index.
  2. out/ip-concentration.kotoba.edn — the derived :ipnet/* datoms, flagged
     :derived — never re-ingested as authoritative fact.

CONSTITUTIONAL framing (ipaddress G2/G10): this is a number-resource RESILIENCE +
accountability map, NEVER a target-list. Concentration is ranked so the public can
see where address space / routing authority piles up — it does NOT say "which prefix
to attack". No host is probed; no adherent is de-anonymised.

stdlib only. Usage:
    python3 analyze.py [graph.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ip_edn import load_edn, classify, edn_str  # noqa: E402


def analyze(b):
    rirs, asns, ranges = b["rirs"], b["asns"], b["ranges"]
    announces, members, ips = b["announces"], b["members"], b["ips"]
    geos, rdns, whois = b["geos"], b["rdns"], b["whois"]

    # range → origin ASN (from announce edges)
    range_asn = {}
    for e in announces:
        range_asn[e.get(":net.announce/range")] = e.get(":net.announce/asn")

    rir_addr = defaultdict(int)     # rir -> Σ host-count
    rir_ranges = defaultdict(int)   # rir -> # ranges
    country_addr = defaultdict(int)
    hosting_addr = defaultdict(int)
    asn_addr = defaultdict(int)     # asn -> Σ host-count of announced ranges
    v4 = v6 = 0

    for rid, r in ranges.items():
        hc = int(r.get(":iprange/host-count", 0) or 0)
        rir = r.get(":iprange/rir")
        if rir:
            rir_addr[rir] += hc
            rir_ranges[rir] += 1
        country_addr[r.get(":iprange/country", "ZZ")] += hc
        if r.get(":iprange/version") == 6:
            v6 += 1
        else:
            v4 += 1
        asn = range_asn.get(rid)
        if asn:
            asn_addr[asn] += hc
            hc_cls = asns.get(asn, {}).get(":asn/hosting-class", ":unknown")
            hosting_addr[hc_cls] += hc

    # ASN origin-prefix load (declared prefix-count; routing-authority concentration)
    asn_prefix = sorted(
        ((aid, a.get(":asn/name", aid), int(a.get(":asn/prefix-count", 0) or 0),
          a.get(":asn/hosting-class", ":unknown"), a.get(":asn/country", "ZZ"))
         for aid, a in asns.items()),
        key=lambda r: -r[2])

    # address-space HHI across hosting classes (concentration of routed space)
    tot_host = sum(hosting_addr.values()) or 1
    space_hhi = round(sum((v / tot_host) ** 2 for v in hosting_addr.values()), 4)

    # prefix-load HHI across ASNs (routing-authority concentration)
    tot_pref = sum(p for _i, _n, p, _c, _cc in asn_prefix) or 1
    prefix_hhi = round(sum((p / tot_pref) ** 2 for _i, _n, p, _c, _cc in asn_prefix), 4)

    return dict(
        rir_addr=rir_addr, rir_ranges=rir_ranges, country_addr=country_addr,
        hosting_addr=hosting_addr, asn_addr=asn_addr, asn_prefix=asn_prefix,
        v4=v4, v6=v6, space_hhi=space_hhi, prefix_hhi=prefix_hhi,
        n_ips=len(ips), n_geo=len(geos), n_rdns=len(rdns), n_whois=len(whois),
        n_announce=len(announces), n_member=len(members),
    )


def _name(rirs, rid):
    return rirs.get(rid, {}).get(":rir/name", rid)


def render_report(b, a):
    rirs, asns = b["rirs"], b["asns"]
    L = []
    P = L.append
    P("# ipaddress — world IP/ASN number-resource concentration report")
    P("")
    P("> ADR-2605301400 §T2 · **kotoba-native** (Datom log; NO RisingWave) · **aggregate-first** · "
      "number-resource RESILIENCE + accountability map (NOT a target-list). No host is probed; "
      "no adherent is de-anonymised. Sourcing `:representative` unless an operator-gated live RIR "
      "pull tagged it `:authoritative`.")
    P("")
    P(f"- RIRs: **{len(rirs)}**  ·  ASNs: **{len(asns)}**  ·  ranges: **{a['v4']+a['v6']}** "
      f"(v4 {a['v4']} / v6 {a['v6']})  ·  observed IPs: **{a['n_ips']}**")
    P(f"- enrichment: geo **{a['n_geo']}** · rDNS **{a['n_rdns']}** · whois **{a['n_whois']}** · "
      f"announce edges **{a['n_announce']}** · membership edges **{a['n_member']}**")
    P("")

    P("## RIR delegation coverage")
    P("")
    P("Address space + range count delegated per Regional Internet Registry in the graph.")
    P("")
    P("| RIR | ranges | Σ IPv4-equiv addresses |")
    P("|---|---:|---:|")
    for rir, addr in sorted(a["rir_addr"].items(), key=lambda kv: -kv[1]):
        P(f"| {_name(rirs, rir)} | {a['rir_ranges'].get(rir, 0)} | {addr:,} |")
    P("")

    P("## ASN routing-authority load — announced-prefix concentration")
    P("")
    P(f"Declared announced-prefix count per ASN (origin-routing concentration). "
      f"Prefix-load **HHI = {a['prefix_hhi']}** (Σ share²; higher = routing authority piled "
      "into fewer AS operators). Routed to multi-homing / diversity, never to interdiction.")
    P("")
    P("| ASN | name | hosting-class | country | announced prefixes |")
    P("|---|---|---|---|---:|")
    for aid, name, pref, cls, cc in a["asn_prefix"][:15]:
        P(f"| `{str(aid).lstrip(':')}` | {name} | `{str(cls).lstrip(':')}` | {cc} | {pref:,} |")
    P("")

    P("## Hosting-class address-space load")
    P("")
    P(f"Σ routed address space by operator hosting-class (cloud/cdn/residential/transit/…). "
      f"Address-space **HHI = {a['space_hhi']}**. Surfaces how much of the observed routed "
      "space sits behind a few cloud/CDN operators — an accountability signal, aggregate-first.")
    P("")
    P("| hosting-class | Σ IPv4-equiv addresses |")
    P("|---|---:|")
    for cls, addr in sorted(a["hosting_addr"].items(), key=lambda kv: -kv[1]):
        P(f"| `{str(cls).lstrip(':')}` | {addr:,} |")
    if not a["hosting_addr"]:
        P("| (no announce edges in graph) | |")
    P("")

    P("## Per-country delegated address space")
    P("")
    P("Σ delegated address space per registrant country (geographic concentration of "
      "number resources). Routed to equitable allocation visibility, never a target-list.")
    P("")
    P("| country | Σ IPv4-equiv addresses |")
    P("|---|---:|")
    for cc, addr in sorted(a["country_addr"].items(), key=lambda kv: -kv[1])[:15]:
        P(f"| `{cc}` | {addr:,} |")
    P("")

    P("---")
    P("*Generated by `ipaddress/methods/analyze.py`. HONEST: R0 bounded `:representative` seed of "
      "public number-resource records; host-counts from delegated-stats / seed; absence = \"not yet "
      "ingested\". Full RIR/RDAP universe ingest is `methods/ingest.py --live` (G7 operator-gated). "
      "kotoba Datom log is the canonical store (ADR-2605262130); the legacy RisingWave graph is retired.*")
    return "\n".join(L) + "\n"


def render_datoms(b, a):
    rirs = b["rirs"]
    L = []
    P = L.append
    P(";; ipaddress — DERIVED number-resource concentration datoms (ADR-2605301400 §T2).")
    P(";; :derived — recomputed from the graph; NOT re-ingested as :authoritative fact.")
    P("[")
    for rir, addr in sorted(a["rir_addr"].items(), key=lambda kv: -kv[1]):
        P(f' {{:ipnet/rir-coverage {edn_str(_name(rirs, rir))} :ipnet/rir {edn_str(rir)} '
          f':ipnet/ranges {a["rir_ranges"].get(rir, 0)} :ipnet/addresses {addr} :ipnet/derived true}}')
    for aid, name, pref, cls, cc in a["asn_prefix"]:
        P(f' {{:ipnet/asn-prefix-load {edn_str(aid)} :ipnet/asn-name {edn_str(name)} '
          f':ipnet/prefixes {pref} :ipnet/hosting-class {cls} :ipnet/derived true}}')
    for cls, addr in sorted(a["hosting_addr"].items(), key=lambda kv: -kv[1]):
        P(f' {{:ipnet/hosting-class-load {cls} :ipnet/addresses {addr} :ipnet/derived true}}')
    for cc, addr in sorted(a["country_addr"].items(), key=lambda kv: -kv[1]):
        P(f' {{:ipnet/country-load {edn_str(cc)} :ipnet/addresses {addr} :ipnet/derived true}}')
    P(f' {{:ipnet/space-hhi {a["space_hhi"]} :ipnet/prefix-hhi {a["prefix_hhi"]} '
      f':ipnet/v4-ranges {a["v4"]} :ipnet/v6-ranges {a["v6"]} :ipnet/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    default = here / "data" / "ip-network.merged.kotoba.edn"
    if not default.exists():
        default = here / "data" / "seed-ip-network.kotoba.edn"
    graph = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else default
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    b = classify(load_edn(graph))
    a = analyze(b)
    (outdir / "intel-report.md").write_text(render_report(b, a), encoding="utf-8")
    (outdir / "ip-concentration.kotoba.edn").write_text(render_datoms(b, a), encoding="utf-8")

    print(f"ipaddress: {len(b['rirs'])} RIRs · {len(b['asns'])} ASNs · "
          f"{a['v4']+a['v6']} ranges · prefix-HHI {a['prefix_hhi']} · space-HHI {a['space_hhi']}")
    top = a["asn_prefix"][:3]
    print("top ASNs by prefix: " + ", ".join(f"{n} {p:,}" for _i, n, p, _c, _cc in top))
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'ip-concentration.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
