#!/usr/bin/env python3
"""inochi 命 — coverage-report tests (ADR-2606073000). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-biosphere-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    # honest denominator disclosure present
    assert "coverage of all life is ~0 by design" in md
    # all three realms are represented in a real seed
    assert "terrestrial" in md and "marine" in md
    # the gap map names next-wave targets (freshwater/fungi/etc. are thin by design)
    assert "Gap map" in md


def test_realms_present():
    nodes, _ = load(SEED)
    realms = {n.get(":eco/realm") for n in nodes.values()
              if n.get(":organism/kind") in (":ecosystem", ":biome")}
    assert ":terrestrial" in realms and ":marine" in realms


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
