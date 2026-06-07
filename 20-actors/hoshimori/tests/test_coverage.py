#!/usr/bin/env python3
"""hoshimori 星守 — coverage-report tests (ADR-2606073600). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-orbit-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "coverage of all catalogued objects is ~0 BY DESIGN" in md
    assert "Gap map" in md
    # the key regimes appear in a real seed
    assert "leo-low" in md and "geo" in md and "meo" in md


def test_all_regimes_present():
    nodes, _ = load(SEED)
    regimes = {n.get(":shell/regime") for n in nodes.values()
               if n.get(":organism/kind") == ":shell"}
    assert {":leo-low", ":sso", ":meo", ":geo"} <= regimes, f"missing a regime: {regimes}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
