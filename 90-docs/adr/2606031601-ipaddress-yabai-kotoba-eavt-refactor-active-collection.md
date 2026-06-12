---
id: adr-2606031601-ipaddress-yabai-kotoba-eavt-refactor-active-collection
renumbered_from: "2606031600"
title: "ADR-2606031601: ipaddress + yabai → kotoba EAVT refactor (ADR-2605301400 §T2/§T3 execution) — active SecurityTrails-class IP/DNS collection on the Datom log"
status: proposed
doc_type: adr
topic: ipaddress-yabai-kotoba-refactor
authoritative: true
last_verified: 2026-06-03
priority: 7.5
axis: actor-architecture
weight: 0.75
priority_note: "Executes the substrate halves of ADR-2605301400 (§T2 ipaddress, §T3 yabai): lifts the world IP/ASN number-resource graph and the passive-DNS/CTI graph off the Kotoba/Datomic / yata Workers-RPC SQL store onto the kotoba Datom log (ADR-2605262130), with authorized ACTIVE collection (RIR delegated-stats / RDAP / reverse-DNS / crt.sh CT logs) — a charter-compliant answer to the SecurityTrails-shaped IP/DNS-intelligence question, framed as a resilience+accountability map, never a target-list."
authoritative_for:
  - kotoba EAVT vocabulary `ip-network-ontology` (RIR/ASN/IPrange/IP/geo/rdns/whois + announce/member edges)
  - kotoba EAVT vocabulary `passive-dns-cti-ontology` (domain/passive-DNS/IP-history/TLS-cert/IOC/access-audit)
  - ipaddress active collector + analyzer (methods/ingest.py + analyze.py) on the Datom log
  - yabai active CTI collector + analyzer (methods/ingest.py + analyze.py) on the Datom log
  - the ACTIVE-collection authorization for these two 1次/CTI actors (offline-default, G7 operator-gated)
depends_on:
  - adr-2605301400-tadori-onchain-tracing-actor-and-kotoba-eavt-migration
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2606022000-kabuto-public-company-supply-chain-kg
  - adr-2606012600-watatsuna-submarine-cable-kg
  - adr-2605301600-danjo-public-accountability-actor
supersedes: []
superseded_by: []
---

# ADR-2606031601: ipaddress + yabai → kotoba EAVT refactor (active IP/DNS collection)

**Status**: proposed
**Date**: 2026-06-03
**Deciders**: Jun Kawasaki

# Context

The recurring question — *"全世界の ipaddress / dns の SecurityTrails のような収集と kotoba
Datomic への保存状況は?"* — exposed a substrate violation. Two actors already collect
SecurityTrails-class data and run in production, but on the **prohibited** store:

- **ipaddress.etzhayyim.com** (1次ソース): RIR feeds, WHOIS/RDAP, GeoIP, reverse-DNS, ASN/CIDR
  — held in Kotoba/Datomic / yata Workers-RPC SQL (`vertex_ip_address` / `vertex_ipaddress_asn` /
  `vertex_ipaddress_range`).
- **yabai.etzhayyim.com** (CTI/risk): passive DNS, IP hosting/location history, TLS/CT-log
  certs, IOC store, access-audit — held in the same SQL graph (`WhoisRecord` / `DnsRecord` /
  `IpHostingHistory` / `TlsCertificate` / `IocIndicator` / `IntelAccessLog` …).

ADR-2605262130 + ADR-2605312345 make the **kotoba Datom log the first-class canonical state**;
Kotoba/Datomic / centralized SQL is prohibited as system-of-record. ADR-2605301400 already named
**tadori** as the consolidation point and specified the migration as phases **§T2 (ipaddress)**
and **§T3 (yabai)** — but only **§T0** (scaffold + a passive operator-staged threat-intel
bridge) had been built. No IP/DNS data lived in kotoba.

The operator explicitly authorized **active (能動的)** collection for this work as
Wellbecoming-relevant, lifting the prior passive-only posture — provided it stays inside the
constitutional envelope (public-record only, resilience-framed, no adherent de-anon, no mass
surveillance, PII encrypted, Murakumo-only inference).

# Decision

Execute the **substrate halves** of ADR-2605301400 by building both actors as **kotoba-native
collectors** following the established kabuto/watatsuna pattern (ontology EDN → seed →
`methods/ingest.py` active bridge → `methods/analyze.py` aggregate-first analyzer).

## §T2 — ipaddress on kotoba EAVT

- **Vocab** `00-contracts/schemas/ip-network-ontology.kotoba.edn`: `:rir/*` `:asn/*`
  `:iprange/*` `:ip/*`, first-class edges `:net.announce/*` (range→origin-ASN) and
  `:net.member/*` (IP→range), enrichment `:geo/*` `:rdns/*` `:whois/*`. Sourcing-honest
  (`:authoritative | :representative | :synthesized`); a `:ip.attr/encrypted` PII guard.
- **Seed** `20-actors/ipaddress/data/seed-ip-network.kotoba.edn`: 5 RIRs, 17 major ASNs, 12
  real CIDR ranges, observed IPs, geo/rdns/whois — all `:representative`, real public facts.
