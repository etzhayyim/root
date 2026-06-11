#!/usr/bin/env python3
"""Tests for mitooshi rolling-origin backtest (methods/forecast.py backtest functions).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_backtest.py
    python3 test_backtest.py

The honest skill answer is over ALL origins, leak-free at each — not a single cherry-picked
target. This proves the rolling backtest is leak-free per origin, that persistence beats
climatology on a trend across origins, and that the scorecard EDN carries the G5/G12/G10
markers and per-method aggregate skill.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from forecast import backtest_rolling, compare_methods, emit_scorecard_edn, series_histories
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.forecast import (  # type: ignore
        backtest_rolling, compare_methods, emit_scorecard_edn, series_histories)
    from mitooshi.methods.analyze import load_edn  # type: ignore

_TRAIL = (pathlib.Path(__file__).resolve().parent.parent / "data" / "persisted"
          / "chokepoint-trail.kotoba.edn")


def _trend():
    # clear upward trend over 7 origins → persistence should win across origins
    return [{":obs/series": "s-x", ":obs/observed-at": t, ":obs/value": float(10 + 2 * t)}
            for t in range(1, 8)]


def _noisy_flat():
    # mean-reverting noise around a level → climatology should be competitive
    vals = [5.0, 5.4, 4.7, 5.1, 4.9, 5.2, 5.0]
    return [{":obs/series": "s-y", ":obs/observed-at": i + 1, ":obs/value": v}
            for i, v in enumerate(vals)]


def test_backtest_scores_every_origin_after_first():
    s = backtest_rolling(_trend(), "persistence")
    # 7 observations → 6 scoreable origins (origin 1 has no prior history)
    assert len(s["per_origin"]) == 6
    assert all(o["target_at"] >= 2 for o in s["per_origin"])


def test_backtest_is_leak_free_no_raise():
    # score_pair raises on any leak; a clean run over all origins proves leak-freedom
    s = backtest_rolling(_trend(), "climatology")
    assert s["n"] > 0 and s["mean_crps"] is not None


def test_persistence_beats_climatology_across_origins_on_trend():
    comp = compare_methods(_trend())
    assert comp["persistence"]["mean_crps"] < comp["climatology"]["mean_crps"]
    assert comp["persistence"]["mean_skill"] > 0      # G12 skilled vs climatology baseline


def test_calibration_summary_present():
    s = backtest_rolling(_noisy_flat(), "climatology")
    cal = s["calibration"]
    assert 0.0 <= cal["pit_mean"] <= 1.0 and cal["n"] == s["n"]


def test_scorecard_edn_marks_invariants_and_methods():
    edn = emit_scorecard_edn(compare_methods(_trend()))
    assert ":fc.score/method :persistence" in edn and ":fc.score/method :climatology" in edn
    assert "leak-free" in edn and "G10-gated" in edn and ":fc.score/mean-skill" in edn


def test_runs_over_real_persisted_trail():
    if not _TRAIL.exists():
        return
    rows = load_edn(_TRAIL)
    comp = compare_methods(rows)
    assert comp["climatology"]["n"] > 0 and comp["persistence"]["n"] > 0


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"backtest (forecast.py): {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
