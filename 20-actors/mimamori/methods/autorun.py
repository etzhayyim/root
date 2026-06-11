#!/usr/bin/env python3
"""autorun.py — mimamori deterministic heartbeat (ADR-2606112300; pattern: ADR-2606091000).

One cycle = replay seed → offer-matching pass (§D4) → aggregate coverage →
persist ONE content-addressed transaction to the local append-only kotoba log.

  - NO external I/O: offline seed in, LOCAL log out. Live legs (real roster /
    §1.16 outreach / musubi ceremony / social-capital mint) stay G7-gated —
    one human gate-flip away, not taken here.
  - Deterministic + resume-safe: the cycle number derives from the log length
    (no wall clock, no randomness); same seed + same cycle → same CID.
  - The G1..G7 gates are enforced INSIDE the loop by the bond engine's own
    validator — the heartbeat cannot emit what the schema cannot represent.

Usage:
    python3 autorun.py [seed.json] [--log LOG] [--cycles N]
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bond import load_seed, replay  # noqa: E402
from coverage_report import coverage_of_engine  # noqa: E402
from kotoba import (LOG_DEFAULT, append_tx, bond_datoms, coverage_datoms,  # noqa: E402
                    head_cid, make_tx, read_log, verify_chain)
from match import match_cycle  # noqa: E402


def run_cycle(seed: dict, log_path: pathlib.Path = LOG_DEFAULT) -> dict:
    """One heartbeat. Returns an aggregate-only summary (G5)."""
    prior = read_log(log_path)
    cycle = len(prior) + 1

    engine = replay(seed)                      # gates enforced in replay
    summary = match_cycle(engine, seed["roster"])
    cov = coverage_of_engine(engine, seed["roster"])

    datoms = bond_datoms(engine) + coverage_datoms(cov, cycle)
    tx = make_tx(datoms, tx_id=cycle, as_of=cycle, prev_cid=head_cid(log_path))
    cid = append_tx(tx, log_path)

    chain = verify_chain(log_path)
    if not chain["ok"]:
        raise RuntimeError(f"kotoba log chain broken at {chain['broken_at']}")

    return {  # aggregate-only: counts and CIDs, never a DID
        "cycle": cycle,
        "cid": cid,
        "datoms": len(datoms),
        "chain_length": chain["length"],
        **summary,                # unkept_before / offers_emitted / skipped_*
        "coverage": cov,          # post-match: the offered now count as pending
    }


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed_path = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-mimamori-bonds.json"
    log_path = pathlib.Path(argv[argv.index("--log") + 1]) if "--log" in argv else LOG_DEFAULT
    cycles = int(argv[argv.index("--cycles") + 1]) if "--cycles" in argv else 1

    seed = load_seed(seed_path)
    for _ in range(cycles):
        s = run_cycle(seed, log_path)
        print(f"cycle {s['cycle']}: {s['datoms']} datoms → {s['cid'][:16]}… "
              f"(unkept {s['unkept_before']}→{s['coverage']['unkept_count']} "
              f"via {s['offers_emitted']} offers, chain {s['chain_length']} ok)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
