#!/usr/bin/env python3
"""mimamori cell entry — kotodama-cell-runner contract (ADR-2605192415 §7.1).

Registered in 50-infra/cluster/murakumo/cell-runner/cells.edn as
MimamoriHeartbeatCell (node benjamin, cron 23 * * * *, healthz 13080).
`fire()` runs ONE deterministic heartbeat (ADR-2606112300 / pattern 2606091000):

    replay synthetic seed → §D4 offer-matching → keeper-side social-capital
    mint (moyai reuse) → aggregate coverage → ONE content-addressed tx
    appended to the actor-local kotoba commit-DAG → chain verified.

NO external I/O — the live legs (real roster / §1.16 outreach / musubi
ceremony / live social-capital mint) remain G7-gated. The returned summary is
aggregate-only (G5): counts and CIDs, never a DID.
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "methods"))


def fire(log_path: str | None = None) -> dict:
    """One heartbeat. Idempotent per log state (cycle derives from log length)."""
    from autorun import run_cycle
    from bond import load_seed
    from kotoba import LOG_DEFAULT

    seed = load_seed(_HERE / "data" / "seed-mimamori-bonds.json")
    target = pathlib.Path(log_path) if log_path else LOG_DEFAULT
    summary = run_cycle(seed, target)
    print(f"MimamoriHeartbeatCell cycle {summary['cycle']}: "
          f"unkept {summary['unkept_before']}→{summary['coverage']['unkept_count']} "
          f"via {summary['offers_emitted']} offers, "
          f"{summary['shakai']['minted_units']} social-capital minted, "
          f"chain {summary['chain_length']} ok → {summary['cid'][:16]}…")
    return summary


if __name__ == "__main__":
    fire()
