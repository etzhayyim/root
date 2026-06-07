#!/usr/bin/env python3
"""Tests for the cross-actor chokepoint resilience composite (methods/synthesize.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_synthesize.py
    python3 test_synthesize.py

Proves the watari+watatsuna+mitooshi fusion: per-chokepoint current transit + cable load +
forecast, ranked by a scale-free resilience-attention blend, framed as a resilience map
(never a target-list). Runs over the committed Datom artifacts (reproducible).
"""
from __future__ import annotations

import pathlib
import sys

try:
    from synthesize import (_chokepoint_of, forecast_by_series, latest_by_series,
                          render_edn, synthesize)
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.synthesize import (  # type: ignore
        _chokepoint_of, forecast_by_series, latest_by_series, render_edn, synthesize)
    from mitooshi.methods.analyze import load_edn  # type: ignore

_HERE = pathlib.Path(__file__).resolve().parent.parent
_TRAIL = _HERE / "data" / "persisted" / "chokepoint-trail.kotoba.edn"
_FORECAST = _HERE / "data" / "persisted" / "chokepoint-forecast.kotoba.edn"


def _comp():
    return synthesize(load_edn(_TRAIL), load_edn(_FORECAST))


def test_chokepoint_extraction_strips_suffixes():
    assert _chokepoint_of("s-malacca-cable") == ":malacca"
    assert _chokepoint_of("s-luzon-strait-transit") == ":luzon-strait"


def test_latest_by_series_takes_max_observed_at():
    rows = [{":obs/series": "s-x", ":obs/observed-at": 1, ":obs/value": 10.0},
            {":obs/series": "s-x", ":obs/observed-at": 3, ":obs/value": 30.0},
            {":obs/series": "s-x", ":obs/observed-at": 2, ":obs/value": 20.0}]
    assert latest_by_series(rows)["s-x"] == 30.0


def test_composite_ranks_malacca_top():
    comp = _comp()
    assert comp[0]["chokepoint"] == ":malacca"     # highest transit AND cable → top attention


def test_attention_is_bounded_and_sorted_desc():
    comp = _comp()
    atts = [d["attention"] for d in comp]
    assert all(0.0 <= a <= 1.0 for a in atts)
    assert atts == sorted(atts, reverse=True)


def test_attention_formula_blend():
    comp = _comp()
    cables = [d["cable_load"] for d in comp if d["cable_load"] is not None]
    transits = [d["transit"] for d in comp if d["transit"] is not None]
    mc, mt = max(cables), max(transits)
    for d in comp:
        nc = (d["cable_load"] / mc) if d["cable_load"] else 0.0
        nt = (d["transit"] / mt) if d["transit"] else 0.0
        assert abs(d["attention"] - round(0.7 * nc + 0.3 * nt, 4)) < 1e-9


def test_composite_joins_forecast():
    comp = _comp()
    # at least one chokepoint carries a forecast cable mean (joined from the forecast artifact)
    assert any(d.get("forecast_cable_mean") is not None for d in comp)


def test_transit_only_chokepoint_has_low_attention():
    comp = _comp()
    hormuz = next((d for d in comp if d["chokepoint"] == ":hormuz"), None)
    if hormuz:                                       # hormuz has transit but no cable in seed
        assert hormuz["cable_load"] is None and hormuz["attention"] < 0.5


def test_render_edn_is_resilience_not_target_list():
    edn = render_edn(_comp())
    assert "RESILIENCE" in edn and "never a target-list" in edn.lower()
    assert ":choke/attention" in edn and "G10-gated" in edn


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"synthesize.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
