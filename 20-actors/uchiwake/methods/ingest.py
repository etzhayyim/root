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
    UCHIWAKE_OPERATOR_GATE=1 python3 ingest.py --live --gtin 3017620422003   # G7: live OFF fetch
    UCHIWAKE_OPERATOR_GATE=1 python3 ingest.py --live                        # G7 (no GTIN → offline)
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
            # Open Food Facts files are in OFF record shape, not datom shape:
            # route them through the dedicated normalizer adapter (GTIN-validated).
            if f.name.startswith("openfoodfacts"):
                sys.path.insert(0, str(HERE / "adapters"))
                import openfoodfacts as _off  # noqa: E402
                recs = json.loads(f.read_text(encoding='utf-8'))
                if isinstance(recs, dict):
                    recs = recs.get("products", [])
                off_datoms, off_stats = _off.normalize_dataset(recs)
                print(f"  OFF adapter {f.name}: {off_stats['products_ok']} products, "
                      f"{off_stats['materials']} materials, {off_stats['skipped_bad_gtin']} skipped",
                      file=sys.stderr)
                for r in off_datoms:
                    rid = r.get(':product/id') or r.get(':material/id') or r.get(':bom.edge/id')
                    if rid and rid in seed_ids:
                        continue  # seed wins
                    bridged.append(r)
                continue
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


# ── live OFF fetch leg (G7-gated, single polite request per explicit GTIN) ────
OFF_API = "https://world.openfoodfacts.org/api/v2/product/{gtin}.json"
OFF_FIELDS = "code,product_name,brands,countries_tags,ingredients"
OFF_UA = "etzhayyim-uchiwake research (jun@etzhayyim.group)"
LIVE_FILE = INGEST_DIR / "openfoodfacts.live.json"


def fetch_off(gtin: str) -> dict:
    """LIVE Open Food Facts product fetch — G7-gated, single polite request.

    Mirrors kanjō's `--fetch-edgar CIK` discipline: an EXPLICIT GTIN is required (never an
    auto-discovery scrape loop), the GS1 mod-10 check digit is validated BEFORE any network
    call (G5), and the only gate is `UCHIWAKE_OPERATOR_GATE=1` (Council + operator). OFF is
    CC-BY-SA crowd-sourced, so the resulting datoms stay :representative (G5). Read-only — no
    GS1/GLEIF/OFF write credential is ever held (G12).
    """
    if os.environ.get('UCHIWAKE_OPERATOR_GATE') != '1':
        sys.exit("REFUSED (G7): live OFF fetch requires UCHIWAKE_OPERATOR_GATE=1 + Council. "
                 "Offline mode bridges data/ingest/*.json.")
    digits = ''.join(c for c in str(gtin) if c.isdigit())
    if not gtin_check_digit_ok(digits):
        sys.exit(f"REFUSED (G5): {gtin} fails the GS1 mod-10 check digit; not a valid GTIN.")
    import urllib.request  # imported inside the gated path — autorun/kotoba stay I/O-free (G7)
    url = OFF_API.format(gtin=digits) + "?fields=" + OFF_FIELDS
    req = urllib.request.Request(url, headers={"User-Agent": OFF_UA})
    with urllib.request.urlopen(req, timeout=30) as r:        # noqa: S310 (https, validated host)
        obj = json.load(r)
    if obj.get("status") != 1 or not isinstance(obj.get("product"), dict):
        sys.exit(f"OFF has no product record for GTIN {digits}.")
    prod = obj["product"]
    prod.setdefault("code", digits)
    return prod


def _save_live_record(prod: dict) -> int:
    """Append one fetched OFF record into data/ingest/openfoodfacts.live.json (dedup by code),
    so the existing offline bridge normalizes + GTIN-validates + merges it (seed wins). Returns
    the number of records now in the live file."""
    INGEST_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    if LIVE_FILE.exists():
        doc = json.loads(LIVE_FILE.read_text(encoding='utf-8'))
        existing = doc.get("products", doc) if isinstance(doc, dict) else doc
    by_code = {str(r.get("code")): r for r in existing if isinstance(r, dict)}
    by_code[str(prod.get("code"))] = prod
    records = list(by_code.values())
    LIVE_FILE.write_text(json.dumps({"products": records}, ensure_ascii=False, indent=1),
                         encoding='utf-8')
    return len(records)


def main(argv):
    live = '--live' in argv
    gtin = None
    if '--gtin' in argv:
        gtin = argv[argv.index('--gtin') + 1]
    if live and os.environ.get('UCHIWAKE_OPERATOR_GATE') != '1':
        print("REFUSED (G7): live GS1/GLEIF/OFF ingest requires UCHIWAKE_OPERATOR_GATE=1 + "
              "Council authorization. Running offline instead.", file=sys.stderr)
        live = False
    if live and gtin:
        # WIRED: a single polite OFF fetch for one explicit GTIN, then normalize+merge offline.
        prod = fetch_off(gtin)
        n = _save_live_record(prod)
        print(f"G7 gate satisfied — fetched OFF GTIN {gtin}: "
              f"\"{prod.get('product_name') or '(unnamed)'}\" "
              f"→ {LIVE_FILE.name} ({n} live record{'s' if n != 1 else ''})", file=sys.stderr)
    elif live:
        print("G7 gate satisfied, but no --gtin given. The full GS1 GDSN / GLEIF RR universe "
              "fetch is Council-scoped; the wired live leg fetches ONE explicit --gtin from "
              "Open Food Facts. Falling back to the offline bridge.", file=sys.stderr)

    seed_rows, bridged = bridge_offline()
    g = classify(seed_rows)
    print(f"seed: {len(g['products'])} products, {len(g['parts'])} parts, "
          f"{len(g['materials'])} materials, {len(g['bom'])} BOM edges, "
          f"{len(g['ownership'])} ownership edges")
    print(f"bridged (offline data/ingest/*.json): {len(bridged)} new datoms")
    # Splice bridged datoms into the merged EDN by inserting them before the seed
    # vector's closing ']' — preserves the seed text/comments verbatim (seed wins on id).
    text = SEED.read_text(encoding='utf-8')
    if bridged:
        block = _emit_bridged_edn(bridged)
        cut = text.rstrip().rfind(']')
        merged = text[:cut] + "\n" + block + "\n]\n"
        MERGED.write_text(merged, encoding='utf-8')
        print(f"→ {MERGED} (seed + {len(bridged)} bridged datoms)")
    else:
        MERGED.write_text(text, encoding='utf-8')
        print(f"→ {MERGED} (== seed; no external ingest)")
    return 0


def _emit_bridged_edn(datoms):
    """Serialize bridged datom dicts to EDN map literals (one per line)."""
    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return v if v.startswith(':') else ('"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"')
        return v
    lines = [" ;; ── bridged datoms (offline adapters; :representative, G5) ──"]
    for d in datoms:
        lines.append(" {" + " ".join(f"{k} {val(v)}" for k, v in d.items()) + "}")
    return "\n".join(lines)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
