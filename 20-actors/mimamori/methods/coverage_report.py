#!/usr/bin/env python3
"""mimamori 見守り — AGGREGATE-ONLY coverage report (G5: NEVER-a-throne).

誰の保持者でもない人間を作らない — measured without naming anyone.
The report contains COUNTS only. No DID, no per-person line, ever
(test-enforced: "did:" must not appear in the output).

Pure stdlib. Usage:
    python3 coverage_report.py [seed.json] [--out OUTDIR]
"""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bond import load_seed, replay  # noqa: E402


def coverage_of_engine(m, roster_list) -> dict:
    """Aggregate-only coverage over a (possibly already-mutated) engine (G5)."""
    roster = set(roster_list)
    kept_active = {m._kept[b] for b, st in m._state.items() if st == ":active"}
    kept_pending = {m._kept[b] for b, st in m._state.items() if st == ":offered"}
    relays = sum(1 for b, st in m._state.items() if st == ":handed-off")
    return {
        "members_total": len(roster),
        "with_keeper": len(kept_active & roster),
        "offers_pending": len((kept_pending - kept_active) & roster),
        "unkept_count": len(roster - kept_active - kept_pending),
        "active_bonds": sum(1 for st in m._state.values() if st == ":active"),
        "relays": relays,
        "datoms": len(m.datoms),
    }


def coverage(seed: dict) -> dict:
    return coverage_of_engine(replay(seed), seed["roster"])


def render(c: dict) -> str:
    L = ["# mimamori 見守り — coverage report (AGGREGATE-ONLY, G5)",
         "",
         "GENERATED — do not hand-edit. No DID appears here, by construction.",
         "",
         f"- members (synthetic roster): {c['members_total']}",
         f"- with an active keeper:      {c['with_keeper']}",
         f"- offers pending:             {c['offers_pending']}",
         f"- **unkept (the gap)**:       {c['unkept_count']}",
         f"- active bonds:               {c['active_bonds']}",
         f"- relays (継ぎ):              {c['relays']}",
         f"- datoms (append-only):       {c['datoms']}",
         "",
         "The unkept are not listed (G5). The offer-matching cell reaches them",
         "directly, one covenant offer at a time (ADR-2606112300 §D4; G7-gated).",
         ""]
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed_path = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-mimamori-bonds.json"
    outdir = pathlib.Path(argv[argv.index("--out") + 1]) if "--out" in argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    rep = render(coverage(load_seed(seed_path)))
    out = outdir / "coverage-report.md"
    out.write_text(rep, encoding="utf-8")
    print(f"mimamori coverage → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
