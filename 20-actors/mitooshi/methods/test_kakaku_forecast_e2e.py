#!/usr/bin/env python3
"""End-to-end: kakaku 価格 → bridge_kakaku → mitooshi forecast (cross-actor pipeline).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_kakaku_forecast_e2e.py
    python3 test_kakaku_forecast_e2e.py

Proves the WHOLE composition closes leak-free: kakaku's supply-demand-index observations,
bridged into mitooshi :series+:obs over successive snapshots, are forecast as a DISTRIBUTION
routed to :resilience (G1/G2), using only pre-target history (G5), and scored against the
realizing obs with skill vs climatology (G12). This is the price/supply-demand analogue of
the chokepoint pipeline — the first time a kakaku series is forecast end-to-end.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from bridge_kakaku import bridge_kakaku
    from forecast import forecast_next, forecast_trail, series_histories
    from score import Observation, score_pair
except ImportError:
    from mitooshi.methods.bridge_kakaku import bridge_kakaku  # type: ignore
    from mitooshi.methods.forecast import (  # type: ignore
        forecast_next, forecast_trail, series_histories)
    from mitooshi.methods.score import Observation, score_pair  # type: ignore

_PID = "jan_4901777300443"
_SID = "s-jan-4901777300443-supply-demand"


def _bridged_trail():
    """Bridge a rising supply-demand-index for one product over snapshots t=1..7.
    A clear trend makes the forecast non-trivially skillful and the realizing obs at t=7
    scoreable. Returns the accumulated mitooshi rows (series + obs)."""
    series: dict = {}
    obs: list = []
    for t in range(1, 8):
        idx = round(-0.6 + 0.15 * t, 4)   # rises from -0.45 → 0.45 across the window
        b = bridge_kakaku([{":sd/product": _PID, ":sd/index": idx}], observed_at=t)
        series.update(b["series"])
        obs.extend(b["obs"])
    return list(series.values()) + obs


def test_pipeline_builds_a_forecastable_trail():
    rows = _bridged_trail()
    hist = series_histories(rows)
    assert _SID in hist
    ts = [t for t, _v in hist[_SID]]
    assert ts == sorted(ts) and ts == [1, 2, 3, 4, 5, 6, 7]


def test_kakaku_series_forecast_is_distribution_to_resilience():
    rows = _bridged_trail()
    fc = forecast_next(_SID, series_histories(rows)[_SID], target_at=7)
    assert fc is not None
    assert fc.point_asserted is False        # G1 — never a deterministic point
    assert fc.use == ":resilience"           # G2 — resilience, never a trade/price target
    assert fc.dist_kind == "gaussian"


def test_kakaku_forecast_is_leak_free():
    rows = _bridged_trail()
    fc = forecast_next(_SID, series_histories(rows)[_SID], target_at=7)
    assert fc.info_as_of < 7                  # G5 — only history strictly before target
    s = score_pair(fc, Observation(oid="o", observed_at=7, value=0.45))
    assert "crps" in s                        # obs strictly after info ⇒ no leak raise


def test_kakaku_forecast_trail_scores_against_realizing_obs():
    rows = _bridged_trail()
    out = forecast_trail(rows, target_at=7)
    row = next(r for r in out if r["series"] == _SID)
    assert "crps" in row and "skill" in row   # realizing obs at t=7 is in the trail → scored
    assert row["forecast"].use == ":resilience"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"kakaku_forecast_e2e.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
