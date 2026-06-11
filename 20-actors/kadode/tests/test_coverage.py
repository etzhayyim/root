#!/usr/bin/env python3
"""kadode 門出 — coverage-report tests (ADR-2606112238). Pure stdlib."""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-resignation-graph.kotoba.edn"


def test_report_renders():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert md.startswith("# kadode") and "coverage of all employment situations is bounded" in md


def test_upl_invariant_reported_holding():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "holds for all scenarios" in md, "UPL invariant must report as holding"
    assert "VIOLATED" not in md


def test_all_routes_present():
    """The full escalation ladder (self → messenger → union → lawyer) must exist."""
    nodes, _ = load(SEED)
    actors = {n.get(":route/actor") for n in nodes.values() if n.get(":lx/kind") == ":route"}
    assert {":worker-self", ":kadode-messenger", ":labor-union", ":lawyer"} <= actors


def test_every_scenario_and_risk_covered():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    scen = sum(1 for n in nodes.values() if n.get(":lx/kind") == ":scenario")
    assert f"{scen}/{scen}" in md, "all scenarios should reach a route"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
