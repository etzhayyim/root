#!/usr/bin/env python3
"""tanemaki 種蒔き — coverage-report integrity tests (ADR-2606122001). Pure stdlib."""
import sys, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))
from analyze import load  # noqa: E402
from coverage_report import report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-stewardship-graph.kotoba.edn"


def test_report_renders_and_invariants_hold():
    nodes, edges = load(SEED)
    md = report(nodes, edges)
    assert md.startswith("# tanemaki")
    assert "holds for all orgs" in md, "G1 integrity line missing or violated"
    assert "all instruments on the allowlist" in md, "G2 integrity line missing or violated"
    assert "**1.00** ✓" in md, "G4 rubric-sum line missing or violated"
    assert "all named" in md, "G5 evidence-source line missing or violated"
    assert "all fictional" in md, "G6 synthetic-seed line missing or violated"


def test_all_routes_exercised():
    nodes, edges = load(SEED)
    md = report(nodes, edges)
    for bucket in ("propose", "insufficient-evidence", "excluded"):
        assert f"| {bucket} |" in md
    assert "MISSING" not in md.split("## Route exercise")[1].split("##")[0], \
        "a route lane is unexercised by the seed"


def test_every_criterion_sourced():
    nodes, edges = load(SEED)
    sourced = {e[":en/from"] for e in edges if e.get(":en/kind") == ":sourced-from"}
    for nid, n in nodes.items():
        if n.get(":fs/kind") == ":criterion":
            assert nid in sourced, f"criterion {nid} has no disclosed evidence source (G4)"


def test_report_deterministic():
    nodes, edges = load(SEED)
    assert report(nodes, edges) == report(nodes, edges)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
