#!/usr/bin/env python3
"""sukashi 透かし — ad-tech supply-chain integrity + fraud-network concentration analyzer.

ADR-2606071600. Reads a kotoba-EDN ad-tech graph (:adtech/* entities, :adauth.edge/*
ads.txt/sellers.json authorization edges, :adcreative/* creatives, :addelivery.edge/*
serving-infrastructure edges, :adfraud.signal/* fraud signals) and emits:

  1. an AGGREGATE-FIRST ad-tech transparency + fraud-protection report (out/intel-report.md):
     where the authorization handshake is broken (declared-but-unconfirmed / spoofed), where
     scam advertising concentrates onto one hosting ASN / registrar, and which advertiser
     categories carry the most fraud signal — framed toward takedown-referral + consumer
     protection.
  2. the derived concentration + fraud-cluster datoms (out/ad-fraud-clusters.kotoba.edn),
     flagged :derived — never re-ingested as authoritative fact.

CONSTITUTIONAL framing (sukashi G2/G3/G4): this is a fraud-PROTECTION + ad-tech TRANSPARENCY
map, NEVER a target-list and NEVER an ad-buying/optimization tool. sukashi does NOT adjudicate
— it surfaces signals + clusters routed to actors that act (akashi's malak bridge / kurashimori
/ tasuke / danjo). Concentration is ranked so inventory can be de-spoofed and victims protected,
NOT to identify "who to hit".

stdlib only (no numpy). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sukashi_edn import load_edn, classify, edn_str  # noqa: E402


def analyze(adtech, auth, creatives, delivery, fraud):
    # ── supply-chain authorization integrity ──
    seller_fan_out = defaultdict(set)        # seller -> {publishers authorizing it}
    publisher_sellers = defaultdict(set)     # publisher -> {sellers it authorizes}
    seller_declared = defaultdict(int)       # seller -> # declared edges
    seller_unconfirmed = defaultdict(int)    # seller -> # declared && !confirmed edges
    reseller_edges = 0
    for e in auth:
        s = e.get(':adauth.edge/seller')
        p = e.get(':adauth.edge/publisher')
        if not s or not p:
            continue
        seller_fan_out[s].add(p)
        publisher_sellers[p].add(s)
        if e.get(':adauth.edge/declared'):
            seller_declared[s] += 1
            if not e.get(':adauth.edge/confirmed'):
                seller_unconfirmed[s] += 1
        if e.get(':adauth.edge/relationship') == ':reseller':
            reseller_edges += 1

    # unconfirmed-rate per seller (the unauthorized/spoofed-inventory surface)
    unconfirmed_rate = []
    for s, dec in seller_declared.items():
        unc = seller_unconfirmed.get(s, 0)
        rate = round(unc / dec, 3) if dec else 0.0
        if unc > 0:
            unconfirmed_rate.append((s, unc, dec, rate))
    unconfirmed_rate.sort(key=lambda r: (-r[3], -r[1]))

    # account-id collisions across DIFFERENT publishers selling to the SAME seller =
    # a domain-spoof / impersonation surface (two domains claim one publisher account).
    acct_claims = defaultdict(set)  # (seller, account-id) -> {publishers}
    for e in auth:
        s = e.get(':adauth.edge/seller')
        acct = e.get(':adauth.edge/account-id')
        p = e.get(':adauth.edge/publisher')
        if s and acct and p:
            acct_claims[(s, acct)].add(p)
    acct_collisions = [(s, acct, sorted(ps)) for (s, acct), ps in acct_claims.items() if len(ps) > 1]
    acct_collisions.sort(key=lambda r: -len(r[2]))

    seller_fan_rank = sorted(((s, len(ps)) for s, ps in seller_fan_out.items()), key=lambda r: -r[1])

    # ── delivery-infrastructure concentration (where scam delivery piles up) ──
    # join each delivery edge to the creative's fraud weight (Σ confidence of its signals).
    creative_fraud = defaultdict(float)
    subj_fraud = defaultdict(float)          # any subject id -> Σ confidence
    subj_kinds = defaultdict(set)            # any subject id -> {distinct fraud kinds}
    fraud_kind_count = defaultdict(int)
    for f in fraud:
        subj = f.get(':adfraud.signal/subject')
        conf = float(f.get(':adfraud.signal/confidence', 0.0) or 0.0)
        kind = f.get(':adfraud.signal/kind', ':unknown')
        subj_fraud[subj] += conf
        subj_kinds[subj].add(kind)
        fraud_kind_count[kind] += 1
        if subj and subj.startswith('adc.'):
            creative_fraud[subj] += conf

    cre_by_id = {c.get(':adcreative/id'): c for c in creatives}
    asn_load = defaultdict(float)            # asn -> Σ fraud-weighted delivery
    registrar_load = defaultdict(float)
    whois_load = defaultdict(float)
    asn_members = defaultdict(set)           # asn -> {creatives}
    registrar_members = defaultdict(set)
    for d in delivery:
        cre = d.get(':addelivery.edge/creative')
        w = creative_fraud.get(cre, 0.0)
        asn = d.get(':addelivery.edge/asn')
        reg = d.get(':addelivery.edge/registrar')
        org = d.get(':addelivery.edge/whois-org')
        if asn:
            asn_load[asn] += w
            if cre:
                asn_members[asn].add(cre)
        if reg:
            registrar_load[reg] += w
            if cre:
                registrar_members[reg].add(cre)
        if org:
            whois_load[org] += w
    infra_rank = sorted(((a, round(v, 2), len(asn_members[a])) for a, v in asn_load.items() if v > 0),
                        key=lambda r: -r[1])
    registrar_rank = sorted(((r, round(v, 2), len(registrar_members[r])) for r, v in registrar_load.items() if v > 0),
                            key=lambda r: -r[1])

    # ── fraud clusters: creatives sharing serving infra (ASN ∧ registrar ∧ whois-org) ──
    # AND carrying ≥1 fraud signal = a candidate scam-ad NETWORK. Aggregate-first; the
    # advertiser names within stay :synthesized/illustrative. Cluster key = the shared infra.
    infra_to_creatives = defaultdict(set)
    infra_meta = {}
    for d in delivery:
        cre = d.get(':addelivery.edge/creative')
        asn = d.get(':addelivery.edge/asn')
        reg = d.get(':addelivery.edge/registrar')
        org = d.get(':addelivery.edge/whois-org')
        if not cre or creative_fraud.get(cre, 0.0) <= 0:
            continue
        key = (asn, reg, org)
        infra_to_creatives[key].add(cre)
        infra_meta[key] = dict(asn=asn, registrar=reg, whois_org=org)
    clusters = []
    for key, cres in infra_to_creatives.items():
        if len(cres) < 2:   # a cluster needs ≥2 co-hosted scam creatives
            continue
        advertisers = sorted({cre_by_id.get(c, {}).get(':adcreative/advertiser') for c in cres} - {None})
        conf_sum = round(sum(creative_fraud.get(c, 0.0) for c in cres), 2)
        # MULTI-SIGNAL CORROBORATION: distinct fraud-signal kinds across the cluster's
        # member creatives. More distinct kinds = independent evidence corroborating one
        # operation (a crypto + a deepfake + a counterfeit ad on one bulletproof host is
        # stronger than three of the same) → a higher-confidence protection priority.
        kinds = set()
        for c in cres:
            kinds |= subj_kinds.get(c, set())
        corroboration = len(kinds)
        m = infra_meta[key]
        # rank weighted by corroboration so multi-kind networks surface first.
        rank_score = round(len(cres) * conf_sum * (1 + 0.5 * max(0, corroboration - 1)), 2)
        clusters.append(dict(asn=m['asn'], registrar=m['registrar'], whois_org=m['whois_org'],
                             creatives=sorted(cres), advertisers=advertisers,
                             conf_sum=conf_sum, members=len(cres),
                             kinds=sorted(str(k).lstrip(':') for k in kinds),
                             corroboration=corroboration, rank_score=rank_score))
    clusters.sort(key=lambda c: -c['rank_score'])

    # ── fraud-signal load by advertiser category (which verticals carry the scam surface) ──
    adv_cat = {a.get(':adtech/id'): a.get(':adtech/category', ':unknown') for a in adtech.values()}
    category_load = defaultdict(float)
    for f in fraud:
        subj = f.get(':adfraud.signal/subject')
        conf = float(f.get(':adfraud.signal/confidence', 0.0) or 0.0)
        cre = cre_by_id.get(subj)
        cat = None
        if cre:
            cat = cre.get(':adcreative/category') or adv_cat.get(cre.get(':adcreative/advertiser'))
        elif subj in adv_cat:
            cat = adv_cat[subj]
        category_load[cat or ':unknown'] += conf
    category_rank = sorted(category_load.items(), key=lambda kv: -kv[1])

    # ── routing tally: who acts on the signals (sukashi does not) ──
    routed = defaultdict(int)
    for f in fraud:
        routed[f.get(':adfraud.signal/routed-to', ':unrouted')] += 1

    return dict(
        seller_fan_rank=seller_fan_rank,
        publisher_sellers={p: len(s) for p, s in publisher_sellers.items()},
        unconfirmed_rate=unconfirmed_rate,
        acct_collisions=acct_collisions,
        reseller_edges=reseller_edges,
        infra_rank=infra_rank,
        registrar_rank=registrar_rank,
        clusters=clusters,
        category_rank=category_rank,
        fraud_kind_count=dict(fraud_kind_count),
        routed=dict(routed),
        subj_fraud=subj_fraud,
    )


def aname(adtech, aid):
    return adtech.get(aid, {}).get(':adtech/name', aid)


def render_report(adtech, auth, creatives, delivery, fraud, a):
    L = []
    P = L.append
    P("# sukashi 透かし — ad-tech supply-chain integrity + fraud-network report")
    P("")
    P("> ADR-2606071600 · **aggregate-first** · ad-tech fraud-PROTECTION + TRANSPARENCY map "
      "(NOT a target-list, NOT an ad-buying tool; sukashi G2). sukashi does NOT adjudicate (G4) — "
      "every fraud signal is an evidence-bearing observation **routed** to an actor that acts "
      "(akashi malak bridge / kurashimori / tasuke / danjo). All fraud examples are attached to "
      "CLEARLY-FICTIONAL illustrative entities (`.test`/`.example` + RFC-5737 doc IP ranges); real "
      "ad-tech firms carry NO fraud signal (non-adjudication).")
    P("")
    roles = defaultdict(int)
    for e in adtech.values():
        roles[e.get(':adtech/role', ':unknown')] += 1
    P(f"- ad-tech entities: **{len(adtech)}**  ·  authorization edges (ads.txt/sellers.json): "
      f"**{len(auth)}**  ·  creatives: **{len(creatives)}**  ·  delivery edges: **{len(delivery)}**  "
      f"·  fraud signals: **{len(fraud)}**")
    P(f"- roles covered: " + ", ".join(
        f"`{str(r).lstrip(':')}` {n}" for r, n in sorted(roles.items(), key=lambda kv: -kv[1])))
    P("")

    # ── authorization-handshake integrity (the headline supply-chain signal) ──
    P("## Authorization-handshake integrity — unauthorized / unconfirmed sellers")
    P("")
    P("Per seller: declared edges (a publisher's ads.txt names it) that are NOT confirmed in the "
      "seller's sellers.json. A declared-but-unconfirmed edge is the **unauthorized / spoofed-"
      "inventory surface** — the headline ad-tech-fraud signal. Routed to de-spoofing + takedown-"
      "referral, never to interdiction (G2).")
    P("")
    P("| seller | unconfirmed | declared | unconfirmed-rate |")
    P("|---|---:|---:|---:|")
    for s, unc, dec, rate in a['unconfirmed_rate']:
        P(f"| {aname(adtech, s)} | {unc} | {dec} | {rate} |")
    if not a['unconfirmed_rate']:
        P("| (none in seed — every declared edge confirmed) | | | |")
    P("")

    # ── account-id collisions (domain-spoof surface) ──
    P("## Account-id collisions — publisher-impersonation (domain-spoof) surface")
    P("")
    P("One seller account-id claimed by MORE THAN ONE publisher domain = a candidate "
      "publisher-impersonation: a spoofed domain claims a legitimate publisher's account to "
      "monetize counterfeit inventory. Routed to the affected publisher + exchange, never a target (G2).")
    P("")
    P("| seller | account-id | claiming publishers |")
    P("|---|---|---|")
    for s, acct, ps in a['acct_collisions']:
        P(f"| {aname(adtech, s)} | `{acct}` | " + ", ".join(aname(adtech, p) for p in ps) + " |")
    if not a['acct_collisions']:
        P("| (none in seed) | | |")
    P("")

    # ── delivery-infrastructure concentration ──
    P("## Delivery-infrastructure concentration — where scam delivery piles up")
    P("")
    P("Σ fraud-weighted creative delivery per hosting ASN (fraud weight = Σ confidence of the "
      "creative's signals). High = scam advertising concentrates onto one hosting network — a "
      "takedown-referral + resilience priority, NEVER a target-list (G2). Reuses ip-network-"
      "ontology `:asn` ids (tadori substrate, ADR-2606031600).")
    P("")
    P("| hosting ASN | Σ fraud-weighted delivery | scam creatives |")
    P("|---|---:|---:|")
    for asn, load, n in a['infra_rank']:
        P(f"| `{str(asn).lstrip(':')}` | {load} | {n} |")
    if not a['infra_rank']:
        P("| (none in seed) | | |")
    P("")
    P("Registrar concentration (a fraud-cluster co-occurrence key):")
    P("")
    P("| registrar | Σ fraud-weighted delivery | scam creatives |")
    P("|---|---:|---:|")
    for reg, load, n in a['registrar_rank']:
        P(f"| {reg} | {load} | {n} |")
    if not a['registrar_rank']:
        P("| (none in seed) | | |")
    P("")

    # ── fraud clusters (candidate scam-ad networks) ──
    P("## Candidate scam-ad networks — creatives sharing serving infrastructure")
    P("")
    P("Creatives that share serving infrastructure (ASN ∧ registrar ∧ WHOIS-org) AND each carry "
      "≥1 fraud signal = a candidate scam-ad **network**. Ranked by members × Σ confidence. "
      "AGGREGATE-FIRST + NON-ADJUDICATING (G4): a candidate for protection actors to investigate, "
      "never a verdict. Routed to akashi's malak evidence bridge.")
    P("")
    P("| shared ASN | registrar | WHOIS-org | creatives | distinct fraud kinds (corroboration) | Σ confidence | rank |")
    P("|---|---|---|---:|---|---:|---:|")
    for c in a['clusters']:
        kinds = ", ".join(f"`{k}`" for k in c['kinds']) + f" ({c['corroboration']})"
        P(f"| `{str(c['asn']).lstrip(':')}` | {c['registrar']} | {c['whois_org']} | "
          f"{c['members']} | {kinds} | {c['conf_sum']} | {c['rank_score']} |")
    if not a['clusters']:
        P("| (none in seed) | | | | | | |")
    P("")
    P("> **Multi-signal corroboration**: distinct fraud-signal kinds across a cluster's "
      "creatives. Independent kinds (e.g. scam-finance + fake-endorsement + counterfeit-goods on "
      "one bulletproof host) corroborate a single operation more strongly than repeats — the rank "
      "weights corroboration so multi-kind networks surface first. Still NON-ADJUDICATING (G4): a "
      "stronger candidate for protection actors, never a verdict.")
    P("")

    # ── fraud by category ──
    P("## Fraud-signal load by advertiser category — high-risk verticals")
    P("")
    P("Σ fraud-signal confidence per advertiser category — which verticals (finance / crypto / "
      "health-supplement / gambling) the scam surface concentrates in. A consumer-protection "
      "prioritization signal (routed to kurashimori), never a target-list (G2).")
    P("")
    P("| category | Σ fraud confidence |")
    P("|---|---:|")
    for cat, load in a['category_rank']:
        P(f"| `{str(cat).lstrip(':')}` | {round(load, 2)} |")
    if not a['category_rank']:
        P("| (none in seed) | |")
    P("")

    # ── fraud-kind + routing tallies ──
    P("## Fraud-signal taxonomy + routing — who acts (sukashi does not)")
    P("")
    P("| fraud kind | count |   | routed to | count |")
    P("|---|---:|---|---|---:|")
    kinds = sorted(a['fraud_kind_count'].items(), key=lambda kv: -kv[1])
    routes = sorted(a['routed'].items(), key=lambda kv: -kv[1])
    for i in range(max(len(kinds), len(routes))):
        lk = f"`{str(kinds[i][0]).lstrip(':')}`" if i < len(kinds) else ""
        lkn = kinds[i][1] if i < len(kinds) else ""
        rk = f"`{str(routes[i][0]).lstrip(':')}`" if i < len(routes) else ""
        rkn = routes[i][1] if i < len(routes) else ""
        P(f"| {lk} | {lkn} |  | {rk} | {rkn} |")
    P("")
    P("> Routing legend: `akashi-malak` = handed to akashi's `com.etzhayyim.akashi."
      "malakEvidenceCandidate` bridge (evidence-only, never an accusation); `kurashimori` = "
      "consumer-protection concierge; `tasuke` = cybercrime-victim support; `danjo` = public "
      "accountability. **sukashi observes; these actors act.**")
    P("")

    # ── most-systemic legit sellers (transparency, not targeting) ──
    P("## Seller fan-out — most-authorized sellers (transparency signal)")
    P("")
    P("# distinct publishers that authorize each seller in their ads.txt. High = a systemic "
      "seller many sites depend on — a transparency signal (where supply-chain power concentrates), "
      "never a target (G2).")
    P("")
    P("| seller | publishers authorizing |")
    P("|---|---:|")
    for s, n in a['seller_fan_rank'][:15]:
        P(f"| {aname(adtech, s)} | {n} |")
    P("")

    P("---")
    P("*Generated by `sukashi/methods/analyze.py`. HONEST: R0 bounded seed; real ad-tech firms "
      "+ genuinely-public ads.txt/sellers.json facts are :representative/:authoritative and carry "
      "NO fraud signal; every fraud example is :synthesized on a CLEARLY-FICTIONAL illustrative "
      "entity. Full-web ads.txt / sellers.json / WHOIS crawl is G7 Council + operator gated. "
      "sukashi is an observatory, NOT an ad network (G2); it does NOT adjudicate (G4).*")
    return "\n".join(L) + "\n"


def render_datoms(a):
    L = []
    P = L.append
    P(";; sukashi — DERIVED ad-tech concentration + fraud-cluster datoms (ADR-2606071600).")
    P(";; :derived — NOT fact. Recomputed from the seed graph; do not re-ingest as :authoritative.")
    P("[")
    for s, unc, dec, rate in a['unconfirmed_rate']:
        P(f' {{:adsupply/seller {edn_str(s)} :adsupply/unconfirmed {unc} '
          f':adsupply/declared {dec} :adsupply/unconfirmed-rate {rate} :adsupply/derived true}}')
    for s, n in a['seller_fan_rank']:
        P(f' {{:adsupply/seller {edn_str(s)} :adsupply/seller-fan-out {n} :adsupply/derived true}}')
    for asn, load, n in a['infra_rank']:
        P(f' {{:adsupply/asn {edn_str(asn)} :adsupply/infra-concentration {load} '
          f':adsupply/scam-creatives {n} :adsupply/derived true}}')
    for c in a['clusters']:
        P(f' {{:adfraud/cluster {edn_str(str(c["asn"]) + "|" + str(c["registrar"]))} '
          f':adfraud/cluster-asn {edn_str(c["asn"])} :adfraud/cluster-registrar {edn_str(c["registrar"])} '
          f':adfraud/cluster-members {c["members"]} :adfraud/cluster-confidence {c["conf_sum"]} '
          f':adfraud/cluster-corroboration {c["corroboration"]} '
          f':adfraud/network-rank {c["rank_score"]} :adfraud/derived true}}')
    for cat, load in a['category_rank']:
        P(f' {{:adfraud/category {edn_str(str(cat).lstrip(":"))} '
          f':adfraud/category-load {round(load, 2)} :adfraud/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-ad-supply-chain.kotoba.edn"
    merged = here / "data" / "ad-supply-chain.merged.kotoba.edn"
    if seed == here / "data" / "seed-ad-supply-chain.kotoba.edn" and merged.exists():
        seed = merged
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    adtech, auth, creatives, delivery, fraud = classify(rows)
    a = analyze(adtech, auth, creatives, delivery, fraud)

    (outdir / "intel-report.md").write_text(
        render_report(adtech, auth, creatives, delivery, fraud, a), encoding='utf-8')
    (outdir / "ad-fraud-clusters.kotoba.edn").write_text(render_datoms(a), encoding='utf-8')

    print(f"sukashi: {len(adtech)} ad-tech entities, {len(auth)} auth edges, "
          f"{len(creatives)} creatives, {len(delivery)} delivery edges, {len(fraud)} fraud signals")
    print(f"unauthorized/unconfirmed sellers: {len(a['unconfirmed_rate'])}  ·  "
          f"account-id collisions (spoof surface): {len(a['acct_collisions'])}  ·  "
          f"candidate scam-ad networks: {len(a['clusters'])}")
    if a['infra_rank']:
        top = a['infra_rank'][0]
        print(f"top scam-delivery ASN: {str(top[0]).lstrip(':')} (fraud-weight {top[1]}, {top[2]} creatives)")
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'ad-fraud-clusters.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
