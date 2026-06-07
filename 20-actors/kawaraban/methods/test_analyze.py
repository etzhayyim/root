#!/usr/bin/env python3
"""kawaraban — tests for the edition composer (analyze.py). Standalone + pytest."""
from __future__ import annotations
import pathlib

from route import load_edn
from analyze import (
    compose, render_md, render_edn, assert_rank_signals,
    ALLOWED_RANK_SIGNALS, USED_SIGNALS, score,
)

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-news-graph.kotoba.edn"


def _c():
    return compose(load_edn(SEED))


def test_compose_has_leads_and_sections():
    c = _c()
    assert len(c["leads"]) == 4, len(c["leads"])
    # the international 面 (chokepoint cluster) must be populated
    assert c["by_men"]["international"], "international 面 empty"
    assert c["by_men"]["economy"], "economy 面 empty"


def test_rank_signals_are_public_good_only():
    # G2 — the used signals are a subset of the allowlist; no engagement/paid signal exists.
    for s in USED_SIGNALS:
        assert s in ALLOWED_RANK_SIGNALS, s
    for banned in ("paid-placement", "sponsored", "engagement", "dwell-time"):
        assert banned not in ALLOWED_RANK_SIGNALS, banned


def test_assert_rank_signals_refuses_engagement():
    assert_rank_signals(USED_SIGNALS)  # ok
    for banned in ("engagement", "paid-placement", "dwell-time"):
        try:
            assert_rank_signals([banned])
            assert False, f"expected G2 refusal for {banned}"
        except ValueError as e:
            assert "G2" in str(e), e


def test_score_monotonic_in_recency():
    mentions = []
    a_new = {":news.article/id": "n", ":news.article/as-of": 100}
    a_old = {":news.article/id": "o", ":news.article/as-of": 0}
    s_new = score(a_new, mentions, newest=100, oldest=0, seen_outlets=set())
    s_old = score(a_old, mentions, newest=100, oldest=0, seen_outlets=set())
    assert s_new > s_old, (s_new, s_old)


def test_render_md_contains_front_and_wire():
    md = render_md(_c())
    assert "一面" in md
    assert "Actor-to-actor wire" in md
    assert "no full" in md.lower() or "G4" in md  # link-out disclaimer present
    # link-out: a mirror article renders a markdown link
    assert "([link](" in md


def test_render_edn_is_unpublished_and_not_final():
    edn = render_edn(_c())
    assert ":news.issue/published false" in edn
    assert ":news.issue/final false" in edn
    assert ":news.issue/server-held-key false" in edn
    assert ":news.medium.link/" in edn  # the actor-to-actor edges are emitted


def test_compose_refuses_charter_violating_seed():
    bad = load_edn(SEED) + [{
        ":news.article/id": "art.bad", ":news.article/kind": ":mirror",
        ":news.article/outlet": "o", ":news.article/url": "u",
        ":news.article/truth-rating": 5}]
    try:
        compose(bad)
        assert False, "expected G1 refusal during compose()"
    except ValueError as e:
        assert "G1" in str(e), e


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
    print(f"analyze: {len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
