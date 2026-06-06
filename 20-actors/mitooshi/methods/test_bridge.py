#!/usr/bin/env python3
"""Tests for the mitooshi watari/watatsuna chokepoint bridge (methods/bridge.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_bridge.py
    python3 test_bridge.py
"""
from __future__ import annotations

import pathlib
import sys

try:
    from bridge import bridge
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.bridge import bridge  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore

_BRIDGE = pathlib.Path(__file__).resolve().parent.parent / "data" / "bridge"


def _by_actor():
    return {
        "watari": load_edn(_BRIDGE / "watari-sample.edn"),
        "watatsuna": load_edn(_BRIDGE / "watatsuna-sample.edn"),
    }


def test_bridge_maps_chokepoints_to_series():
    b = bridge(_by_actor(), observed_at=1)
    ids = set(b["series"])
    # watari → transit series, watatsuna → cable series, joined on the chokepoint keyword
    assert "s-malacca-transit" in ids and "s-malacca-cable" in ids
    assert "s-luzon-strait-transit" in ids and "s-luzon-strait-cable" in ids


def test_bridge_ignores_non_chokepoint_records():
    b = bridge(_by_actor(), observed_at=1)
    # watari sample has 1 lane + 1 craft; watatsuna sample has 1 station → 3 skipped
    assert b["skipped"] == 3
    # series are chokepoints only (4 watari + 3 watatsuna = 7)
    assert len(b["series"]) == 7


def test_bridge_carries_value_and_source_actor():
    b = bridge(_by_actor(), observed_at=5)
    malacca_t = next(o for o in b["obs"] if o[":obs/series"] == "s-malacca-transit")
    assert malacca_t[":obs/value"] == 3.0 and malacca_t[":obs/source-actor"] == "watari"
    assert malacca_t[":obs/observed-at"] == 5
    malacca_c = next(o for o in b["obs"] if o[":obs/series"] == "s-malacca-cable")
    assert malacca_c[":obs/value"] == 940.16 and malacca_c[":obs/source-actor"] == "watatsuna"


def test_bridge_same_chokepoint_two_series_two_units():
    # the shared keyword :malacca yields BOTH a vessel-transit and a cable-load series
    b = bridge(_by_actor(), observed_at=1)
    assert b["series"]["s-malacca-transit"][":series/kind"] == ":transit-load"
    assert b["series"]["s-malacca-cable"][":series/kind"] == ":cable-load"
    assert b["series"]["s-malacca-cable"][":series/source-class"] == ":public-broadcast"  # G4


def test_bridge_single_actor_ok():
    b = bridge({"watari": load_edn(_BRIDGE / "watari-sample.edn")}, observed_at=1)
    assert len(b["series"]) == 4 and all(":obs/source-actor" in o for o in b["obs"])


def test_bridged_obs_chain_into_a_forecast_series():
    # two snapshots at ts 1 and 2 build an append-only as-of trail for one chokepoint
    b1 = bridge(_by_actor(), observed_at=1)
    b2 = bridge(_by_actor(), observed_at=2)
    trail = [o for o in (b1["obs"] + b2["obs"]) if o[":obs/series"] == "s-malacca-cable"]
    ats = sorted(o[":obs/observed-at"] for o in trail)
    assert ats == [1, 2]   # the forecastable trail mitooshi would consume (非終末論)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"bridge.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
