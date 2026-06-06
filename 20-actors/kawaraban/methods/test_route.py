#!/usr/bin/env python3
"""kawaraban — tests for the medium/routing core (route.py). Standalone + pytest."""
from __future__ import annotations
import pathlib

from route import (
    load_edn, classify, validate, wire_table, actor_links, actor_targets, ACTOR_WIRE,
)

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-news-graph.kotoba.edn"
W = "did:web:etzhayyim.com:actor:"


def _rows():
    return load_edn(SEED)


def test_classify_counts():
    outlets, sections, articles, mentions, wires = classify(_rows())
    assert len(outlets) == 7, len(outlets)
    assert len(sections) == 10, len(sections)
    assert len(articles) == 12, len(articles)
    assert len(mentions) == 24, len(mentions)
    assert len(wires) == 9, len(wires)


def test_validate_passes_on_seed():
    _, _, articles, _, _ = classify(_rows())
    validate(articles)  # must not raise


def test_validate_refuses_verdict():
    try:
        validate([{":news.article/id": "x", ":news.article/kind": ":mirror",
                   ":news.article/outlet": "o", ":news.article/url": "u",
                   ":news.article/verdict": True}])
        assert False, "expected G1 refusal"
    except ValueError as e:
        assert "G1" in str(e), e


def test_validate_refuses_full_text():
    try:
        validate([{":news.article/id": "x", ":news.article/kind": ":mirror",
                   ":news.article/outlet": "o", ":news.article/url": "u",
                   ":news.article/full-text": "the whole body"}])
        assert False, "expected G4 refusal"
    except ValueError as e:
        assert "G4" in str(e), e


def test_validate_refuses_unknown_kind():
    try:
        validate([{":news.article/id": "x", ":news.article/kind": ":original"}])
        assert False, "expected G11 refusal (:original is not a kind)"
    except ValueError as e:
        assert "G11" in str(e), e


def test_validate_refuses_mirror_without_url():
    try:
        validate([{":news.article/id": "x", ":news.article/kind": ":mirror",
                   ":news.article/outlet": "o"}])
        assert False, "expected G4/G5 refusal"
    except ValueError as e:
        assert "url" in str(e).lower(), e


def test_validate_refuses_actor_event_without_provenance():
    try:
        validate([{":news.article/id": "x", ":news.article/kind": ":actor-event",
                   ":news.article/source-actor": "did:web:...:danjo"}])
        assert False, "expected G7/G11 refusal (missing source-tid)"
    except ValueError as e:
        assert "source-tid" in str(e), e


def test_wire_table_maps_actors_to_men():
    _, _, _, _, wires = classify(_rows())
    t = wire_table(wires)
    assert t[W + "danjo"] == "politics", t.get(W + "danjo")
    assert t[W + "kanae"] == "economy", t.get(W + "kanae")
    assert t[W + "watari"] == "international", t.get(W + "watari")
    assert t[W + "kataribe"] == "culture", t.get(W + "kataribe")


def test_actor_links_chokepoint_cluster():
    _, _, articles, mentions, _ = classify(_rows())
    edges, degree = actor_links(articles, mentions)
    wa, wt, mi = W + "watari", W + "watatsuna", W + "mitooshi"
    # the chokepoint story (m7) + 3 actor-events (e2/e3/e5) all co-mention watari+watatsuna
    assert edges[frozenset({wa, wt})] == 4, edges.get(frozenset({wa, wt}))
    assert edges[frozenset({wa, mi})] == 2, edges.get(frozenset({wa, mi}))
    # danjo + ooyake share exactly one article (m6)
    assert edges[frozenset({W + "danjo", W + "ooyake"})] == 1
    # watatsuna is wired to >= 2 distinct actors (the medium connects it)
    assert degree[wt] >= 2, degree.get(wt)


def test_actor_targets_excludes_entities():
    _, _, _, mentions, _ = classify(_rows())
    # art.e1 mentions danjo (actor) + gov.jp.mof (entity); only the actor is a wire endpoint
    tgts = actor_targets("art.e1", mentions)
    assert W + "danjo" in tgts
    assert "gov.jp.mof" not in tgts


def test_actor_wire_constant_has_no_duplicates_collapsing_men():
    # every fallback maps to a known 面 men keyword
    valid = {"front", "politics", "economy", "international", "society",
             "culture", "science", "sports", "local", "opinion"}
    for actor, men in ACTOR_WIRE.items():
        assert men in valid, (actor, men)


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"route: {len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
