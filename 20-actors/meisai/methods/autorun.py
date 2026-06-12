#!/usr/bin/env python3
"""autorun.py — meisai 明細 AUTONOMOUS statement-intake heartbeat on the kotoba Datom log.
ADR-2606122400.

The same constitution-permitted autonomous-loop shape the actor family uses (danjo / shionome /
kanjō autorun): each heartbeat the actor sweeps the LOCAL intake directory (`data/intake/*.edn` —
statement EDN files the member-principal fetch leg already wrote), ingests every intake whose
content CID is not yet in the log, and persists ONE content-addressed transaction per new intake
to the append-only local kotoba Datom log, linking the previous CID into a verifiable commit-DAG.

Constitutional posture holds by construction:

  - MEMBER-OWN data only (G1): the intake directory is the member's own machine; meisai fetches
    nothing and talks to no service.
  - credential/PAN unrepresentable (G2): ingest.guard raises before anything is persisted.
  - local-only (G3): `data/` is gitignored; the loop persists to the LOCAL log only — it
    publishes, pins, and posts nothing.
  - provenance + dedup (G5): the intake content CID is in every statement tx; re-running the
    loop over the same intakes appends nothing (resume-safe, deterministic, no wall clock).

NO external I/O. Stdlib only.

    python3 autorun.py --cycles 3            # heartbeat → LOCAL kotoba Datom log
    python3 autorun.py --fresh --cycles 1    # wipe the local log first (it is regenerable)
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest  # noqa: E402
from kotoba import (LOG_DEFAULT, append_tx, head_cid, make_tx, read_log,  # noqa: E402
                    verify_chain)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
INTAKE = DATA / "intake"
BASE_AS_OF = 20260612


def ingested_cids(log_path: pathlib.Path = LOG_DEFAULT) -> set[str]:
    """Every intake content CID already persisted (the dedup set)."""
    out: set[str] = set()
    for tx in read_log(log_path):
        for d in tx.get(":tx/datoms", []):
            if len(d) == 4 and d[2] == ":meisai.stmt/intake-cid":
                out.add(d[3])
    return out


def sweep(intake_dir: pathlib.Path = INTAKE) -> list[pathlib.Path]:
    """Deterministic intake worklist (sorted; no set iteration)."""
    if not intake_dir.is_dir():
        return []
    return sorted(p for p in intake_dir.iterdir() if p.suffix == ".edn" and p.is_file())


def run_cycle(cycle: int, intake_dir: pathlib.Path = INTAKE,
              log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """One heartbeat: sweep intake → ingest every NEW statement (one tx each). Deterministic:
    tx ids continue from the log length; as-of derives from BASE_AS_OF + cycle (no wall clock)."""
    seen = ingested_cids(log_path)
    appended = []
    skipped = 0
    for path in sweep(intake_dir):
        doc, cid = ingest.load_statement(path)
        if cid in seen:
            skipped += 1
            continue
        datoms = ingest.statement_datoms(doc, cid)
        tx = make_tx(datoms, tx_id=len(read_log(log_path)) + 1,
                     as_of=BASE_AS_OF + cycle, prev_cid=head_cid(log_path))
        append_tx(tx, log_path)
        seen.add(cid)
        appended.append({"intake": path.name, "cid": tx[":tx/cid"], "datoms": len(datoms)})
    return {"cycle": cycle, "appended": appended, "skipped": skipped,
            "head": head_cid(log_path)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="meisai autonomous statement-intake heartbeat")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--intake", type=pathlib.Path, default=INTAKE)
    ap.add_argument("--log", type=pathlib.Path, default=LOG_DEFAULT)
    ap.add_argument("--fresh", action="store_true",
                    help="wipe the local log first (it is regenerable from intake)")
    args = ap.parse_args(argv)
    if args.fresh and args.log.exists():
        args.log.unlink()
    for c in range(1, args.cycles + 1):
        r = run_cycle(c, args.intake, args.log)
        print(f"cycle {r['cycle']}: +{len(r['appended'])} tx "
              f"({sum(a['datoms'] for a in r['appended'])} datoms), "
              f"{r['skipped']} already ingested, head {r['head'][:16] or '(empty)'}")
    v = verify_chain(args.log)
    print(f"chain: ok={v['ok']} length={v['length']}")
    return 0 if v["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
