#!/usr/bin/env python3
"""Tests for the watatsuna 綿津綱 submarine-cable resilience analyzer (methods/analyze.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
    python3 test_analyze.py

Covers the chokepoint/station/diversity roll-ups, the render_datoms bridge-input shape
(the :resilience/chokepoint-load records mitooshi's bridge consumes), AND the load-bearing
charter invariant: watatsuna is a RESILIENCE map, NEVER a target-list — it ranks fragility
to ADD redundancy, never to identify where to cut, and never asserts sabotage intent (G2).
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import analyze, classify, load_edn, render_datoms, render_report
except ImportError:
    from watatsuna.methods.analyze import (  # type: ignore
        analyze, classify, load_edn, render_datoms, render_report)

_SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-cable-graph.kotoba.edn"


def _load():
    rows = load_edn(_SEED)
    cables, stations, links, segs, faults = classify(rows)
    return cables, stations, links, segs, faults, analyze(cables, stations, links, segs, faults)


def test_classify_buckets_the_seed():
    cables, stations, links, segs, faults, _ = _load()
    assert len(cables) == 14 and len(stations) == 22
    assert len(links) == 43 and len(segs) == 11 and len(faults) == 2


def test_chokepoint_load_ranking():
    *_, a = _load()
    top = sorted(a["choke_load"], key=lambda k: -a["choke_load"][k])[:3]
    assert top[0] == ":malacca"
    assert abs(a["choke_load"][":malacca"] - 490.16) < 1e-6
    assert abs(a["choke_load"][":luzon-strait"] - 454.56) < 1e-6
    assert abs(a["choke_load"][":gibraltar"] - 324.0) < 1e-6


def test_chokepoint_count_matches_load_keys():
    *_, a = _load()
    assert set(a["choke_count"]) == set(a["choke_load"])
    assert all(a["choke_count"][cp] >= 1 for cp in a["choke_count"])


def test_redundancy_gap_is_single_cable_stations():
    cables, stations, links, segs, faults, a = _load()
    # a resilience finding: stations served by <=1 cable are the brittle landings
    for s in a["redundancy_gap"]:
        assert a["station_degree"][s] <= 1


def test_render_datoms_emit_bridge_input_shape():
    cables, stations, links, segs, faults, a = _load()
    edn = render_datoms(cables, stations, a)
    # the exact records mitooshi's bridge reads: :resilience/chokepoint + chokepoint-load
    assert ":resilience/chokepoint " in edn and ":resilience/chokepoint-load " in edn
    assert ":resilience/derived true" in edn        # never re-ingested as authoritative


def test_chokepoint_keys_are_mitooshi_bridge_compatible():
    *_, a = _load()
    known = {":malacca", ":luzon-strait", ":suez-red-sea", ":hormuz", ":gibraltar",
             ":south-china-sea", ":bab-el-mandeb"}
    # the chokepoints watatsuna emits must be joinable in mitooshi's keyword space
    assert set(a["choke_load"]) <= known


def test_g2_resilience_not_targeting_invariant():
    cables, stations, links, segs, faults, a = _load()
    md = render_report(cables, stations, links, segs, faults, a)
    assert "RESILIENCE" in md and "target-list" in md   # framing stated
    assert "NOT a target-list" in md


def test_g4_faults_do_not_adjudicate_intent():
    # fault records mirror public bulletins; the analyzer must not assert sabotage intent.
    rows = load_edn(_SEED)
    for r in rows:
        if isinstance(r, dict) and ":cable.fault/id" in r:
            # no field claims who-did-it / intent; only public-bulletin kind/location
            assert not any("culprit" in k or "attribution" in k or "intent" in k
                           for k in r)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"watatsuna analyze.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
