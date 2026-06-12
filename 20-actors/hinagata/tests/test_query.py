#!/usr/bin/env python3
"""hinagata 雛形 — knowledge-graph query tests (ADR-2606111954). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import query  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-legal-template-graph.kotoba.edn"


def _g():
    return load(SEED)


def test_templates_in_jurisdiction():
    nodes, edges = _g()
    jp = query.templates_in_jurisdiction(nodes, edges, "jx.jp")
    assert jp, "expected templates governed by Japan"
    for t in jp:
        assert nodes[t][":lt/kind"] == ":template"
    # international has the broad-reach templates
    intl = query.templates_in_jurisdiction(nodes, edges, "jx.intl")
    assert "tmpl.sales-intl" in intl


def test_statutes_grounding_template_are_real_statutes():
    nodes, edges = _g()
    st = query.statutes_grounding_template(nodes, edges, "tmpl.dpa-gdpr")
    assert st, "GDPR DPA should rest on statutes"
    for s in st:
        assert nodes[s][":lt/kind"] == ":statute"
    # the DPA must rest on at least one GDPR article
    assert any("gdpr" in s for s in st)


def test_translations_of_nda_are_multilingual():
    nodes, edges = _g()
    tr = query.translations_of(nodes, edges, "tmpl.nda-mutual")
    assert len(tr) >= 5, f"NDA should have many translations, got {tr}"
    langs = {nodes[t].get(":template/lang") for t in tr}
    assert len(langs) >= 5, f"translations should span many languages, got {langs}"


def test_conflicting_clauses_symmetric_lookup():
    nodes, edges = _g()
    c = query.conflicting_clauses(nodes, edges, "cl.ip-assignment")
    assert "cl.cc-license" in c or "cl.copyleft-license" in c
    # the relation resolves from either side
    back = query.conflicting_clauses(nodes, edges, "cl.copyleft-license")
    assert "cl.ip-assignment" in back


def test_jurisdictions_for_concept_data_protection_is_global():
    nodes, edges = _g()
    jx = query.jurisdictions_for_concept(nodes, edges, "concept.data-protection")
    assert len(jx) >= 4, f"data-protection should be grounded across many jurisdictions, got {jx}"


def test_coverage_gaps_is_the_inverse_worklist():
    """gaps(concept) = MAJOR jurisdictions present in the graph that don't ground the concept."""
    nodes, edges = _g()
    have = set(query.jurisdictions_for_concept(nodes, edges, "concept.data-protection"))
    gaps = query.coverage_gaps(nodes, edges, "concept.data-protection")
    # a gap is never something already grounded, and is always a real major-jurisdiction node
    for g in gaps:
        assert g not in have
        assert g in query.MAJOR_JURISDICTIONS and g in nodes
    # electronic-signature is broadly grounded, so it should have few/zero gaps
    esign_gaps = query.coverage_gaps(nodes, edges, "concept.electronic-signature")
    assert len(esign_gaps) <= len(query.coverage_gaps(nodes, edges, "concept.escrow")), \
        "broadly-grounded e-signature should have no more gaps than a niche concept"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
