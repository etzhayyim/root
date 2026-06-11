#!/usr/bin/env python3
"""hinagata 雛形 — maturity-scorecard tests (ADR-2606111954). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import maturity  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def test_scorecard_renders_and_is_generated_banner():
    nodes, edges = load(SEED)
    md = maturity.maturity(nodes, edges)
    assert md.startswith("# hinagata") and "GENERATED" in md
    for section in ("## Size", "## Quality gates", "## Core-clause worldwide grounding",
                    "## Readiness"):
        assert section in md, f"missing section {section}"


def test_scorecard_reports_clean_integrity():
    nodes, edges = load(SEED)
    md = maturity.maturity(nodes, edges)
    assert "0 errors / 0 warnings" in md, "scorecard should reflect clean integrity"


def test_core_clauses_grounded_across_multiple_jurisdictions():
    """Each of the 8 core clauses must rest on law in >1 jurisdiction (the worldwide goal)."""
    nodes, edges = load(SEED)
    from analyze import CITE_KINDS
    st_jx = {n[":lt/id"]: n.get(":statute/jurisdiction") for n in nodes.values()
             if n.get(":lt/kind") == ":statute"}
    for cl in maturity.CORE_CLAUSES:
        assert cl in nodes, f"core clause {cl} missing from graph"
        jx = {st_jx.get(e[":en/to"]) for e in edges
              if e.get(":en/kind") in CITE_KINDS and e[":en/from"] == cl}
        jx = {j for j in jx if j}
        assert len(jx) >= 2, f"core clause {cl} grounded in only {len(jx)} jurisdiction(s)"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
