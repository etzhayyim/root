#!/usr/bin/env python3
"""Tests for mitooshi online-recalibrated backtest (methods/forecast.py calibration).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_calibrate.py
    python3 test_calibrate.py

The actor's own learning loop (cells/online_update apply_correction) applied leak-free at
each origin: bias from PAST residuals only shifts the mean, inflation scales the spread.
On a biased (trending) series this measurably improves both CRPS and PIT-mean toward 0.5 —
the documented bias-correction behavior — without ever seeing the future.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from forecast import backtest_calibrated, backtest_rolling, _recalib_params
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.forecast import (  # type: ignore
        backtest_calibrated, backtest_rolling, _recalib_params)
    from mitooshi.methods.analyze import load_edn  # type: ignore

_TRAIL = (pathlib.Path(__file__).resolve().parent.parent / "data" / "persisted"
          / "chokepoint-trail.kotoba.edn")


def _trend():
    # climatology (mean of past) systematically UNDER-forecasts a rising series → biased
    return [{":obs/series": "s-x", ":obs/observed-at": t, ":obs/value": float(10 + 2 * t)}
            for t in range(1, 9)]


def test_recalib_params_identity_when_no_residuals():
    assert _recalib_params([]) == (0.0, 1.0)        # nothing learned yet → no correction


def test_recalib_params_bias_is_mean_error():
    bias, infl = _recalib_params([{"error": 2.0, "sd": 1.0}, {"error": 4.0, "sd": 1.0}])
    assert bias == 3.0                               # mean of the residual errors
    assert 0.25 <= infl <= 4.0                       # inflation stays in the clamp band


def test_calibration_reduces_crps_on_a_biased_series():
    raw = backtest_rolling(_trend(), "climatology")
    cal = backtest_calibrated(_trend(), "climatology")
    assert cal["mean_crps"] < raw["mean_crps"]       # bias removal helps


def test_calibration_moves_pit_toward_half():
    raw = backtest_rolling(_trend(), "climatology")["calibration"]["pit_mean"]
    cal = backtest_calibrated(_trend(), "climatology")["calibration"]["pit_mean"]
    assert abs(cal - 0.5) < abs(raw - 0.5)           # better-centered after correction


def test_calibrated_backtest_is_leak_free():
    s = backtest_calibrated(_trend(), "climatology")
    assert s["calibrated"] is True and s["n"] > 0     # score_pair would raise on any leak


def test_runs_over_real_persisted_trail():
    if not _TRAIL.exists():
        return
    rows = load_edn(_TRAIL)
    cal = backtest_calibrated(rows, "climatology")
    raw = backtest_rolling(rows, "climatology")
    assert cal["n"] == raw["n"] and cal["n"] > 0
    # on the real two-regime trail, bias correction still re-centers PIT toward 0.5
    assert abs(cal["calibration"]["pit_mean"] - 0.5) <= abs(raw["calibration"]["pit_mean"] - 0.5)


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"calibrate (forecast.py): {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
