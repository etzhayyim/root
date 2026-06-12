#!/usr/bin/env python3
"""match.py — mimamori offer-matching cell (ADR-2606112300 §D4).

誰の保持者でもない人間を作らない — the matching cell reaches each unkept roster
member DIRECTLY with one covenant offer at a time, never via a public list:

  G5  no global person view leaves this module — the returned summary is
      aggregate-only (counts); the offers themselves exist as bond datoms,
      visible to their two parties (G4) and no one else.
  G3  cooldown respected (a declined offer rests); an offer is an OFFER —
      the matched member may decline or ignore it, penalty-free.
  cap each keeper carries at most MAX_KEPT active+offered bonds — keeping is
      covenant, not a queue (Wellbecoming §1.13); the relay exists so that no
      keeper becomes a sleepless center (D3).

Deterministic: candidates are sorted; assignment is round-robin over the least-
loaded willing keepers. No wall clock, no randomness. Stdlib only.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bond import GateViolation, Mishmeret  # noqa: E402

MAX_KEPT = 2  # bonds (active + standing offers) a keeper may carry


def _load(engine: Mishmeret, did: str) -> int:
    return sum(1 for b in engine.bonds_of(did)
               if b["keeper"] == did and b["state"] in (":active", ":offered"))


def match_cycle(engine: Mishmeret, roster: list[str]) -> dict:
    """One matching pass: offer a keeper to every unkept member, capacity permitting.

    Returns an AGGREGATE-ONLY summary (G5). Mutates the engine by emitting offers
    (each offer is itself an append-only bond datom addressed to its two parties)."""
    members = sorted(set(roster))
    kept_or_offered = set()
    for bid, st in engine._state.items():
        if st in (":active", ":offered"):
            kept_or_offered.add(engine._kept[bid])
    unkept = [m for m in members if m not in kept_or_offered]

    offers = skipped_cooldown = skipped_capacity = 0
    for m in unkept:
        # least-loaded willing keepers, deterministic order; never self-keeping
        keepers = sorted((k for k in members if k != m and _load(engine, k) < MAX_KEPT),
                         key=lambda k: (_load(engine, k), k))
        placed = False
        for k in keepers:
            try:
                engine.offer(k, m)
                offers += 1
                placed = True
                break
            except GateViolation as e:
                if "cooldown" in str(e):
                    continue  # this pair rests; try the next keeper
                raise
        if not placed:
            if keepers:
                skipped_cooldown += 1
            else:
                skipped_capacity += 1

    return {  # aggregate-only (G5): counts, never names
        "unkept_before": len(unkept),
        "offers_emitted": offers,
        "skipped_cooldown": skipped_cooldown,
        "skipped_capacity": skipped_capacity,
    }
