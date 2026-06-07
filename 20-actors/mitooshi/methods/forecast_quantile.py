#!/usr/bin/env python3
"""mitooshi 見通し — quantile (pinball-scored) forecaster (R1, offline).

ADR-2606051800. A second forecaster family alongside the Gaussian baselines in forecast.py:
emit a forecast as a set of QUANTILES (e.g. 10/50/90) rather than a mean±sd, and score it
with the pinball (quantile) loss already in score.py. Same constitutional invariants:

  G1 distribution-only — dist_kind="quantile", point_asserted=False; a spread of quantiles is
                         a distribution, never a single asserted future.
  G2 non-speculative   — use=":resilience".
  G5 leak-free         — uses ONLY observations strictly before target_at; score_pair RAISES
                         on a look-ahead leak (inherited from score.py).
  G12 anti-pseudoscience — skill is pinball vs a documented persistence baseline, not
                         cherry-picked accuracy; :skilled only when it beats the baseline.

stdlib only. Usage:
    python3 forecast_quantile.py   # self-test
"""
from __future__ import annotations

import sys

try:
    from analyze import _empirical_quantiles
    from score import Forecast, Observation, pinball_loss, score_pair, skill_score
except ImportError:
    from mitooshi.methods.analyze import _empirical_quantiles  # type: ignore
    from mitooshi.methods.score import (  # type: ignore
        Forecast, Observation, pinball_loss, score_pair, skill_score)

DEFAULT_LEVELS = (0.1, 0.5, 0.9)


def forecast_next_quantile(sid: str, history, target_at: int,
                           levels=DEFAULT_LEVELS) -> Forecast | None:
    """Forecast series `sid` at `target_at` as empirical QUANTILES of the prior values
    (leak-free — only observations strictly before target_at). None if no prior history."""
    prior = [(t, v) for (t, v) in history if t < target_at]
    if not prior:
        return None
    values = [v for _t, v in prior]
    info_as_of = max(t for t, _v in prior)               # G5
    q = _empirical_quantiles(values, levels)
    return Forecast(fid=f"fc.{sid}.{target_at}.quantile", dist_kind="quantile",
                    info_as_of=info_as_of, use=":resilience", point_asserted=False,
                    quantiles=q)


def _persistence_quantiles(values, levels) -> dict:
    """Documented naive baseline: every quantile = the last observed value (no spread).
    A 'tomorrow = today, with certainty' straw man the real forecaster must beat (G12)."""
    last = values[-1]
    return {float(tau): float(last) for tau in levels}


def score_quantile(fc: Forecast, y: float, observed_at: int) -> dict:
    """Score a quantile forecast against the realizing value (leak-checked by score_pair)."""
    return score_pair(fc, Observation(oid=f"o.{fc.fid}", observed_at=observed_at, value=y))


def forecast_quantile_trail(rows: list[dict], target_at: int,
                            levels=DEFAULT_LEVELS) -> list[dict]:
    """Forecast every series at target_at as quantiles; when the realizing obs is already in
    the trail, score pinball + skill vs the persistence-quantile baseline (G12)."""
    from collections import defaultdict
    hist: dict = defaultdict(list)
    actual: dict = {}
    for r in rows:
        if ":obs/series" in r and ":obs/observed-at" in r:
            hist[r[":obs/series"]].append((int(r[":obs/observed-at"]), float(r[":obs/value"])))
            actual[(r[":obs/series"], int(r[":obs/observed-at"]))] = float(r[":obs/value"])
    out: list = []
    for sid, h in sorted(hist.items()):
        h.sort()
        fc = forecast_next_quantile(sid, h, target_at, levels)
        if fc is None:
            continue
        row: dict = {"series": sid, "forecast": fc}
        if (sid, target_at) in actual:
            y = actual[(sid, target_at)]
            s = score_quantile(fc, y, target_at)            # raises on G5 leak
            prior = [v for t, v in h if t < target_at]
            base = pinball_loss(_persistence_quantiles(prior, levels), y)
            row["pinball"] = round(s["pinball"], 6)
            row["baseline_pinball"] = round(base, 6)
            row["skill"] = round(skill_score(s["pinball"], base), 4)
            row["skilled"] = bool(s["pinball"] < base)       # G12: only if it beats baseline
        out.append(row)
    return out


def _run() -> bool:
    # rising series 1..7; forecast quantiles at t=7 from history t<7, score against y=24
    hist = [(t, float(10 + 2 * t)) for t in range(1, 7)]
    fc = forecast_next_quantile("s-x", hist, target_at=7)
    assert fc is not None and fc.dist_kind == "quantile" and fc.point_asserted is False
    assert fc.use == ":resilience" and fc.info_as_of == 6      # G5
    qs = sorted(fc.quantiles.items())
    assert qs[0][1] <= qs[1][1] <= qs[2][1]                    # monotone quantiles
    s = score_quantile(fc, 24.0, 7)
    assert "pinball" in s and "pit" in s
    rows = ([{":obs/series": "s-x", ":obs/observed-at": t, ":obs/value": float(10 + 2 * t)}
             for t in range(1, 8)])
    trail = forecast_quantile_trail(rows, target_at=7)
    assert trail and "skill" in trail[0]
    print("forecast_quantile.py: self-test passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
