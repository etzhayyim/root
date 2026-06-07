#!/usr/bin/env python3
"""tsugite 継ぎ手 — coverage-report tests (ADR-2606073800). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-peoples-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "coverage of all peoples/languages is ~0 by design" in md
    assert "Gap map" in md
    # both strands present: displacement (refugee/stateless) and erasure (endangered languages)
    assert "refugee-population" in md and "critically-endangered" in md


def test_both_strands_present():
    nodes, _ = load(SEED)
    pkinds = {n.get(":people/kind") for n in nodes.values() if n.get(":organism/kind") == ":people"}
    langs = [n for n in nodes.values() if n.get(":organism/kind") == ":language"]
    assert {":refugee-population", ":stateless", ":indigenous"} <= pkinds, f"thin peoples: {pkinds}"
    assert len(langs) >= 5, "endangered-language strand too thin"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
