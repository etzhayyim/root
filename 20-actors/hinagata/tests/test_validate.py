#!/usr/bin/env python3
"""hinagata 雛形 — integrity-validator tests (ADR-2606111954). Pure stdlib.

Enforces the maturity invariants validate.py checks: the committed seed has ZERO structural
errors, and its remaining soft warnings stay in the honestly-allowed categories (a generic
structural clause with no dedicated concept, or a registered-but-uncited statute). This keeps
the graph referentially sound as coverage keeps growing.
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import validate  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def test_seed_has_zero_errors():
    nodes, edges = load(SEED)
    errors, _ = validate.validate(nodes, edges)
    assert errors == [], "seed has structural integrity errors:\n  " + "\n  ".join(errors)


def test_warnings_are_only_allowed_soft_categories():
    """Remaining warnings must be honest soft issues, never a silent structural defect."""
    nodes, edges = load(SEED)
    _, warnings = validate.validate(nodes, edges)
    for w in warnings:
        ok = ("does not :instantiate any concept" in w) or ("registry-only" in w) \
            or ("not used by any template" in w) or ("not instantiated by any clause" in w) \
            or ("has no signature clause" in w)
        assert ok, f"unexpected warning category (investigate): {w}"


def test_every_template_is_complete():
    """Defence-in-depth: every template has clauses + a governing jurisdiction (errors, not warns)."""
    nodes, edges = load(SEED)
    errors, _ = validate.validate(nodes, edges)
    assert not any("has no clauses" in e or "has no :governed-by" in e for e in errors)


def test_all_citation_targets_are_statutes():
    nodes, edges = load(SEED)
    errors, _ = validate.validate(nodes, edges)
    assert not any("expected :statute" in e for e in errors)


def test_relational_edges_are_well_typed():
    """:conflicts-with is clause↔clause (no self-loop); :derived-from is template→template."""
    nodes, edges = load(SEED)
    conflicts = [e for e in edges if e.get(":en/kind") == ":conflicts-with"]
    derived = [e for e in edges if e.get(":en/kind") == ":derived-from"]
    assert conflicts and derived, "the :conflicts-with / :derived-from relations should be exercised"
    for e in conflicts:
        assert nodes[e[":en/from"]][":lt/kind"] == ":clause"
        assert nodes[e[":en/to"]][":lt/kind"] == ":clause"
        assert e[":en/from"] != e[":en/to"], "conflict self-loop"
    for e in derived:
        assert nodes[e[":en/from"]][":lt/kind"] == ":template"
        assert nodes[e[":en/to"]][":lt/kind"] == ":template"
    errors, _ = validate.validate(nodes, edges)
    assert not any("conflicts-with" in e or "derived-from" in e for e in errors)


def test_all_ten_edge_kinds_exercised():
    """Maturity completeness: every edge kind in the ontology is used at least once."""
    nodes, edges = load(SEED)
    kinds = {e.get(":en/kind") for e in edges}
    expected = {":has-clause", ":cites-statute", ":mandated-by", ":instantiates", ":governed-by",
                ":applies-in", ":translates", ":conflicts-with", ":derived-from", ":supersedes"}
    missing = expected - kinds
    assert not missing, f"ontology edge kinds never exercised: {missing}"
    # :supersedes must be template→template
    for e in edges:
        if e.get(":en/kind") == ":supersedes":
            assert nodes[e[":en/from"]][":lt/kind"] == ":template"
            assert nodes[e[":en/to"]][":lt/kind"] == ":template"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
