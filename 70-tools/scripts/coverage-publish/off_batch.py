#!/usr/bin/env python3
"""off_batch — Council-authorised bounded live Open Food Facts ingest for uchiwake 内訳.
ADR-2606081800 G7 (operator gate OPEN). Reproducible, polite, bounded.

Fetches a CURATED list of real GTINs (curated/gtins.txt) from the Open Food Facts v2 product API
(CC-BY-SA) one polite request at a time, tolerant of misses (a GTIN not in OFF / failing the GS1
mod-10 check digit is skipped), writes the hits in OFF record shape to
uchiwake/data/ingest/openfoodfacts.live.json, then runs uchiwake ingest.py so the existing
GTIN-validated OFF adapter normalises + merges them (seed wins). Representative sourcing (G5).

BOUNDED batch (a curated list), NOT the full ~3M OFF universe — that remains a continued operator/
loop process. Polite: declared User-Agent, 0.4s between requests.

Usage: off_batch.py [--list curated/gtins.txt]
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, time, urllib.request, urllib.error

UA = "etzhayyim-uchiwake research (jun@etzhayyim.group)"
GET = ("https://world.openfoodfacts.org/api/v2/product/{gtin}.json"
       "?fields=code,product_name,brands,countries_tags,ingredients")
HERE = pathlib.Path(__file__).resolve().parent
UCHIWAKE = HERE.parents[2] / "20-actors" / "uchiwake"
LIVE = UCHIWAKE / "data" / "ingest" / "openfoodfacts.live.json"


def fetch_one(gtin: str):
    req = urllib.request.Request(GET.format(gtin=gtin), headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:   # noqa: S310 (https, fixed host)
            obj = json.load(r)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    if obj.get("status") == 1 and isinstance(obj.get("product"), dict) and obj["product"].get("product_name"):
        p = obj["product"]; p.setdefault("code", gtin)
        return p
    return None


def main(argv) -> int:
    if os.environ.get("UCHIWAKE_OPERATOR_GATE") != "1":
        print("REFUSED (G7): set UCHIWAKE_OPERATOR_GATE=1 (Council-authorised) to run live OFF ingest.",
              file=sys.stderr)
        return 2
    list_path = HERE / "curated" / "gtins.txt"
    if "--list" in argv:
        list_path = pathlib.Path(argv[argv.index("--list") + 1])
    gtins = [ln.strip() for ln in list_path.read_text().splitlines()
             if ln.strip() and not ln.strip().startswith("#")]
    by_code, hits, miss = {}, 0, 0
    for g in gtins:
        p = fetch_one(g)
        if p:
            by_code[str(p["code"])] = p; hits += 1
        else:
            miss += 1
        time.sleep(0.4)  # polite
    print(f"  OFF batch: {hits} resolved / {miss} skipped (not in OFF or bad GS1) of {len(gtins)}",
          file=sys.stderr)
    LIVE.parent.mkdir(parents=True, exist_ok=True)
    LIVE.write_text(json.dumps({"products": list(by_code.values())}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    r = subprocess.run([sys.executable, "methods/ingest.py"], cwd=str(UCHIWAKE),
                       capture_output=True, text=True, timeout=120)
    sys.stderr.write(r.stderr)
    print(r.stdout.strip())
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
