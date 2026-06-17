#!/usr/bin/env python3
"""edgar_batch — Council-authorised bounded live SEC EDGAR ingest for kanjō 勘定.
ADR-2606032000 / 2606101540 G7 (operator gate OPEN). ADDITIVE + safe.

Fetches a CURATED list of real CIKs (curated/ciks.txt) from SEC EDGAR companyfacts (public primary
disclosure, the only admissible source — G1; paid terminals forbidden) one polite request at a
time, parses FY 10-K/20-F facts as :authoritative, and merges them ADDITIVELY into the EXISTING
kanjō facts.merged.kotoba.edn (authoritative-wins dedup) — it NEVER resets to the seed, so prior
live-ingested filings are preserved. A backup is written first and the new fact count is asserted
≥ the old count.

BOUNDED batch (a curated list), NOT the full ~8,000-filer EDGAR universe — that remains a continued
operator/loop process. Polite: declared User-Agent (SEC fair-access), 0.4s between requests.

Usage: KANJO_OPERATOR_GATE=1 edgar_batch.py [--list curated/ciks.txt]
"""
from __future__ import annotations
import os, pathlib, shutil, sys, time

HERE = pathlib.Path(__file__).resolve().parent
KANJO = HERE.parents[2] / "20-actors" / "kanjo"
sys.path.insert(0, str(KANJO / "methods"))
import ingest as kanjo      # noqa: E402  (kanjo.fetch_edgar / merge_with_seed / _v)
import kanjo_edn            # noqa: E402

MERGED = KANJO / "data" / "facts.merged.kotoba.edn"
RANK = {":representative": 0, ":synthesized": 0, ":authoritative": 1}


def _id(row): return row.get(":fin.filing/id") or row.get(":fin.fact/id")
def _src(row): return row.get(":fin.fact/sourcing") or row.get(":fin.filing/sourcing")


def _write(rows):
    with MERGED.open("w", encoding="utf-8") as f:
        f.write(";; kanjō — merged 決算 graph (seed ⊕ ingested; :authoritative wins). GENERATED.\n[")
        f.write("\n".join(" {" + " ".join(f"{k} {kanjo._v(v)}" for k, v in r.items()) + "}" for r in rows))
        f.write("\n]\n")


def main(argv) -> int:
    if os.environ.get("KANJO_OPERATOR_GATE") != "1":
        print("REFUSED (G7): set KANJO_OPERATOR_GATE=1 (Council-authorised) to run live EDGAR ingest.",
              file=sys.stderr)
        return 2
    list_path = HERE / "curated" / "ciks.txt"
    if "--list" in argv:
        list_path = pathlib.Path(argv[argv.index("--list") + 1])
    ciks = [ln.strip() for ln in list_path.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")]

    base = kanjo_edn.read_file(str(MERGED)) if MERGED.exists() else []
    by_id = {_id(r): r for r in base if isinstance(r, dict)}
    old_facts = sum(1 for r in base if ":fin.fact/id" in r)

    added_filings = 0
    for cik in ciks:
        try:
            fl, fa = kanjo.fetch_edgar(cik)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"  CIK {cik}: skipped ({type(e).__name__})", file=sys.stderr); continue
        for row in fl + fa:
            rid = _id(row); old = by_id.get(rid)
            if old is None or RANK.get(_src(row), 0) >= RANK.get(_src(old), 0):
                by_id[rid] = row
        added_filings += len(fl)
        print(f"  EDGAR CIK {cik}: +{len(fl)} filings / +{len(fa)} authoritative facts", file=sys.stderr)
        time.sleep(0.4)  # polite (SEC fair-access)

    merged = list(by_id.values())
    new_facts = sum(1 for r in merged if ":fin.fact/id" in r)
    if new_facts < old_facts:
        print(f"REFUSED: merge would shrink facts ({old_facts} → {new_facts}); aborting.", file=sys.stderr)
        return 1
    if MERGED.exists():
        shutil.copy2(MERGED, MERGED.with_suffix(".edn.bak"))
    _write(merged)
    print(f"kanjō EDGAR batch: facts {old_facts} → {new_facts}, filings now "
          f"{sum(1 for r in merged if ':fin.filing/id' in r)} → {MERGED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
