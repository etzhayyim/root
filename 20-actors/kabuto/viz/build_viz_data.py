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


def _edn_scalar(v):
    """Encode a Python value as an EDN scalar string for a kotoba Datom `v_edn`.

    Mirrors the `[{e,a,v_edn}]` contract that `KotobaNode.loadDatoms` ingests:
      str starting with ':' → bare EDN keyword (`:semiconductors`)
      other str            → EDN string literal (`"TSMC"`)
      int/float            → bare number
    Returns None for values that should not produce a Datom (None / "").
    """
    if v is None:
        return None
    if isinstance(v, bool):  # guard: bool is an int subclass
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    if s == "":
        return None
    if s.startswith(":"):
        return s  # already an EDN keyword
    return json.dumps(s, ensure_ascii=False)  # EDN string literal


def build_datoms(payload):
    """Flatten the viz payload into the `[{e,a,v_edn}]` Datom array that the
    in-browser kotoba-wasm node hydrates via `loadDatoms` (ADR-2606013600).

    This is the SAME data the static render uses, expressed as the kotoba Datom
    contract so the viewer can drive the graph through `KotobaNode.datomicQ`
    (loadDatoms → q) with zero server round-trip. Company id + flattened
    address/contact ride on the company entity; each supply edge is its own
    entity keyed `<from>>><to>`.
    """
    datoms = []

    def add(e, a, v):
        s = _edn_scalar(v)
        if s is not None:
            datoms.append({"e": e, "a": a, "v_edn": s, "added": True})

    for c in payload["companies"]:
        e = c["id"]
        add(e, ":company/id", c["id"])
        add(e, ":company/name", c.get("name"))
        add(e, ":company/ticker", c.get("ticker"))
        add(e, ":company/sector", c.get("sector"))
        add(e, ":company/country", c.get("country"))
        add(e, ":company/out", int(c.get("out", 0) or 0))
        a = c.get("address") or {}
        add(e, ":company.address/street", a.get("street"))
        add(e, ":company.address/city", a.get("city"))
        add(e, ":company.address/country", a.get("country"))
        add(e, ":company.address/lat", a.get("lat"))
        add(e, ":company.address/lon", a.get("lon"))
        ct = c.get("contact") or {}
        add(e, ":company.contact/website", ct.get("website"))
        add(e, ":company.contact/ir", ct.get("ir"))

    for ed in payload["edges"]:
        if not ed.get("from") or not ed.get("to"):
            continue
        e = f"supply.edge:{ed['from']}>>>{ed['to']}"
        add(e, ":supply.edge/from", ed["from"])
        add(e, ":supply.edge/to", ed["to"])
        add(e, ":supply.edge/commodity", ":" + str(ed.get("commodity", "unknown")))
        add(e, ":supply.edge/criticality", float(ed.get("criticality", 0) or 0))

    return datoms


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    root = here.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else root / "data" / "seed-public-companies.kotoba.edn"

    rows = load_edn(seed)
    companies, addresses, contacts, edges, _proc = classify(rows)
    payload = build_payload(companies, addresses, contacts, edges)
    datoms = build_datoms(payload)

    (here / "supply-chain.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # The kotoba Datom contract the in-browser kotoba-wasm node hydrates.
    (here / "supply-datoms.json").write_text(
        json.dumps(datoms, ensure_ascii=False) + "\n", encoding="utf-8")

    template = (here / "_template.htm").read_text(encoding="utf-8")
    html = (template
            .replace("__KABUTO_DATA__", json.dumps(payload, ensure_ascii=False))
            .replace("__KABUTO_DATOMS__", json.dumps(datoms, ensure_ascii=False)))
    (here / "supply-chain.htm").write_text(html, encoding="utf-8")

    print(f"kabuto.viz: {len(companies)} companies, {len(edges)} edges, "
          f"{len(datoms)} datoms → {here/'supply-chain.json'} + "
          f"{here/'supply-datoms.json'} + {here/'supply-chain.htm'}")


if __name__ == "__main__":
    main(sys.argv)
