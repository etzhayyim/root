#!/usr/bin/env python3
"""kabuto 兜 — public-company ingest bridge (R1 scaffold; offline default).

ADR-2606022000. Normalizes PUBLIC company registries into the kotoba EAVT
:company/* vocabulary and dedup-merges with the curated seed (seed wins). The
full-universe sources below are the path to "register ALL public companies";
live fetch of any of them is G7 Council + operator gated (millions of LEIs) and
is a NO-OP unless KABUTO_OPERATOR_GATE is set. Default offline run simply
re-emits the seed as the merged graph so downstream cells have a stable input.

Sources (all PUBLIC record):
  --source gleif     GLEIF LEI Golden-Copy (every legal entity w/ an LEI; ISO 17442)
  --source edgar      SEC EDGAR company tickers + submissions (US listings)
  --source exchange   exchange listing directories (TWSE/TSE/KRX/Euronext/HKEX/…)
  --source file PATH  a local public-dataset-shaped JSON to bridge offline

stdlib only. Usage:
    python3 ingest.py [--source gleif|edgar|exchange|file] [--in PATH] [--out PATH]
"""
from __future__ import annotations
import sys
import os
import json
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kabuto_edn import load_edn, classify, edn_str  # noqa: E402

OPERATOR_GATE = os.environ.get("KABUTO_OPERATOR_GATE", "") == "1"

# Documented full-universe endpoints — NOT fetched unless the operator gate is set.
SOURCES = {
    "gleif": "https://leidata.gleif.org/api/v1/lei-records (GLEIF Golden Copy)",
    "edgar": "https://www.sec.gov/files/company_tickers.json (SEC EDGAR)",
    "exchange": "per-exchange listing directories (TWSE/TSE/KRX/Euronext/HKEX/LSE/…)",
}


def bridge_public_json(records):
    """Map a public-dataset-shaped record list → :company/* datom dicts.

    Expected loose shape per record: {id|lei, name, ticker, exchange, country,
    sector, status}. Unknown fields are dropped; sourcing is forced to
    :representative (G5) because a bridged record is not first-party verified.
    """
    out = []
    for r in records:
        cid = r.get("id") or (("org.corp." + (r.get("country", "xx").lower()) + "." +
                               (r.get("ticker") or r.get("lei") or "unknown").lower()))
        d = {":company/id": cid,
             ":company/name": r.get("name", cid),
             ":company/status": ":" + r.get("status", "listed"),
             ":company/sourcing": ":representative"}
        if r.get("ticker"):
            d[":company/ticker"] = r["ticker"]
        if r.get("exchange"):
            d[":company/exchange"] = ":" + str(r["exchange"]).lower()
        if r.get("country"):
            d[":company/country"] = r["country"]
        if r.get("sector"):
            d[":company/sector"] = ":" + str(r["sector"]).lower()
        if r.get("lei"):
            d[":company/lei"] = r["lei"]
        out.append(d)
    return out


def emit_company(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, str) and not v.startswith(':'):
            parts.append(f'{k} {edn_str(v)}')
        else:
            parts.append(f'{k} {v}')
    return " {" + " ".join(parts) + "}"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = here / "data" / "seed-public-companies.kotoba.edn"
    outp = here / "data" / "companies.merged.kotoba.edn"
    if "--out" in argv:
        outp = pathlib.Path(argv[argv.index("--out") + 1])

    source = argv[argv.index("--source") + 1] if "--source" in argv else None
    infile = argv[argv.index("--in") + 1] if "--in" in argv else None

    bridged = []
    if source in SOURCES and not OPERATOR_GATE:
        print(f"kabuto.ingest: source '{source}' = {SOURCES[source]}")
        print("  → G7 GATED: live full-universe fetch requires KABUTO_OPERATOR_GATE=1 "
              "(Council). Skipping live fetch; emitting seed only (offline default).")
    elif source == "file" and infile:
        recs = json.loads(pathlib.Path(infile).read_text(encoding="utf-8"))
        recs = recs.get("companies", recs) if isinstance(recs, dict) else recs
        bridged = bridge_public_json(recs)
        print(f"kabuto.ingest: bridged {len(bridged)} records from {infile} (:representative)")
    elif source:
        print(f"kabuto.ingest: unknown source '{source}'. Known: {', '.join(SOURCES)}, file")

    # dedup-merge: seed wins on :company/id collision
    seed_rows = load_edn(seed)
    seed_companies, addresses, contacts, edges, processes = classify(seed_rows)
    merged_ids = set(seed_companies)
    extra = [d for d in bridged if d[":company/id"] not in merged_ids]

    seed_text = seed.read_text(encoding="utf-8").rstrip()
    if extra:
        # append bridged companies before the closing bracket
        body = seed_text[:seed_text.rfind("]")].rstrip()
        tail = "\n ;; ── bridged (ingest; :representative) ──\n" + \
               "\n".join(emit_company(d).strip() and (" " + emit_company(d).strip()) for d in extra)
        outp.write_text(body + "\n" + "\n".join(" " + emit_company(d).strip() for d in extra) + "\n]\n",
                        encoding="utf-8")
    else:
        outp.write_text(seed_text + "\n", encoding="utf-8")

    print(f"kabuto.ingest: merged graph → {outp} "
          f"({len(seed_companies)} seed + {len(extra)} bridged companies)")


if __name__ == "__main__":
    main(sys.argv)