- **Active collector** `methods/ingest.py`: real parsers for RIR **delegated-stats**
  (`registry|cc|type|start|value|date|status`, IPv4 ranges decomposed via
  `ipaddress.summarize_address_range`), **RDAP/WHOIS**, and **reverse-DNS** (`socket`).
  Offline-default; a live network pull requires `--live` **and** `IPADDRESS_OPERATOR_GATE`
  (G7). Dedup-merges with the seed (seed wins) → `data/ip-network.merged.kotoba.edn`.
- **Analyzer** `methods/analyze.py`: RIR delegation coverage, ASN announced-prefix load
  (routing-authority HHI), hosting-class & per-country address space (space HHI), v4/v6 split
  → `out/intel-report.md` + derived `:ipnet/*` datoms.

## §T3 — yabai CTI/DNS on kotoba EAVT

- **Vocab** `00-contracts/schemas/passive-dns-cti-ontology.kotoba.edn`: `:domain/*`
  `:pdns/*` (passive-DNS, as-of), `:iphist/*` (hosting/location history, as-of), `:tlscert/*`
  (CT-log), `:indicator/*` (unified IOC), `:access/*` (access-audit — **always encrypted**).
  `:cti.attr/encrypted` guard; vendor feeds restricted to `:feature-flagged-input`.
- **Seed** `20-actors/yabai/data/seed-passive-dns.kotoba.edn`: domains, passive-DNS, IP-history,
  CT-log certs, IOCs, and one encrypted access record. Malicious examples use illustrative
  `example.*` names — never real-entity attribution. IP refs point into the ipaddress id space.
- **Active collector** `methods/ingest.py`: real **crt.sh** CT-log JSON parser, passive-DNS
  bridge, and a vendor-feed bridge that forces `:feature-flagged-input`. Offline-default; live
  crt.sh pull requires `--live` + `YABAI_OPERATOR_GATE` (G7).
- **Analyzer** `methods/analyze.py`: fast-flux candidates (low TTL × many A answers), hosting
  concentration, IOC TLP/category load, IP-movement churn, cert-SAN pivots, and a **G6/G10
  encryption self-audit** (every `:access/*` must be encrypted) → `out/intel-report.md` +
  derived `:cti/*` datoms.

## Active-collection envelope (constitutional)

Active collection is **authorized but bounded**: (1) PUBLIC number-resource / public CTI
record only; (2) **offline-default + G7 operator-gated** live pulls in code; (3)
**aggregate-first, resilience/accountability-framed** output, never a target-list; (4) **no
host port/vuln scanning** as a primary store (that is the akuma/aratame *caseMandate*
boundary); (5) **no adherent de-anon, no mass surveillance** (G10); (6) **PII encrypted**
(`com.etzhayyim.encrypted.*`, G6); (7) **Murakumo-only** for any narration (G9); (8)
**kotoba-only** store (G11). yabai still SCORES risk; the Council authorizes enforcement;
tadori holds case-anchored evidence — separation of duties preserved.

# Consequences

- **Positive**: the SecurityTrails-shaped IP/DNS-intelligence capability now exists **on the
  canonical Datom log**, charter-compliant; both pipelines run stdlib-only and green; the
  active collectors are real (delegated-stats + crt.sh + rDNS parsers verified offline), not
  stubs; tadori §T2/§T3 are unblocked at the substrate layer.
- **Negative / honest limits**: this is the **substrate** half — the seeds are bounded
  `:representative`; **no live full-universe ingest has run** (G7-gated); the dual-write /
  dual-read **set-equality acceptance gates** of ADR-2605301400 §T2/§T3 (`lookup_ip`/`analyze_ip`
  identical from kotoba; `correlate-ip-activity` set-equal) are **still pending**, so the legacy
  Kotoba/Datomic graphs are **not yet retired** (that is §T4, post-verification, Council Lv6+).
- The production Workers still read Kotoba/Datomic until the dual-read shadow cycle passes; this ADR
  lands the kotoba target model + active ingest beside them, it does not flip the read path.

# Alternatives Considered

1. **Keep passive-only (tadori §T0 bridge) and never collect actively** — rejected: the
   operator authorized active collection as Wellbecoming-relevant, and passive-only cannot
   answer the "world IP/DNS" question at the 1次 layer.
2. **One merged actor instead of two** — rejected: ipaddress (1次 number-resource) and yabai
   (defensive CTI/risk) have distinct gates (PII/encryption, enforcement-routing) and distinct
   id spaces; merging would blur the separation of duties tadori depends on.
3. **Port-scan the world like a full SecurityTrails/Shodan** — rejected: host scanning is the
   akuma/aratame authorized-*caseMandate* boundary (G10 no mass surveillance), out of scope for
   1次 number-resource + public-CTI collection.

# References

- ADR-2605301400 — tadori actor + the §T0–§T4 migration plan this executes (§T2/§T3)
- ADR-2605262130 — kotoba storage substrate unification (no Kotoba/Datomic)
- ADR-2605312345 — kotoba Datom log = first-class canonical state
- ADR-2605181100 — encrypted records (XChaCha20-Poly1305 + Signal key-wrap) for PII
- ADR-2605215000 — Murakumo-only inference
- `00-contracts/schemas/ip-network-ontology.kotoba.edn` · `…/passive-dns-cti-ontology.kotoba.edn`
- `20-actors/ipaddress/methods/{ingest,analyze}.py` · `20-actors/yabai/methods/{ingest,analyze}.py`
