#!/usr/bin/env python3
"""Tests for the mitooshi aggregate-first resilience advisory / social layer (methods/social.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_social.py
    python3 test_social.py

Verifies the non-adjudicating delivery invariants: distribution-only (G1), non-speculative
use (G2), planner-routed (G3), aggregate-first (G4), broadcast operator-gated (no-server-key).
"""
from __future__ import annotations

import sys

try:
    from social import compose_resilience_advisory, handle_social_post, ALLOWED_USE, PLANNERS
except ImportError:
    from mitooshi.methods.social import (  # type: ignore
        compose_resilience_advisory, handle_social_post, ALLOWED_USE, PLANNERS)


def test_advisory_states_a_band_not_a_point():
    adv = compose_resilience_advisory("s-x", mean=0.2, sd=0.3, target=7)
    assert adv["pointAsserted"] is False           # G1
    assert adv["band68"] == [-0.1, 0.5]
    assert "[-0.1, 0.5]" in adv["text"]            # the text states the band, not a single value


def test_advisory_refuses_point_assertion_g1():
    try:
        compose_resilience_advisory("s-x", 0.2, 0.3, 7, point_asserted=True)
    except ValueError as e:
        assert "G1" in str(e)
    else:
        assert False, "a point-asserted forecast must be refused (G1)"


def test_advisory_refuses_speculative_use_g2():
    for bad in (":trade", ":speculation", ":wager", ":position"):
        try:
            compose_resilience_advisory("s-x", 0.2, 0.3, 7, use=bad)
        except ValueError as e:
            assert "G2" in str(e)
        else:
            assert False, f"use {bad} must be refused (G2)"


def test_advisory_requires_planner_route_g3():
    try:
        compose_resilience_advisory("s-x", 0.2, 0.3, 7, route_to="some-trader")
    except ValueError as e:
        assert "G3" in str(e)
    else:
        assert False, "an advisory must route to a planner (G3)"
    # a valid planner is accepted
    adv = compose_resilience_advisory("s-x", 0.2, 0.3, 7, route_to="kanae")
    assert adv["routeTo"] == "kanae" and "kanae" in adv["text"]


def test_allowed_use_excludes_trade():
    assert ":resilience" in ALLOWED_USE
    assert "danjo" in PLANNERS
    for forbidden in (":trade", ":speculation", ":wager", ":position"):
        assert forbidden not in ALLOWED_USE


def test_social_post_default_is_draft_aggregate():
    out = handle_social_post({"forecasts": [
        {"series": "s-x", "mean": 0.2, "sd": 0.3, "target": 7, "routeTo": "danjo"}]})
    assert len(out["posts"]) == 1
    p = out["posts"][0]
    assert p["state"] == "draft"                    # operator-gated (no-server-key)
    assert p["shape"] == "aggregate"                # G4
    assert out["aggregateSharePct"] == 100


def test_social_post_posts_with_operator():
    out = handle_social_post({"forecasts": [
        {"series": "s-x", "mean": 0.2, "sd": 0.3, "target": 7, "routeTo": "danjo"}],
        "operatorRef": "op:1"})
    assert out["posts"][0]["state"] == "posted"


def test_social_post_refuses_bad_items_per_item():
    out = handle_social_post({"forecasts": [
        {"series": "ok", "mean": 0.2, "sd": 0.3, "target": 7, "routeTo": "danjo"},
        {"series": "pt", "mean": 0.2, "sd": 0.3, "target": 7, "pointAsserted": True},
        {"series": "tr", "mean": 0.2, "sd": 0.3, "target": 7, "use": ":trade"},
    ]})
    assert len(out["posts"]) == 1                    # only the clean one
    reasons = {r["series"]: r["reason"] for r in out["refused"]}
    assert "G1" in reasons["pt"] and "G2" in reasons["tr"]


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"social.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
