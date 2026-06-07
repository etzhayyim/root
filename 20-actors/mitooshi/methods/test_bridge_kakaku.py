#!/usr/bin/env python3
"""Tests for the mitooshi kakaku price/supply-demand bridge (methods/bridge_kakaku.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_bridge_kakaku.py
    python3 test_bridge_kakaku.py
"""
from __future__ import annotations

import pathlib
import sys

try:
    from bridge_kakaku import bridge_kakaku
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.bridge_kakaku import bridge_kakaku  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore

_SAMPLE = pathlib.Path(__file__).resolve().parent.parent / "data" / "bridge" / "kakaku-sample.edn"


def _records():
    return load_edn(_SAMPLE)


def test_maps_price_and_supply_demand_series():
    b = bridge_kakaku(_records(), observed_at=1)
    ids = set(b["series"])
    # each product yields a price-level series and a supply-demand-index series
    assert "s-jan-4901777300443-price" in ids
    assert "s-jan-4901777300443-supply-demand" in ids
    assert "s-gtin-04901234567894-price" in ids
    assert "s-gtin-04901234567894-supply-demand" in ids


def test_ignores_non_price_sd_records():
    b = bridge_kakaku(_records(), observed_at=1)
    # sample has 1 spread + 1 offer + 1 merchant → 3 skipped; 4 forecastable series
    assert b["skipped"] == 3
    assert len(b["series"]) == 4


def test_carries_value_and_source_actor():
    b = bridge_kakaku(_records(), observed_at=5)
    price = next(o for o in b["obs"] if o[":obs/series"] == "s-jan-4901777300443-price")
    assert price[":obs/value"] == 3200.0 and price[":obs/source-actor"] == "kakaku"
    assert price[":obs/observed-at"] == 5
    sd = next(o for o in b["obs"] if o[":obs/series"] == "s-jan-4901777300443-supply-demand")
    assert sd[":obs/value"] == 0.42


def test_source_class_is_public_broadcast_g4():
    b = bridge_kakaku(_records(), observed_at=1)
    s = b["series"]["s-jan-4901777300443-supply-demand"]
    assert s[":series/source-class"] == ":public-broadcast"   # G4
    assert s[":series/sourcing"] == ":representative"         # G11
    assert s[":series/kind"] == ":supply-demand-index"


def test_obs_chain_into_a_forecast_trail():
    # two snapshots build the append-only as-of trail mitooshi forecasts (非終末論)
    b1 = bridge_kakaku(_records(), observed_at=1)
    b2 = bridge_kakaku(_records(), observed_at=2)
    trail = [o for o in (b1["obs"] + b2["obs"])
             if o[":obs/series"] == "s-jan-4901777300443-supply-demand"]
    ats = sorted(o[":obs/observed-at"] for o in trail)
    assert ats == [1, 2]


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"bridge_kakaku.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
