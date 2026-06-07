#!/usr/bin/env python3
"""
Enrich per-country kotodama.jsonld profile sections with fields from the
generated stateProfile records (/tmp/state-records/profile/{iso3}.json).

When `etzhayyim deploy` runs on the appview, the enriched profile is picked up
by `registerProfileToYata()` — a write path that historically works even
when com.atproto.repo.putRecord is degraded.

Usage:
    python3 enrich-kotodama-profiles.py                      # all found
    python3 enrich-kotodama-profiles.py --iso jpn,usa,fra    # subset
    python3 enrich-kotodama-profiles.py --records-dir /tmp/state-records/profile
    python3 enrich-kotodama-profiles.py --dry-run
"""
import argparse, json, glob, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APPVIEW = ROOT / "60-apps/etzhayyim-project-states/appview"

# Fields from generated stateProfile record to merge into kotodama.jsonld
# profile block. Keeps kotodama.jsonld's existing displayName/description
# unless the current values are templates ("Government of X Government").
SCALAR_FIELDS = ["ministryCount", "contractCount", "bpmnCount", "dataSourceRef"]
# Lists merged by id (preserve hand-crafted entries, append new)
LIST_ID_FIELDS = ["procedures", "documentTemplates"]
# Lists replaced only if profile field is empty/missing (preserve rich hand edits)
LIST_FILL_FIELDS = ["addresses", "contacts", "desks", "complianceFrameworks"]

def find_kotodama(iso3):
    pattern = str(APPVIEW / f"etzhayyim-wasm-states-{iso3}-*")
    dirs = glob.glob(pattern)
    for d in dirs:
        mj = Path(d) / "kotodama.jsonld"
        if mj.exists(): return mj
    return None

def enrich(iso3, records_dir, dry_run):
    rec_file = records_dir / f"{iso3}.json"
    if not rec_file.exists():
        return (iso3, "skip-no-record", 0)
    payload = json.loads(rec_file.read_text())
    rec = payload.get("record", {})

    mj_path = find_kotodama(iso3)
    if not mj_path:
        return (iso3, "skip-no-appview", 0)
    mj = json.loads(mj_path.read_text())
    profile = mj.setdefault("profile", {})

    changed = 0
    for field in SCALAR_FIELDS:
        if field in rec and profile.get(field) != rec[field]:
            profile[field] = rec[field]; changed += 1
    # Fill empty lists only (preserve existing rich entries)
    for field in LIST_FILL_FIELDS:
        if rec.get(field) and not profile.get(field):
            profile[field] = rec[field]; changed += 1
    # ID-merge: keep existing, append new by id
    for field in LIST_ID_FIELDS:
        new_items = rec.get(field) or []
        if not new_items: continue
        existing = profile.get(field) or []
        existing_ids = {item.get("id") for item in existing if isinstance(item, dict) and item.get("id")}
        merged = list(existing)
        for item in new_items:
            if isinstance(item, dict) and item.get("id") and item["id"] not in existing_ids:
                merged.append(item); existing_ids.add(item["id"])
        if merged != existing:
            profile[field] = merged; changed += 1

    if changed == 0:
        return (iso3, "unchanged", 0)
    if dry_run:
        return (iso3, "would-write", changed)
    mj_path.write_text(json.dumps(mj, indent=2, ensure_ascii=False) + "\n")
    return (iso3, "written", changed)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", help="comma-separated iso3 (default: all generated)")
    ap.add_argument("--records-dir", default="/tmp/state-records/profile")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    records_dir = Path(args.records_dir)
    if not records_dir.exists():
        print(f"records dir not found: {records_dir}", file=sys.stderr); sys.exit(2)
    if args.iso:
        isos = [x.strip().lower() for x in args.iso.split(",") if x.strip()]
    else:
        isos = sorted(f.stem for f in records_dir.glob("*.json"))

    stats = {"written": 0, "would-write": 0, "unchanged": 0,
             "skip-no-record": 0, "skip-no-appview": 0}
    total_fields = 0
    for iso in isos:
        iso, status, fields = enrich(iso, records_dir, args.dry_run)
        stats[status] = stats.get(status, 0) + 1
        total_fields += fields
        if status in ("written", "would-write"):
            print(f"  {iso}: {status} ({fields} fields)")
    print()
    for k,v in stats.items():
        if v: print(f"  {k}: {v}")
    print(f"  total fields merged: {total_fields}")

if __name__ == "__main__":
    main()
