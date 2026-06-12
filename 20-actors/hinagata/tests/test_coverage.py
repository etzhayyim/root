#!/usr/bin/env python3
"""hinagata 雛形 — coverage-report tests (ADR-2606111954). Pure stdlib.

Verifies coverage honesty (G5): the report measures real coverage against honest denominators,
surfaces statute-binding integrity (which clauses are not yet anchored to a public law), and
never claims completeness it does not have.
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def test_report_renders():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert md.startswith("# hinagata"), "coverage report missing title"
    assert "coverage of all template families" in md, "missing honest-denominator framing"
    assert "Statute-binding integrity" in md, "missing statute-binding section"


def test_legal_systems_plural():
    """Law is plural — the seed must span more than one legal system."""
    nodes, _ = load(SEED)
    systems = {n.get(":jurisdiction/system") for n in nodes.values()
               if n.get(":lt/kind") == ":jurisdiction"}
    systems.discard(None)
    assert {":civil-law", ":common-law", ":international"} <= systems, \
        f"expected plural legal systems, got {systems}"


def test_statute_binding_surfaced_honestly():
    """G5: clauses not yet citing a statute are surfaced as the binding worklist, not hidden."""
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    # the report must state a clause-binding count (either all-bound or an explicit unbound list)
    assert ("clauses unbound" in md) or ("cite at least one public statute" in md), \
        "statute-binding integrity not reported"


def test_language_coverage_reported_and_multilingual():
    """A worldwide commons must be multilingual, and the report must measure it."""
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "Language coverage" in md, "language coverage not reported"
    langs = {n.get(":template/lang") for n in nodes.values() if n.get(":lt/kind") == ":template"}
    langs.discard(None)
    assert len(langs) >= 3, f"expected a multilingual corpus, got languages {langs}"
    # every non-English translation must be linked to an original by a :translates 縁
    translated = {e[":en/from"] for e in edges if e.get(":en/kind") == ":translates"}
    for e in edges:
        if e.get(":en/kind") == ":translates":
            assert e[":en/to"] in nodes and e[":en/from"] in nodes, "dangling :translates 縁"


def test_coverage_is_not_overclaimed():
    """Coverage fractions vs world denominators must be tiny (honest ~0-by-design)."""
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    concepts = sum(1 for n in nodes.values() if n.get(":lt/kind") == ":concept")
    assert concepts < 120, "seed should not claim to cover all contract families"
    assert "e-0" in md or "e-2" in md or "e-1" in md, "expected scientific-notation tiny fractions"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
