#!/usr/bin/env python3
"""aburi 炙り — autorun: local heartbeat that ingests the member's OWN privacy exports into the
append-only kotoba Datom log. ADR-2606161630.

One cycle sweeps the local intake dir (data/local/intake/*.json|*.edn), and for every export the
log has NOT yet seen (dedup by intake content CID), appends ONE content-addressed transaction:
the export's tracker-exposure datoms (via ingest.export_to_datoms) + an intake-marker datom. The
loop does NO network I/O (G7) and holds no credential (G2/G8); persistence is local-only under the
gitignored data/local/ (G7). Deterministic: tx ids continue from the log length; as-of derives
from BASE_AS_OF + cycle (no wall clock) → resume-safe, mid-sweep-crash byte-identical.

The export's `kind` is taken from a `:kind`/"kind" field inside the file, else inferred from the
filename prefix (apple-* / play-* / takeout-* / perm-*).

    python3 methods/autorun.py --cycles 1                 # ingest data/local/intake/*
    python3 methods/autorun.py --intake DIR --fresh       # custom dir, ignore existing log
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kotoba  # noqa: E402
import ingest  # noqa: E402

ACTOR = pathlib.Path(__file__).resolve().parents[1]
INTAKE_DEFAULT = ACTOR / "data" / "local" / "intake"
LOG_DEFAULT = kotoba.LOG_DEFAULT
BASE_AS_OF = 2606161630

_FILENAME_KIND = (
    ("apple", ":apple-app-privacy-report"),
    ("play", ":play-data-safety"),
    ("takeout", ":google-takeout-ads"),
    ("perm", ":android-permission-dump"),
)


def infer_kind(path: pathlib.Path, raw) -> str:
    if isinstance(raw, dict):
        k = raw.get(":kind") or raw.get("kind")
        if k:
            return k if str(k).startswith(":") else ":" + str(k)
    name = path.name.lower()
    for prefix, kind in _FILENAME_KIND:
        if name.startswith(prefix):
            return kind
    return ":play-data-safety"


def sweep(intake_dir: pathlib.Path) -> list[pathlib.Path]:
    if not intake_dir.exists():
        return []
    return sorted(p for p in intake_dir.iterdir()
                  if p.is_file() and p.suffix in (".json", ".edn"))


def ingested_cids(log_path: pathlib.Path) -> set[str]:
    seen = set()
    for tx in kotoba.read_log(log_path):
        for d in tx.get(":tx/datoms", []):
            if len(d) >= 4 and d[2] == ":aburi.intake/cid":
                seen.add(d[3])
    return seen


def run_cycle(cycle: int, intake_dir: pathlib.Path = INTAKE_DEFAULT,
              log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    seen = ingested_cids(log_path)
    appended, skipped = [], 0
    for path in sweep(intake_dir):
        raw, cid = ingest.load_export(path)
        if cid in seen:
            skipped += 1
            continue
        kind = infer_kind(path, raw)
        datoms = ingest.export_to_datoms(raw, kind, cid)
        tx = kotoba.make_tx(datoms, tx_id=len(kotoba.read_log(log_path)) + 1,
                            as_of=BASE_AS_OF + cycle, prev_cid=kotoba.head_cid(log_path))
        kotoba.append_tx(tx, log_path)
        seen.add(cid)
        appended.append({"intake": path.name, "kind": kind, "cid": tx[":tx/cid"],
                         "datoms": len(datoms)})
    return {"cycle": cycle, "appended": appended, "skipped": skipped,
            "head": kotoba.head_cid(log_path), "verify": kotoba.verify_chain(log_path)}


def main(argv):
    intake = pathlib.Path(argv[argv.index("--intake") + 1]) if "--intake" in argv else INTAKE_DEFAULT
    log = pathlib.Path(argv[argv.index("--log") + 1]) if "--log" in argv else LOG_DEFAULT
    cycles = int(argv[argv.index("--cycles") + 1]) if "--cycles" in argv else 1
    if "--fresh" in argv and log.exists():
        log.unlink()
    for c in range(cycles):
        res = run_cycle(c, intake, log)
        print(f"aburi cycle {c}: +{len(res['appended'])} ingested, {res['skipped']} skipped, "
              f"head {res['head'][:14]}…, chain-ok {res['verify']['ok']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
