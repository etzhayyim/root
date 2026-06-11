#!/usr/bin/env python3
"""kabuto 兜 — global public-company supply-chain concentration analyzer.

ADR-2606022000. Reads a kotoba-EDN company graph (:company/* listed companies,
:company.address/* HQ, :company.contact/* public contact, :supply.edge/*
supplier→customer edges, :company.process/* BPMN refs) and emits:

  1. an AGGREGATE-FIRST supply-chain intel report (out/intel-report.md) — where
     the world's production concentrates onto a single-source supplier, a sector,
     or one jurisdiction, framed toward redundancy + accountability.
  2. the derived concentration datoms (out/supply-criticality.kotoba.edn),
     flagged :derived — never re-ingested as authoritative fact.

CONSTITUTIONAL framing (kabuto G2/G3/G4): this is a supply-chain RESILIENCE +
corporate-power TRANSPARENCY map, NEVER a target-list. Concentration is ranked so
buyers can DIVERSIFY and the public can hold concentration accountable — it does
NOT identify "who to hit". kabuto does not adjudicate; it states public facts.

stdlib only (no numpy). Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kabuto_edn import load_edn, classify, edn_str  # noqa: E402


# ISO-3166 alpha-2 → macro region bloc (for regional supply concentration).
# Kept in sync with the seed's country coverage so cross-bloc / regional metrics
# don't silently bucket new countries into "Other".
_BLOC = {
    'JP': 'East Asia', 'KR': 'East Asia', 'CN': 'East Asia', 'TW': 'East Asia', 'HK': 'East Asia',
    'MO': 'East Asia',
    'US': 'North America', 'CA': 'North America', 'MX': 'North America',
    'NL': 'Europe', 'DE': 'Europe', 'FR': 'Europe', 'CH': 'Europe', 'GB': 'Europe', 'IE': 'Europe',
    'ES': 'Europe', 'IT': 'Europe', 'SE': 'Europe', 'FI': 'Europe', 'DK': 'Europe', 'NO': 'Europe',
    'LU': 'Europe', 'PL': 'Europe', 'AT': 'Europe', 'PT': 'Europe', 'SI': 'Europe', 'HR': 'Europe',
    'LT': 'Europe', 'IS': 'Europe', 'GR': 'Europe', 'CZ': 'Europe', 'HU': 'Europe', 'RO': 'Europe',
    'IN': 'South Asia', 'BD': 'South Asia', 'PK': 'South Asia', 'LK': 'South Asia',
    'SG': 'SE Asia', 'ID': 'SE Asia', 'TH': 'SE Asia', 'MY': 'SE Asia', 'VN': 'SE Asia', 'PH': 'SE Asia',
    'SA': 'Middle East', 'AE': 'Middle East', 'QA': 'Middle East', 'KW': 'Middle East',
    'BH': 'Middle East', 'OM': 'Middle East', 'JO': 'Middle East', 'IL': 'Middle East', 'TR': 'Middle East',
    'BR': 'Latin America', 'CL': 'Latin America', 'CO': 'Latin America', 'AR': 'Latin America',
    'PE': 'Latin America', 'PA': 'Latin America',
    'ZA': 'Africa', 'NG': 'Africa', 'EG': 'Africa', 'KE': 'Africa', 'MA': 'Africa',
    'CI': 'Africa', 'GH': 'Africa',
    'AU': 'Oceania', 'NZ': 'Oceania',
    'GE': 'Eurasia', 'KZ': 'Eurasia',
}


def _bloc(country):
    return _BLOC.get(country, 'Other')


def analyze(companies, edges):
    in_deg = defaultdict(set)    # customer -> {suppliers}
    out_deg = defaultdict(set)   # supplier -> {customers}
    # criticality-weighted supplier load per customer-commodity
    cust_commodity_suppliers = defaultdict(list)  # (customer, commodity) -> [(supplier, crit)]
    sector_concentration = defaultdict(float)     # (supplier_sector, commodity) -> Σ crit
    jurisdiction_load = defaultdict(float)        # supplier_country -> Σ crit
    bloc_load = defaultdict(float)                 # supplier macro-region bloc -> Σ crit
    systemic = defaultdict(float)                 # supplier -> Σ crit it supplies outward

    for e in edges:
        s = e.get(':supply.edge/from')
        c = e.get(':supply.edge/to')
        crit = float(e.get(':supply.edge/criticality', 0.0) or 0.0)
        commodity = e.get(':supply.edge/commodity', ':unknown')
        if not s or not c:
            continue
        in_deg[c].add(s)
        out_deg[s].add(c)
        cust_commodity_suppliers[(c, commodity)].append((s, crit))
        systemic[s] += crit
        sec = companies.get(s, {}).get(':company/sector', ':unknown')
        sector_concentration[(sec, commodity)] += crit
        country = companies.get(s, {}).get(':company/country', '??')
        jurisdiction_load[country] += crit
        bloc_load[_bloc(country)] += crit

    # single-source: a (customer, commodity) met by exactly one disclosed supplier
    # at high criticality (≥ 0.7) — the brittle redundancy gaps.
    single_source = []
    for (c, commodity), sups in cust_commodity_suppliers.items():
        if len(sups) == 1:
            sup, crit = sups[0]
            if crit >= 0.7:
                single_source.append((c, commodity, sup, crit))
    single_source.sort(key=lambda r: -r[3])

    # MATURITY — customer supplier-sector diversification: # distinct supplier
    # sectors a customer draws on (lower at high inbound criticality = brittle).
    cust_supplier_sectors = defaultdict(set)
    cust_in_crit = defaultdict(float)
    for e in edges:
        s = e.get(':supply.edge/from')
        c = e.get(':supply.edge/to')
        if not s or not c:
            continue
        cust_supplier_sectors[c].add(companies.get(s, {}).get(':company/sector', ':unknown'))
        cust_in_crit[c] += float(e.get(':supply.edge/criticality', 0.0) or 0.0)
    # diversification index = distinct-supplier-sectors / Σ inbound criticality
    # (low = much dependency concentrated in few sectors). Rank brittle-first.
    diversification = []
    for c in cust_in_crit:
        secs = len(cust_supplier_sectors[c])
        load = round(cust_in_crit[c], 2)
        idx = round(secs / load, 3) if load > 0 else 0.0
        if load >= 1.0:  # only customers with material inbound dependency
            diversification.append((c, secs, load, idx))
    diversification.sort(key=lambda r: r[3])  # most brittle (lowest index) first

    # MATURITY — intermediaries (supply-betweenness proxy): nodes that are BOTH a
    # customer and a supplier sit in the chain's middle; rank by in×out (the more
    # paths route through them, the more systemic a single disruption is).
    intermediaries = []
    for n in set(in_deg) & set(out_deg):
        score = len(in_deg[n]) * len(out_deg[n])
        intermediaries.append((n, len(in_deg[n]), len(out_deg[n]), score))
    intermediaries.sort(key=lambda r: -r[3])

    # MATURITY — tier depth: longest DISCLOSED upstream supplier chain reaching a
    # node (depth(node) = 1 + max depth of its suppliers). Cycle-guarded memo;
    # deeper = the disclosed chain has more hops back to raw inputs (more places a
    # disruption can originate). A transparency/resilience signal, never a target.
    depth_memo = {}

    def _depth(node, stack):
        if node in depth_memo:
            return depth_memo[node]
        if node in stack:           # cycle guard — break without counting the loop
            return 0
        sups = in_deg.get(node)
        if not sups:
            depth_memo[node] = 0
            return 0
        stack.add(node)
        d = 1 + max(_depth(s, stack) for s in sups)
        stack.discard(node)
        depth_memo[node] = d
        return d

    tier_depth = sorted(
        ((n, _depth(n, set())) for n in set(in_deg) | set(out_deg)),
        key=lambda r: -r[1])
    tier_depth = [(n, d) for n, d in tier_depth if d > 0]

    # MATURITY — per-commodity HHI (Herfindahl-Hirschman Index): supplier-share
    # concentration within each commodity, by Σ criticality. HHI = Σ(share²) ∈
    # (0,1]; 1.0 = a single disclosed supplier (monopoly), low = fragmented/diverse.
    commodity_supplier_crit = defaultdict(lambda: defaultdict(float))
    for e in edges:
        s = e.get(':supply.edge/from')
        commodity = e.get(':supply.edge/commodity', ':unknown')
        crit = float(e.get(':supply.edge/criticality', 0.0) or 0.0)
        if s and crit > 0:
            commodity_supplier_crit[commodity][s] += crit
    commodity_hhi = []
    for commodity, shares in commodity_supplier_crit.items():
        tot = sum(shares.values())
        if tot <= 0:
            continue
        hhi = sum((v / tot) ** 2 for v in shares.values())
        commodity_hhi.append((commodity, len(shares), round(hhi, 3)))
    commodity_hhi.sort(key=lambda r: -r[2])  # most concentrated first

    # MATURITY — cross-bloc dependency exposure: criticality on edges whose supplier
    # and customer sit in DIFFERENT macro-region blocs = geopolitical supply exposure
    # (the reshoring / friendshoring surface). Aggregated per supplier→customer
    # corridor; routed to diversification + resilience, never to interdiction (G2).
    cross_bloc = defaultdict(float)
    cross_total = 0.0
    all_total = 0.0
    for e in edges:
        s = e.get(':supply.edge/from')
        c = e.get(':supply.edge/to')
        crit = float(e.get(':supply.edge/criticality', 0.0) or 0.0)
        if not s or not c:
            continue
        all_total += crit
        bs = _bloc(companies.get(s, {}).get(':company/country', '??'))
        bc = _bloc(companies.get(c, {}).get(':company/country', '??'))
        if bs != bc:
            cross_bloc[(bs, bc)] += crit
            cross_total += crit
    cross_corridors = sorted(
        ((f"{a}→{b}", v) for (a, b), v in cross_bloc.items()), key=lambda r: -r[1])
    cross_share = round(100 * cross_total / all_total, 1) if all_total else 0.0

    # MATURITY — composite resilience score (capstone synthesis of the signals).
    # Per customer with material inbound dependency, fragility rises with
    # single-source inputs (×2), inbound criticality concentrated in few supplier
    # sectors, and the share of inbound that crosses a region bloc. score =
    # 100/(1+fragility) ∈ (0,100]; LOW = most fragile. Aggregate-first, an
    # accountability/redundancy ranking — never a target-list (G2).
    cust_single_cnt = defaultdict(int)
    for (c, _commodity, _sup, _crit) in single_source:
        cust_single_cnt[c] += 1
    cust_cross_in = defaultdict(float)
    for e in edges:
        s = e.get(':supply.edge/from')
        c = e.get(':supply.edge/to')
        crit = float(e.get(':supply.edge/criticality', 0.0) or 0.0)
        if s and c and _bloc(companies.get(s, {}).get(':company/country', '??')) != \
                _bloc(companies.get(c, {}).get(':company/country', '??')):
            cust_cross_in[c] += crit
    resilience = []
    for c, load in cust_in_crit.items():
        if load < 1.0:
            continue
        secs = max(1, len(cust_supplier_sectors[c]))
        cross_frac = cust_cross_in.get(c, 0.0) / load if load else 0.0
        frag = cust_single_cnt.get(c, 0) * 2 + load / secs + cross_frac
        score = round(100.0 / (1.0 + frag), 1)
        resilience.append((c, score, cust_single_cnt.get(c, 0), len(cust_supplier_sectors[c]),
                           round(load, 2), round(cross_frac, 2)))
    resilience.sort(key=lambda r: r[1])  # most fragile (lowest score) first

    # MATURITY — market-cap concentration (leverages :company/market-cap-busd where
    # publicly known). Σ cap by sector + cap-HHI (Σ sector-share²) across the COVERED
    # caps only, plus the cap-coverage ratio. Honesty (G5): caps are public approx
    # figures `:representative`; only companies carrying a public cap are counted, and
    # cap_coverage states exactly how much of the seed that is. An economic-weight
    # concentration signal (which sectors hold the listed market value), aggregate-first.
    sector_cap = defaultdict(float)
    capped = []
    for cid, co in companies.items():
        mc = co.get(':company/market-cap-busd')
        try:
            mc = float(mc)
        except (TypeError, ValueError):
            continue
        if mc <= 0:
            continue
        capped.append((cid, mc))
        sector_cap[co.get(':company/sector', ':unknown')] += mc
    total_cap = sum(mc for _, mc in capped)
    sector_cap_rank = sorted(sector_cap.items(), key=lambda kv: -kv[1])
    cap_hhi = round(sum((v / total_cap) ** 2 for v in sector_cap.values()), 3) if total_cap else 0.0
    top_caps = sorted(capped, key=lambda r: -r[1])[:12]

    return dict(
        in_deg={k: len(v) for k, v in in_deg.items()},
        out_deg={k: len(v) for k, v in out_deg.items()},
        single_source=single_source,
        sector_concentration=sector_concentration,
        jurisdiction_load=jurisdiction_load,
        systemic=systemic,
        diversification=diversification,
        intermediaries=intermediaries,
        tier_depth=tier_depth,
        bloc_load=bloc_load,
        commodity_hhi=commodity_hhi,
        cross_corridors=cross_corridors,
        cross_share=cross_share,
        resilience=resilience,
        sector_cap_rank=sector_cap_rank,
        cap_hhi=cap_hhi,
        total_cap=round(total_cap, 1),
        cap_count=len(capped),
        cap_coverage=round(100 * len(capped) / len(companies), 1) if companies else 0.0,
        top_caps=top_caps,
    )


def cname(companies, cid):
    return companies.get(cid, {}).get(':company/name', cid)


def render_report(companies, addresses, contacts, edges, processes, a):
    L = []
    P = L.append
    P("# kabuto 兜 — global public-company supply-chain concentration report")
    P("")
    P("> ADR-2606022000 · **aggregate-first** · supply-chain RESILIENCE + corporate-power "
      "TRANSPARENCY map (NOT a target-list; kabuto G2). kabuto does not adjudicate (G4). "
      "All sourcing `:representative` — bounded illustrative seed of public companies + "
      "disclosed supplier relationships, NOT an exhaustive bill of materials.")
    P("")
    status_counts = defaultdict(int)
    for c in companies.values():
        status_counts[c.get(':company/status', ':listed')] += 1
    n_listed = status_counts.get(':listed', 0)
    n_hist = len(companies) - n_listed
    hist_note = (f" (incl. **{n_hist}** delisted/acquired retained as history — Datomic as-of, "
                 "非終末論: facts are superseded, never deleted)") if n_hist else ""
    P(f"- companies: **{len(companies)}**{hist_note}  ·  HQ addresses: **{len(addresses)}**  "
      f"·  public contacts: **{len(contacts)}**  ·  supply edges: **{len(edges)}**  "
      f"·  BPMN process templates: **{len(processes)}**")
    sectors = defaultdict(int)
    for c in companies.values():
        sectors[c.get(':company/sector', ':unknown')] += 1
    P(f"- sectors covered: " + ", ".join(
        f"`{s}` {n}" for s, n in sorted(sectors.items(), key=lambda kv: -kv[1])))
    P("")

    # ── data-coverage self-audit (G5 honesty: what is actually covered) ──
    n = len(companies) or 1
    with_addr = len({a.get(':company.address/company') for a in addresses} & set(companies))
    with_contact = len({c.get(':company.contact/company') for c in contacts} & set(companies))
    in_edges = set()
    for e in edges:
        in_edges.add(e.get(':supply.edge/from'))
        in_edges.add(e.get(':supply.edge/to'))
    with_edge = len(in_edges & set(companies))
    with_cap = sum(1 for c in companies.values() if c.get(':company/market-cap-busd'))
    countries = len({c.get(':company/country') for c in companies.values()})
    exch_count = defaultdict(int)
    for c in companies.values():
        exch_count[c.get(':company/exchange', ':?')] += 1
    n_exch = len(exch_count)
    top_exch = sorted(exch_count.items(), key=lambda kv: -kv[1])[:8]
    P("## Data coverage — G5 honesty self-audit")
    P("")
    P("What the seed ACTUALLY carries (absence = \"not yet ingested\", never \"does not exist\"). "
      "A bounded `:representative` slice, growing each iteration — not exhaustive coverage.")
    P("")
    P("| field | companies | coverage |")
    P("|---|---:|---:|")
    P(f"| registered HQ address | {with_addr} | {round(100*with_addr/n,1)}% |")
    P(f"| public IR contact | {with_contact} | {round(100*with_contact/n,1)}% |")
    P(f"| ≥1 disclosed supply edge | {with_edge} | {round(100*with_edge/n,1)}% |")
    P(f"| market-cap snapshot | {with_cap} | {round(100*with_cap/n,1)}% |")
    P(f"| distinct countries | {countries} | — |")
    P(f"| distinct listing exchanges | {n_exch} | — |")
    P(f"| sector balance (min..max per sector) | {min(sectors.values())}..{max(sectors.values())} | — |")
    P("")
    P("Exchange coverage (top listing venues by company count) — where the seed is "
      "thick vs. where the R1 GLEIF/EDGAR/exchange ingest should still reach:")
    P("")
    P("| exchange | companies |  | exchange | companies |")
    P("|---|---:|---|---|---:|")
    half = (len(top_exch) + 1) // 2
    for i in range(half):
        le, lc = top_exch[i]
        if i + half < len(top_exch):
            re, rc = top_exch[i + half]
            P(f"| `{str(le).lstrip(':')}` | {lc} |  | `{str(re).lstrip(':')}` | {rc} |")
        else:
            P(f"| `{str(le).lstrip(':')}` | {lc} |  | | |")
    P("")

    # ── single-source dependencies (the headline resilience signal) ──
    P("## Single-source dependencies — supply-chain redundancy gaps")
    P("")
    P("A (customer, commodity) met by exactly ONE disclosed supplier at high criticality "
      "(≥0.7). These are where a customer's production shares one supplier's fate — "
      "**routed to diversification, never to interdiction.**")
    P("")
    P("| customer | commodity | sole disclosed supplier | criticality |")
    P("|---|---|---|---:|")
    for c, commodity, sup, crit in a['single_source']:
        P(f"| {cname(companies, c)} | `{commodity}` | {cname(companies, sup)} | {crit} |")
    if not a['single_source']:
        P("| (none in seed) | | | |")
    P("")

    # ── jurisdiction concentration ──
    P("## Jurisdiction concentration — geographic supply load")
    P("")
    P("Σ disclosed-dependency criticality whose SUPPLIER domiciles in each country. "
      "Higher = more of the seeded supply chain shares one geographic/regulatory fate.")
    P("")
    P("| supplier domicile | Σ criticality |")
    P("|---|---:|")
    for country, load in sorted(a['jurisdiction_load'].items(), key=lambda kv: -kv[1]):
        P(f"| `{country}` | {round(load, 2)} |")
    P("")

    # ── regional-bloc concentration (maturity) ──
    P("## Regional-bloc concentration — supply load by macro-region")
    P("")
    P("Σ disclosed-dependency criticality grouped by the SUPPLIER's macro-region "
      "bloc. Surfaces which world region the seeded supply chain leans on most — "
      "routed to cross-region diversification, never to interdiction (G2).")
    P("")
    total_bloc = sum(a['bloc_load'].values()) or 1.0
    P("| region bloc | Σ criticality | share |")
    P("|---|---:|---:|")
    for bloc, load in sorted(a['bloc_load'].items(), key=lambda kv: -kv[1]):
        P(f"| {bloc} | {round(load, 2)} | {round(100 * load / total_bloc, 1)}% |")
    P("")

    # ── sector × commodity concentration ──
    # ── per-commodity HHI (maturity) ──
    P("## Commodity supplier concentration — Herfindahl index (HHI)")
    P("")
    P("Supplier-share concentration WITHIN each commodity, by Σ criticality "
      "(HHI = Σ share²; 1.0 = a single disclosed supplier, low = fragmented). "
      "High HHI = the world depends on few suppliers for that input — the headline "
      "redundancy priority, routed to diversification (G2).")
    P("")
    P("| commodity | disclosed suppliers | HHI |")
    P("|---|---:|---:|")
    for commodity, nsup, hhi in a['commodity_hhi']:
        P(f"| `{str(commodity).lstrip(':')}` | {nsup} | {hhi} |")
    P("")

    P("## Sector × commodity concentration")
    P("")
    P("| supplier sector | commodity | Σ criticality |")
    P("|---|---|---:|")
    for (sec, commodity), load in sorted(
            a['sector_concentration'].items(), key=lambda kv: -kv[1])[:15]:
        P(f"| `{sec}` | `{commodity}` | {round(load, 2)} |")
    P("")

    # ── systemic suppliers ──
    P("## Most systemic suppliers — outward dependency weight")
    P("")
    P("Suppliers carrying the most criticality-weighted outward dependency across the "
      "seeded graph. High = many customers concentrate on them (a transparency signal: "
      "where corporate supply power concentrates).")
    P("")
    P("| supplier | sector | customers | Σ outward criticality |")
    P("|---|---|---:|---:|")
    for sup, load in sorted(a['systemic'].items(), key=lambda kv: -kv[1])[:15]:
        sec = companies.get(sup, {}).get(':company/sector', '?')
        P(f"| {cname(companies, sup)} | `{sec}` | {a['out_deg'].get(sup, 0)} | {round(load, 2)} |")
    P("")

    # ── customer diversification (maturity) ──
    P("## Least-diversified customers — supplier-sector concentration")
    P("")
    P("Customers whose inbound dependency draws on the FEWEST distinct supplier "
      "sectors per unit of criticality (index = distinct-sectors ÷ Σ inbound "
      "criticality). Lower = more brittle; candidates for cross-sector diversification.")
    P("")
    P("| customer | supplier sectors | Σ inbound criticality | diversification index |")
    P("|---|---:|---:|---:|")
    for c, secs, load, idx in a['diversification'][:12]:
        P(f"| {cname(companies, c)} | {secs} | {load} | {idx} |")
    if not a['diversification']:
        P("| (none in seed) | | | |")
    P("")

    # ── intermediaries / supply-betweenness (maturity) ──
    P("## Supply-chain intermediaries — betweenness (in × out)")
    P("")
    P("Nodes that are BOTH a customer and a supplier sit in the chain's middle. "
      "Ranked by in×out: the more paths route through them, the more systemic a "
      "single disruption — a transparency signal, never a target (G2).")
    P("")
    P("| node | suppliers (in) | customers (out) | betweenness |")
    P("|---|---:|---:|---:|")
    for n, ind, outd, score in a['intermediaries'][:12]:
        P(f"| {cname(companies, n)} | {ind} | {outd} | {score} |")
    if not a['intermediaries']:
        P("| (none in seed) | | | |")
    P("")

    # ── tier depth (maturity) ──
    P("## Deepest disclosed supply chains — tier depth")
    P("")
    P("Longest DISCLOSED upstream chain of suppliers-of-suppliers reaching each node "
      "(depth = hops back toward raw inputs). Deeper = more upstream stages where a "
      "disruption can originate; routed to multi-tier visibility, never to a target.")
    P("")
    P("| node | tier depth |")
    P("|---|---:|")
    for n, d in a['tier_depth'][:12]:
        P(f"| {cname(companies, n)} | {d} |")
    if not a['tier_depth']:
        P("| (none in seed) | |")
    P("")

    # ── cross-bloc dependency exposure (maturity) ──
    P("## Cross-bloc dependency exposure — geopolitical supply corridors")
    P("")
    P(f"**{a['cross_share']}%** of disclosed-dependency criticality flows across a "
      "macro-region bloc boundary (supplier and customer in different blocs) — the "
      "geopolitical exposure / reshoring surface. Top corridors below; routed to "
      "supply diversification + resilience, never to interdiction (G2).")
    P("")
    P("| corridor (supplier bloc → customer bloc) | Σ criticality |")
    P("|---|---:|")
    for corridor, load in a['cross_corridors'][:12]:
        P(f"| {corridor} | {round(load, 2)} |")
    if not a['cross_corridors']:
        P("| (none in seed) | |")
    P("")

    # ── market-cap concentration (maturity) ──
    if a.get('cap_count'):
        P("## Market-cap concentration — listed economic weight by sector")
        P("")
        P(f"Across the **{a['cap_count']}** seed companies carrying a publicly-known market cap "
          f"(**{a['cap_coverage']}%** of the seed; Σ ≈ **${a['total_cap']:,.0f}B** `:representative`), "
          f"the sector **cap-HHI = {a['cap_hhi']}** (Σ sector-share²; higher = listed value piled into "
          "fewer sectors). An economic-weight concentration signal complementing the criticality view — "
          "which sectors hold the market value, aggregate-first, never a target-list (G2). Honesty (G5): "
          "covers only companies with a public cap; absence ≠ zero value.")
        P("")
        P("| sector | Σ market cap (USD B) | share of covered cap |")
        P("|---|---:|---:|")
        for sec, cap in a['sector_cap_rank'][:12]:
            sh = round(100 * cap / a['total_cap'], 1) if a['total_cap'] else 0.0
            P(f"| {str(sec).lstrip(':')} | {cap:,.0f} | {sh}% |")
        P("")
        P("Largest covered caps (orientation only, not a ranking of importance):")
        P("")
        P("| company | market cap (USD B) |")
        P("|---|---:|")
        for cid, cap in a['top_caps']:
            P(f"| {cname(companies, cid)} | {cap:,.0f} |")
        P("")

    # ── composite resilience score (maturity capstone) ──
    P("## Composite supply-resilience score — most-fragile customers")
    P("")
    P("Capstone synthesis: score = 100/(1+fragility), where fragility rises with "
      "single-source inputs (×2), inbound criticality concentrated in few supplier "
      "sectors, and cross-bloc inbound share. **Lower = more fragile.** Aggregate-first "
      "accountability/redundancy ranking — never a target-list (G2).")
    P("")
    P("| customer | resilience score | single-source | supplier sectors | inbound crit | cross-bloc share |")
    P("|---|---:|---:|---:|---:|---:|")
    for c, score, ss, secs, load, cross in a['resilience'][:12]:
        P(f"| {cname(companies, c)} | {score} | {ss} | {secs} | {load} | {cross} |")
    if not a['resilience']:
        P("| (none in seed) | | | | | |")
    P("")

    P("---")
    P("*Generated by `kabuto/methods/analyze.py`. HONEST: R0 bounded seed of public "
      "companies; supplier edges are disclosed/public `:representative` estimates, NOT an "
      "exhaustive bill of materials; criticality is a bounded estimate, never a contract "
      "figure. Full GLEIF/EDGAR/exchange-universe ingest is G7 Council + operator gated.*")
    return "\n".join(L) + "\n"


def render_datoms(companies, a):
    L = []
    P = L.append
    P(";; kabuto — DERIVED supply-chain concentration datoms (ADR-2606022000). :derived — NOT fact.")
    P(";; Recomputed from the seed graph; do not re-ingest as :authoritative.")
    P("[")
    for c, commodity, sup, crit in a['single_source']:
        P(f' {{:supply/single-source-customer {edn_str(c)} :supply/commodity "{commodity}" '
          f':supply/sole-supplier {edn_str(sup)} :supply/criticality {crit} :supply/derived true}}')
    for country, load in sorted(a['jurisdiction_load'].items(), key=lambda kv: -kv[1]):
        P(f' {{:supply/jurisdiction "{country}" :supply/jurisdiction-load {round(load, 2)} '
          f':supply/derived true}}')
    for sup, load in sorted(a['systemic'].items(), key=lambda kv: -kv[1]):
        P(f' {{:supply/systemic-supplier {edn_str(sup)} '
          f':supply/out-degree {a["out_deg"].get(sup, 0)} '
          f':supply/outward-criticality {round(load, 2)} :supply/derived true}}')
    for c, secs, load, idx in a['diversification']:
        P(f' {{:supply/diversification-customer {edn_str(c)} '
          f':supply/supplier-sectors {secs} :supply/inbound-criticality {load} '
          f':supply/diversification-index {idx} :supply/derived true}}')
    for n, ind, outd, score in a['intermediaries']:
        P(f' {{:supply/intermediary {edn_str(n)} :supply/in-degree {ind} '
          f':supply/out-degree {outd} :supply/betweenness {score} :supply/derived true}}')
    for n, d in a['tier_depth']:
        P(f' {{:supply/tier-depth-node {edn_str(n)} :supply/tier-depth {d} :supply/derived true}}')
    for bloc, load in sorted(a['bloc_load'].items(), key=lambda kv: -kv[1]):
        P(f' {{:supply/region-bloc "{bloc}" :supply/bloc-load {round(load, 2)} :supply/derived true}}')
    for commodity, nsup, hhi in a['commodity_hhi']:
        P(f' {{:supply/commodity "{str(commodity).lstrip(":")}" '
          f':supply/commodity-suppliers {nsup} :supply/commodity-hhi {hhi} :supply/derived true}}')
    for corridor, load in a['cross_corridors']:
        P(f' {{:supply/cross-bloc-corridor "{corridor}" :supply/cross-bloc-load {round(load, 2)} '
          f':supply/derived true}}')
    for c, score, ss, secs, load, cross in a['resilience']:
        P(f' {{:supply/resilience-customer {edn_str(c)} :supply/resilience-score {score} '
          f':supply/single-source-count {ss} :supply/derived true}}')
    for sec, cap in a.get('sector_cap_rank', []):
        P(f' {{:supply/cap-sector "{str(sec).lstrip(":")}" :supply/cap-sector-busd {round(cap, 1)} '
          f':supply/derived true}}')
    if a.get('cap_count'):
        P(f' {{:supply/cap-hhi {a["cap_hhi"]} :supply/cap-total-busd {a["total_cap"]} '
          f':supply/cap-covered {a["cap_count"]} :supply/cap-coverage-pct {a["cap_coverage"]} '
          f':supply/derived true}}')
    P("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-public-companies.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    companies, addresses, contacts, edges, processes = classify(rows)
    a = analyze(companies, edges)

    (outdir / "intel-report.md").write_text(
        render_report(companies, addresses, contacts, edges, processes, a), encoding='utf-8')
    (outdir / "supply-criticality.kotoba.edn").write_text(
        render_datoms(companies, a), encoding='utf-8')

    print(f"kabuto: {len(companies)} companies, {len(edges)} supply edges, "
          f"{len(addresses)} HQ addresses, {len(processes)} processes")
    print(f"single-source dependencies (≥0.7): {len(a['single_source'])}")
    top = sorted(a['jurisdiction_load'].items(), key=lambda kv: -kv[1])[:3]
    print("top supplier jurisdictions: " +
          ", ".join(f"{c} {round(v, 2)}" for c, v in top))
    print(f"wrote {outdir/'intel-report.md'} + {outdir/'supply-criticality.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
