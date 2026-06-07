#!/usr/bin/env python3
"""Tests for mitooshi baseline forecasting over the persisted trail (methods/forecast.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_forecast.py
    python3 test_forecast.py

Proves observe→bridge→persist→forecast closes leak-free: forecasts are distributions
(G1, point-asserted false), use only pre-target history (G5), and score against the
realizing obs with proper rules + skill vs climatology (G12). One test runs over the
REAL persisted trail; the rest use a synthetic varying history for non-trivial skill.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from forecast import (emit_forecast_edn, forecast_next, forecast_trail, series_histories)
    from score import Forecast, Observation, score_pair
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.forecast import (  # type: ignore
        emit_forecast_edn, forecast_next, forecast_trail, series_histories)
    from mitooshi.methods.score import Forecast, Observation, score_pair  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore

_TRAIL = (pathlib.Path(__file__).resolve().parent.parent / "data" / "persisted"
          / "chokepoint-trail.kotoba.edn")


def _synthetic():
    # one series with a clear upward trend, through the target t=7 (so the forecast at
    # target=7 — built from history t<7 — has a realizing obs to score against)
    return [{":obs/series": "s-x", ":obs/observed-at": t, ":obs/value": float(10 + 2 * t)}
            for t in range(1, 8)]


def test_series_histories_are_sorted():
    h = series_histories(_synthetic())
    assert "s-x" in h
    ts = [t for t, _v in h["s-x"]]
    assert ts == sorted(ts)


def test_forecast_is_distribution_not_point():
    fc = forecast_next("s-x", series_histories(_synthetic())["s-x"], target_at=7)
    assert fc is not None
    assert fc.point_asserted is False          # G1 — never a deterministic point
    assert fc.dist_kind == "gaussian" and fc.use == ":resilience"


def test_forecast_is_leak_free_info_as_of_before_target():
    fc = forecast_next("s-x", series_histories(_synthetic())["s-x"], target_at=7)
    assert fc.info_as_of < 7                    # G5 — only saw history strictly before target
    # and scoring against the realized obs at 7 does NOT raise (obs strictly after info)
    s = score_pair(fc, Observation(oid="o", observed_at=7, value=24.0))
    assert "crps" in s


def test_forecast_next_returns_none_without_prior_history():
    # target at/before the first observation → no leak-free history → no forecast
    assert forecast_next("s-x", series_histories(_synthetic())["s-x"], target_at=1) is None


def test_persistence_beats_climatology_on_a_trend():
    rows = _synthetic()
    pers = forecast_trail(rows, target_at=7, method="persistence")
    clim = forecast_trail(rows, target_at=7, method="climatology")
    pj = next(r for r in pers if r["series"] == "s-x")
    cj = next(r for r in clim if r["series"] == "s-x")
    # on a clean linear trend, persistence (last value) tracks far better than the mean
    assert pj["crps"] < cj["crps"]
    assert pj["skill"] > 0                      # G12 — persistence is skilled vs climatology


def test_emit_forecast_edn_marks_g1_and_g5():
    rows = _synthetic()
    edn = emit_forecast_edn(forecast_trail(rows, 7, "climatology"), 7, "climatology")
    assert ":forecast/point-asserted false" in edn       # G1
    assert "leak-free" in edn and "G10-gated" in edn      # G5 + G10


def test_runs_over_real_persisted_trail_leak_free():
    # the real append-only trail must be forecastable end-to-end without a leak
    if not _TRAIL.exists():
        return                                  # trail not generated in this checkout — skip
    rows = load_edn(_TRAIL)
    h = series_histories(rows)
    assert h, "expected series in the persisted trail"
    target = max(t for pairs in h.values() for t, _v in pairs)  # latest snapshot
    fcs = forecast_trail(rows, target_at=target, method="climatology")
    assert fcs, "expected at least one forecast over the real trail"
    for r in fcs:
        assert r["forecast"].info_as_of < target           # leak-free by construction


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"forecast.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
