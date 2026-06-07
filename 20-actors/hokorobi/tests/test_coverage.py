#!/usr/bin/env python3
"""hokorobi 綻び — coverage-report tests (ADR-2606073400). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-finrisk-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "coverage of all institutions is ~0 by design" in md
    assert "Gap map" in md
    # the three financial pillars (bank/insurer/pension) appear in a real seed
    assert "bank" in md and "insurer" in md and "pension-fund" in md


def test_three_pillars_present():
    nodes, _ = load(SEED)
    sectors = {n.get(":inst/sector") for n in nodes.values()
               if n.get(":organism/kind") == ":institution"}
    assert {":bank", ":insurer", ":pension-fund"} <= sectors, f"missing a pillar: {sectors}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
