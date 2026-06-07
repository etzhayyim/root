#!/usr/bin/env python3
"""Tests for the mitooshi quantile forecaster (methods/forecast_quantile.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_forecast_quantile.py
    python3 test_forecast_quantile.py

Verifies: distribution-only (G1), resilience use (G2), leak-free (G5), monotone quantiles,
pinball scoring + skill vs a documented persistence baseline (G12).
"""
from __future__ import annotations

import sys

try:
    from forecast_quantile import (forecast_next_quantile, forecast_quantile_trail,
                                   score_quantile, DEFAULT_LEVELS)
except ImportError:
    from mitooshi.methods.forecast_quantile import (  # type: ignore
        forecast_next_quantile, forecast_quantile_trail, score_quantile, DEFAULT_LEVELS)


def _rising():
    return [(t, float(10 + 2 * t)) for t in range(1, 8)]   # t=1..7


def test_forecast_is_quantile_distribution_g1():
    fc = forecast_next_quantile("s-x", _rising(), target_at=7)
    assert fc is not None
    assert fc.dist_kind == "quantile"
    assert fc.point_asserted is False               # G1
    assert fc.use == ":resilience"                  # G2
    assert set(fc.quantiles.keys()) == set(DEFAULT_LEVELS)


def test_quantiles_are_monotone():
    fc = forecast_next_quantile("s-x", _rising(), target_at=7)
    vals = [fc.quantiles[tau] for tau in sorted(fc.quantiles)]
    assert vals == sorted(vals)                      # q10 <= q50 <= q90


def test_leak_free_info_before_target_g5():
    fc = forecast_next_quantile("s-x", _rising(), target_at=7)
    assert fc.info_as_of < 7                          # G5 — only prior history
    s = score_quantile(fc, 24.0, 7)                   # obs strictly after info → no raise
    assert "pinball" in s


def test_no_prior_history_returns_none():
    assert forecast_next_quantile("s-x", [(7, 24.0)], target_at=7) is None


def test_trail_scores_pinball_and_skill_g12():
    rows = [{":obs/series": "s-x", ":obs/observed-at": t, ":obs/value": float(10 + 2 * t)}
            for t in range(1, 8)]
    trail = forecast_quantile_trail(rows, target_at=7)
    assert len(trail) == 1
    r = trail[0]
    assert "pinball" in r and "baseline_pinball" in r and "skill" in r
    assert isinstance(r["skilled"], bool)             # G12: only skilled if it beats baseline


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"forecast_quantile.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
