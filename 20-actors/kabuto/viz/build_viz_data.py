#!/usr/bin/env python3
"""kabuto 兜 — supply-chain visualization payload + self-contained viewer.

ADR-2606022000. Reads the company graph, computes the same aggregate-first
concentration signals as analyze.py, and emits:

  1. viz/supply-chain.json   — the viz payload (the data CONTRACT the in-browser
     kotoba-wasm node / kami-engine consumes; browser-native, ADR-2606013600).
  2. viz/supply-chain.htm    — a SELF-CONTAINED viewer (data inlined into
     viz/_template.htm; opens via file://, no external fetch).

A redundancy / accountability surface, NEVER a target-list (kabuto G2).

stdlib only. Usage:
    python3 viz/build_viz_data.py [seed.edn]
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "methods"))
from kabuto_edn import load_edn, classify  # noqa: E402


def build_payload(companies, addresses, contacts, edges):
    addr_by = {a[':company.address/company']: a for a in addresses}
    contact_by = {c[':company.contact/company']: c for c in contacts}

    out_deg = defaultdict(int)
    jur = defaultdict(float)
    for e in edges:
        s = e.get(':supply.edge/from')
        out_deg[s] += 1
        jur[companies.get(s, {}).get(':company/country', '??')] += \
            float(e.get(':supply.edge/criticality', 0) or 0)

    def addr_obj(cid):
        a = addr_by.get(cid)
        if not a:
            return None
        return {"street": a.get(':company.address/street'),
                "city": a.get(':company.address/city'),
                "country": a.get(':company.address/country'),
                "lat": a.get(':company.address/lat'),
                "lon": a.get(':company.address/lon')}

    def contact_obj(cid):
        c = contact_by.get(cid)
        if not c:
            return None
        return {"website": c.get(':company.contact/website'),
                "ir": c.get(':company.contact/ir-url')}

    node_list = []
    for cid, c in companies.items():
        node_list.append({
            "id": cid,
            "name": c.get(':company/name', cid),
            "ticker": c.get(':company/ticker'),
            "sector": c.get(':company/sector'),
            "country": c.get(':company/country'),
            "out": out_deg.get(cid, 0),
            "address": addr_obj(cid),
            "contact": contact_obj(cid),
        })
    edge_list = [{
        "from": e.get(':supply.edge/from'),
        "to": e.get(':supply.edge/to'),
        "commodity": str(e.get(':supply.edge/commodity', ':unknown')).lstrip(':'),
        "criticality": e.get(':supply.edge/criticality', 0),
    } for e in edges]
    jurisdictions = [{"country": k, "load": round(v, 2)}
                     for k, v in sorted(jur.items(), key=lambda kv: -kv[1])]

    return {
        "actor": "kabuto",
        "glyph": "兜",
        "adr": "2606022000",
        "note": "aggregate-first supply-chain resilience + transparency map; NOT a target-list (G2). sourcing :representative.",
        "companies": node_list,
        "edges": edge_list,
        "jurisdictions": jurisdictions,
    }


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    root = here.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else root / "data" / "seed-public-companies.kotoba.edn"

    rows = load_edn(seed)
    companies, addresses, contacts, edges, _proc = classify(rows)
    payload = build_payload(companies, addresses, contacts, edges)

    (here / "supply-chain.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    template = (here / "_template.htm").read_text(encoding="utf-8")
    html = template.replace("__KABUTO_DATA__", json.dumps(payload, ensure_ascii=False))
    (here / "supply-chain.htm").write_text(html, encoding="utf-8")

    print(f"kabuto.viz: {len(companies)} companies, {len(edges)} edges → "
          f"{here/'supply-chain.json'} + {here/'supply-chain.htm'}")


if __name__ == "__main__":
    main(sys.argv)
