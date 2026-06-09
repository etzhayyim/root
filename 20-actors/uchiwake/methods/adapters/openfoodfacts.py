#!/usr/bin/env python3
"""uchiwake 内訳 — Open Food Facts → kotoba datom normalizer (stdlib only). ADR-2606081800.

The first concrete BULK-INGEST adapter: turns Open Food Facts product records (a
CC-BY-SA open dataset of ~3M+ real food/beverage trade items, each with a real GTIN
barcode + brand + ingredient list) into uchiwake :product / :material / :bom.edge
datoms. This is the normalizer that makes the worldwide-coverage path actually run;
the LIVE network fetch of the full OFF dump stays G7 / operator gated (this module
operates on a LOCAL file or fixture and is import-safe).

OFF record shape (subset we read):
    { "code": "3017620422003",            # the GTIN barcode (any length)
      "product_name": "Nutella",
      "brands": "Ferrero",
      "countries_tags": ["en:france"],
      "ingredients": [ {"id":"en:sugar","text":"Sugar","percent_estimate":56.0}, ... ] }

HONESTY (G5): OFF is crowd-sourced, so every emitted datom is :sourcing :representative
(never :authoritative). The GTIN is validated against the GS1 mod-10 check digit; a record
with a bad/missing check digit is SKIPPED, not admitted. Ingredient percentages become
bounded :bom.edge/qty "%mass" estimates, never a manufacturer's confidential recipe.

stdlib only. Usage:
    python3 openfoodfacts.py [off-records.json] [--out merged.edn]
    # default input: ../../data/ingest/openfoodfacts.sample.json
"""
from __future__ import annotations
import sys
import os
import re
import json
import pathlib

# import the shared GTIN helpers from the sibling methods dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from uchiwake_edn import normalize_gtin, gtin_check_digit_ok, edn_str  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ACTOR = HERE.parent.parent
DEFAULT_IN = ACTOR / "data" / "ingest" / "openfoodfacts.sample.json"

# OFF ingredient id (en:sugar) / free text → canonical uchiwake material id.
# Conservative map; unknown ingredients fall through to a slugified mat.<id> (still honest).
_MAT_ALIAS = {
    "en:sugar": "mat.sugar", "en:sucrose": "mat.sugar",
    "en:water": "mat.water",
    "en:cocoa": "mat.cocoa", "en:cocoa-butter": "mat.cocoa", "en:fat-reduced-cocoa": "mat.cocoa",
    "en:hazelnut": "mat.hazelnut", "en:hazelnuts": "mat.hazelnut",
    "en:palm-oil": "mat.palm-oil", "en:palm-fat": "mat.palm-oil",
    "en:skimmed-milk-powder": "mat.milk-powder", "en:milk": "mat.milk-powder",
    "en:carbon-dioxide": "mat.co2",
}
_MAT_NAME = {  # display names for the canonical material ids above (used when freshly created)
    "mat.sugar": "Sugar (sucrose)", "mat.water": "Water", "mat.cocoa": "Cocoa",
    "mat.hazelnut": "Hazelnut", "mat.palm-oil": "Palm oil", "mat.milk-powder": "Skim milk powder",
    "mat.co2": "Carbon dioxide (food grade)",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower().split(":")[-1]).strip("-") or "unknown"


def _country_from_tags(tags):
    """First countries_tag → ISO alpha-2 (best-effort; en:france→FR style is name-based, skip)."""
    if not tags:
        return None
    # OFF tags are names not ISO codes; we don't fabricate an ISO mapping (honesty) — return None.
    return None


def material_for(ingredient):
    """Return (material_id, material_datom_or_None) for an OFF ingredient dict."""
    iid = ingredient.get("id") or ""
    if iid in _MAT_ALIAS:
        mid = _MAT_ALIAS[iid]
        name = _MAT_NAME.get(mid, ingredient.get("text") or mid)
    else:
        mid = "mat." + _slug(iid or ingredient.get("text") or "unknown")
        name = ingredient.get("text") or _slug(iid)
    return mid, {":material/id": mid, ":material/name": name,
                 ":material/kind": ":agricultural", ":material/sourcing": ":representative"}


def normalize_record(rec):
    """One OFF record → list of datom dicts, or [] if the GTIN is invalid (skipped)."""
    raw = str(rec.get("code") or "").strip()
    if not raw or not gtin_check_digit_ok(raw):
        return []
    gtin14 = normalize_gtin(raw)
    pid = f"gtin.{gtin14}"
    digits = "".join(c for c in raw if c.isdigit())
    fmt = {8: ":gtin-8", 12: ":gtin-12", 13: ":gtin-13", 14: ":gtin-14"}.get(len(digits), ":gtin-13")
    brand = (rec.get("brands") or "").split(",")[0].strip()

    datoms = [{
        ":product/id": pid, ":product/gtin": gtin14, ":product/gtin-format": fmt,
        ":product/name": rec.get("product_name") or pid,
        ":product/brand": brand or "(unknown)",
        ":product/gs1-prefix": digits[:3],
        ":product/sector": ":food-beverage", ":product/sourcing": ":representative",
    }]
    seen_mat = set()
    for ing in (rec.get("ingredients") or []):
        mid, mdat = material_for(ing)
        if mid not in seen_mat:
            seen_mat.add(mid)
            datoms.append(mdat)
        pct = ing.get("percent_estimate")
        edge = {":bom.edge/id": f"bom.{gtin14}.{mid.split('.')[-1]}",
                ":bom.edge/parent": pid, ":bom.edge/child": mid, ":bom.edge/tier": 1,
                ":bom.edge/criticality": 0.3, ":bom.edge/sourcing": ":representative"}
        if isinstance(pct, (int, float)):
            edge[":bom.edge/qty"] = round(float(pct), 2)
            edge[":bom.edge/qty-unit"] = "%mass"
        datoms.append(edge)
    return datoms


def normalize_dataset(records):
    """Normalize many OFF records; dedup materials by id (first wins). Returns datom list + stats."""
    out, mat_ids, n_ok, n_skip = [], set(), 0, 0
    for rec in records:
        ds = normalize_record(rec)
        if not ds:
            n_skip += 1
            continue
        n_ok += 1
        for d in ds:
            if ":material/id" in d:
                if d[":material/id"] in mat_ids:
                    continue
                mat_ids.add(d[":material/id"])
            out.append(d)
    return out, {"products_ok": n_ok, "skipped_bad_gtin": n_skip, "materials": len(mat_ids)}


def _to_edn(datoms):
    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, str):
            return v if v.startswith(":") else edn_str(v)
        return v
    lines = [";; uchiwake — datoms normalized from Open Food Facts (CC-BY-SA). :representative (G5).",
             ";; ADR-2606081800. GTINs validated by GS1 mod-10; LIVE OFF fetch is G7-gated.", "["]
    for d in datoms:
        lines.append(" {" + " ".join(f"{k} {val(v)}" for k, v in d.items()) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main(argv):
    inp = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else DEFAULT_IN
    records = json.loads(inp.read_text(encoding="utf-8"))
    if isinstance(records, dict):
        records = records.get("products", [])
    datoms, stats = normalize_dataset(records)
    print(f"OFF normalize: {stats['products_ok']} products, {stats['materials']} materials, "
          f"{stats['skipped_bad_gtin']} skipped (bad/missing GTIN)", file=sys.stderr)
    edn = _to_edn(datoms)
    if "--out" in argv:
        pathlib.Path(argv[argv.index("--out") + 1]).write_text(edn, encoding="utf-8")
    else:
        print(edn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
