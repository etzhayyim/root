#!/usr/bin/env python3
"""uchiwake 内訳 — product / GTIN / BOM ingestion bridge (offline default; live G7-gated).

ADR-2606081800. Bridges public product-data sources into the kotoba Datom log as
:product/:part/:material/:bom.edge/:process.step/:logistics.leg/:design.ref/
:company.ownership datoms, dedup-merged with the bounded real seed (seed wins on id).

WORLDWIDE-COVERAGE ARCHITECTURE (the design target — full ingest is G7 Council +
operator gated; R0 ships the bounded seed only):

  product identity (GTIN)   ← GS1 GDSN (Global Data Synchronisation Network) +
                              GS1 Verified by GS1 + GS1 company-prefix registry;
                              open mirrors: Open Food Facts / Open Beauty Facts /
                              Open Products Facts (CC-licensed, real GTIN + labels).
                              ~hundreds of millions of GTINs worldwide.
  classification            ← GS1 GPC brick + UNSPSC (the existing 18,342-code space,
                              entity-as-actor ADR-2606042330) + HS code (WCO).
  brand-owner → company     ← GS1 prefix licensee → GLEIF LEI (kabuto org.corp.* space).
  subsidiary → parent (子会社) ← GLEIF Level-2 Relationship Records (RR):
                              :is-directly/ultimately-consolidated-by. This is the edge
                              that rolls a brand-owning subsidiary up to its true parent.
  BOM / materials           ← public teardowns (iFixit-style), ingredient labels
                              (Open Food Facts), supplier-list filings, EPDs /
                              digital product passports (EU ESPR DPP, emerging).
  process / logistics       ← public origin declarations, customs HS flows
                              (UN Comtrade), disclosed factory lists (e.g. apparel
                              transparency pledges). :representative, never contract data.
  design / standards        ← cited safety/material/interface standards (IEC/ISO/JEDEC/
                              USB-IF) and public regulatory monographs (USP/Ph.Eur.).

GATES enforced here:
  G1  public trade items + public-record data only; no confidential recipes/terms.
  G5  every emitted datom carries :*/sourcing; bridged data defaults :representative.
  G7  live full-universe fetch requires UCHIWAKE_OPERATOR_GATE=1 (Council + operator).
      Default is OFFLINE: bridge data/ingest/*.json if present, else just the seed.
  no-server-key: read-only. uchiwake never holds a GS1/GLEIF write credential.

stdlib only. Usage:
    python3 ingest.py                 # offline: merge data/ingest/*.json (if any) + seed
    UCHIWAKE_OPERATOR_GATE=1 python3 ingest.py --live   # G7 (refuses unless gated)
"""
from __future__ import annotations
import sys
import os
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uchiwake_edn import load_edn, classify, normalize_gtin, gtin_check_digit_ok  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SEED = ROOT / "data" / "seed-products.kotoba.edn"
INGEST_DIR = ROOT / "data" / "ingest"
MERGED = ROOT / "data" / "products.merged.kotoba.edn"


def _seed_ids(rows):
    ids = set()
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in (':product/id', ':part/id', ':material/id', ':bom.edge/id',
                  ':process.step/id', ':logistics.leg/id', ':design.ref/id',
                  ':company.ownership/id'):
            if k in r:
                ids.add(r[k])
    return ids


def bridge_offline():
    """Merge any data/ingest/*.json bridged datoms with the seed (seed wins on id)."""
    seed_rows = load_edn(SEED)
    seed_ids = _seed_ids(seed_rows)
    bridged = []
    if INGEST_DIR.is_dir():
        for f in sorted(INGEST_DIR.glob("*.json")):
            doc = json.loads(f.read_text(encoding='utf-8'))
            for r in (doc if isinstance(doc, list) else doc.get('datoms', [])):
                # validate GTIN check digit before admitting a product datom (G5 honesty)
                if ':product/gtin' in r and not gtin_check_digit_ok(r[':product/gtin']):
                    print(f"  ! skip {r.get(':product/id')} — bad GTIN check digit", file=sys.stderr)
                    continue
                rid = next((r[k] for k in (':product/id', ':part/id', ':material/id',
                                           ':bom.edge/id', ':process.step/id',
                                           ':logistics.leg/id', ':design.ref/id',
                                           ':company.ownership/id') if k in r), None)
                if rid and rid in seed_ids:
                    continue  # seed wins
                r.setdefault(':product/sourcing', ':representative') if ':product/id' in r else None
                bridged.append(r)
    return seed_rows, bridged


def main(argv):
    live = '--live' in argv
    if live and os.environ.get('UCHIWAKE_OPERATOR_GATE') != '1':
        print("REFUSED (G7): live full-universe GS1/GLEIF ingest requires "
              "UCHIWAKE_OPERATOR_GATE=1 + Council authorization. Running offline instead.",
              file=sys.stderr)
        live = False
    if live:
        print("G7 gate satisfied — live ingest would run here (GS1 GDSN / GLEIF RR / "
              "Open Product Data). Not wired in R0; falling back to offline bridge.", file=sys.stderr)

    seed_rows, bridged = bridge_offline()
    g = classify(seed_rows)
    print(f"seed: {len(g['products'])} products, {len(g['parts'])} parts, "
          f"{len(g['materials'])} materials, {len(g['bom'])} BOM edges, "
          f"{len(g['ownership'])} ownership edges")
    print(f"bridged (offline data/ingest/*.json): {len(bridged)} new datoms")
    # R0: merged == seed (no external ingest files committed). Write for downstream parity.
    if bridged:
        text = SEED.read_text(encoding='utf-8')
        # naive append is unsafe for EDN vectors; R0 keeps merged == seed unless bridged.
        print("(merged write deferred — bridged datoms present; wire EDN re-emit in a later iteration)")
    else:
        MERGED.write_text(SEED.read_text(encoding='utf-8'), encoding='utf-8')
        print(f"→ {MERGED} (== seed; no external ingest in R0)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
