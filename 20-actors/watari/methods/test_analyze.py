#!/usr/bin/env python3
"""Tests for the watari 渡り moving-craft situational analyzer (methods/analyze.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
    python3 test_analyze.py

Covers the analyzer's aggregate roll-ups (chokepoint transit, lane load, freshness tail)
AND the load-bearing charter invariant: watari is situational-awareness, NEVER
person-surveillance — a craft is a craft, not a person (G4). The seed carries no person
identity and the analyzer surfaces none.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import analyze, classify, load_edn, render_report
except ImportError:
    from watari.methods.analyze import (  # type: ignore
        analyze, classify, load_edn, render_report)

_SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-craft-graph.kotoba.edn"


def _load():
    rows = load_edn(_SEED)
    craft, fixes, legs, lanes = classify(rows)
    return craft, fixes, legs, lanes, analyze(craft, fixes, legs, lanes)


def test_classify_buckets_the_seed():
    craft, fixes, legs, lanes, _ = _load()
    assert len(craft) == 13          # 8 vessels + 5 aircraft
    assert len(fixes) == 26
    assert len(lanes) == 9


def test_kind_split_vessels_and_aircraft():
    craft, fixes, legs, lanes, a = _load()
    assert a["kind_count"].get(":vessel") == 8
    assert a["kind_count"].get(":aircraft") == 5


def test_latest_fix_is_max_observed_at_per_craft():
    craft, fixes, legs, lanes, a = _load()
    # the latest fix per craft must be the lexicographically-max ISO-8601 ts among its fixes
    by_craft = {}
    for fx in fixes:
        by_craft.setdefault(fx[":craft.fix/craft"], []).append(
            fx.get(":craft.fix/observed-at", ""))
    for c, fx in a["latest"].items():
        assert fx.get(":craft.fix/observed-at", "") == max(by_craft[c])


def test_chokepoint_transit_rollup():
    craft, fixes, legs, lanes, a = _load()
    # matches the analyzer's own headline: malacca 3, suez-red-sea 1, hormuz 1
    assert a["choke_transit"].get(":malacca") == 3
    assert a["choke_transit"].get(":suez-red-sea") == 1
    assert a["choke_transit"].get(":hormuz") == 1


def test_freshness_tail_flags_stale_craft():
    craft, fixes, legs, lanes, a = _load()
    # craft whose latest fix predates the dataset latest = the honest stale tail
    assert len(a["stale"]) == 2
    assert all(a["latest"][c].get(":craft.fix/observed-at", "") < a["dataset_latest"]
               for c in a["stale"])


def test_chokepoint_output_is_bridge_compatible_with_mitooshi():
    # watari's chokepoint keys live in the SAME space mitooshi's bridge joins on
    craft, fixes, legs, lanes, a = _load()
    known = {":malacca", ":luzon-strait", ":suez-red-sea", ":hormuz", ":gibraltar",
             ":south-china-sea", ":bab-el-mandeb"}
    assert set(a["choke_transit"]) <= known      # every emitted chokepoint is joinable


def test_g4_no_person_tracking_invariant():
    # STRUCTURAL: a craft is a craft, not a person. The seed must carry NO person identity,
    # and the analyzer must surface none. Person-level surveillance is unrepresentable.
    rows = load_edn(_SEED)
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in r:
            assert ":person" not in k, f"person-level key {k} present (violates G4)"
            assert "operator-name" not in k  # operator is an org id, never a named human


def test_report_is_aggregate_first_and_non_targeting():
    craft, fixes, legs, lanes, a = _load()
    md = render_report(craft, fixes, legs, lanes, a)
    assert "person-surveillance" in md and "never" in md.lower()
    assert "target-list" in md            # the framing invariant is stated in the report


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"watari analyze.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
