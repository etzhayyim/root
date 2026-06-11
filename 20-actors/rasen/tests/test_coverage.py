#!/usr/bin/env python3
"""rasen 螺旋 — coverage-report tests (ADR-2606101000). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-genome-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    # honest denominator disclosure present
    assert "coverage of all genes/variants is ~0 by design" in md
    # the G1 public-only guard is surfaced
    assert "no individual genotypes" in md
    # the gap map names next-wave targets
    assert "Gap map" in md


def test_taxa_span_life_not_just_humans():
    nodes, _ = load(SEED)
    taxa = {n.get(":gene/taxon") for n in nodes.values() if n.get(":genome/kind") == ":gene"}
    assert ":homo-sapiens" in taxa, "human genetics missing"
    # at least one non-human taxon (life is broader than humans)
    assert len(taxa - {":homo-sapiens"}) >= 1, f"only human taxa present: {taxa}"


def test_populations_are_aggregate():
    nodes, _ = load(SEED)
    pops = {n.get(":population/code") for n in nodes.values()
            if n.get(":genome/kind") == ":population"}
    assert ":global" in pops and len(pops) >= 3, f"thin population aggregates: {pops}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
