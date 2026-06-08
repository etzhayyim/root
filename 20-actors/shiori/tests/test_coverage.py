#!/usr/bin/env python3
"""shiori 栞 — coverage-report tests (ADR-2606082100). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-wellbecoming-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "coverage of all cohorts/detractors is ~0 by design" in md
    assert "Gap map" in md
    # all four facets present: cohort, detractor, driver (structural), mitigator
    assert "isolation" in md and "always-on-work-culture" in md and "social-connection" in md


def test_all_severities_and_both_relief_and_pressure_present():
    nodes, _ = load(SEED)
    detrs = [n for n in nodes.values() if n.get(":organism/kind") == ":detractor"]
    sevs = {d.get(":detractor/severity") for d in detrs}
    assert {":critical", ":severe", ":moderate"} <= sevs, f"thin severity spine: {sevs}"
    kinds = {n.get(":organism/kind") for n in nodes.values()}
    assert ":mitigator" in kinds, "no relief side (the 守り) in the seed"
    assert ":driver" in kinds, "no structural-driver side in the seed"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
