#!/usr/bin/env python3
"""Tests for the kabuto 兜 social composer + Charter-Rider gate (methods/social.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_social.py
    python3 test_social.py

Covers the Charter-Rider §2(a)-(h) deny-scan (the content gate every post must pass) and
the G2 framing invariant: every composed post is aggregate-first, public-facts-only, and
framed as resilience/accountability — never a target-list.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from kabuto_edn import classify, load_edn
    from social import charter_rider_clean, compose, post_record
except ImportError:
    from kabuto.methods.kabuto_edn import classify, load_edn  # type: ignore
    from kabuto.methods.social import charter_rider_clean, compose, post_record  # type: ignore

_SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-public-companies.kotoba.edn"


def test_charter_rider_rejects_prohibited_content():
    # §2(a) force / §2 weaponisation-adjacent phrasing must be refused
    assert charter_rider_clean("where to cut the supply chain") is False
    assert charter_rider_clean("weapon design for the foundry") is False
    assert charter_rider_clean("buy adsense placement") is False


def test_charter_rider_accepts_clean_resilience_text():
    assert charter_rider_clean(
        "Disclosed supply dependency — diversify to build resilience.") is True


def test_compose_posts_pass_the_rider_gate():
    rows = load_edn(_SEED)
    companies, _a, _c, edges, _p = classify(rows)
    posts = list(compose(companies, edges, "top jurisdictions US/JP/CN"))
    assert posts, "expected composed posts"
    for _subject, _kind, text in posts:
        assert charter_rider_clean(text), f"composed post violates the Rider: {text!r}"


def test_compose_headline_is_not_a_target_list():
    rows = load_edn(_SEED)
    companies, _a, _c, edges, _p = classify(rows)
    posts = list(compose(companies, edges, "summary"))
    headline = [t for _s, kind, t in posts if kind == "intel-report"]
    assert headline and "not a target-list" in headline[0]


def test_compose_supply_edges_frame_diversification():
    rows = load_edn(_SEED)
    companies, _a, _c, edges, _p = classify(rows)
    edge_posts = [t for _s, kind, t in compose(companies, edges, "") if kind == "supply-edge"]
    assert edge_posts
    # the actionable framing is diversification/resilience, never interdiction
    for t in edge_posts:
        assert "resilience" in t.lower() or "diversify" in t.lower()


def test_post_record_is_well_formed_atproto_post():
    rec = post_record("hello", ["en"])
    assert rec["$type"] == "app.bsky.feed.post"
    assert len(rec["text"]) <= 300 and rec["createdAt"].endswith("Z")


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"kabuto social.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
