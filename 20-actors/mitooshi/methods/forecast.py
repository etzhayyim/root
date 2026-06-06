#!/usr/bin/env python3
"""mitooshi 見通し — baseline forecasts from the persisted chokepoint trail (R1, offline).

ADR-2606051800. `persist.py` accumulates an append-only as-of observation trail
(:series + :obs over observed-at). This module CLOSES the loop: it forecasts the next
value of each chokepoint series as a DISTRIBUTION (G1 — never a point), using ONLY the
observations strictly before the target time (G5 leak-free), and — when the realizing
observation is already in the trail — scores the forecast against it with proper scoring
rules and reports skill vs the climatology baseline (G12).

observe (watari/watatsuna) → bridge → persist → **forecast** — all on the kotoba Datom
log, leak-free by construction (an append-only log makes look-ahead structurally
impossible: info-as-of < observed-at is enforced by score_pair).

Forecasts are emitted as :forecast datoms (`:forecast/point-asserted false`, distribution
parameters, `:forecast/use :resilience`) — the exact records a live promotion would append,
G10-gated for live ingest.

stdlib only. Usage:
    python3 forecast.py --trail ../data/persisted/chokepoint-trail.kotoba.edn --at 7 \
                        [--method climatology|persistence] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import load_edn
    from score import (Forecast, Observation, calibration_summary, climatology_gaussian,
                       gaussian_crps, persistence_gaussian, score_pair, skill_score)
except ImportError:
    from mitooshi.methods.analyze import load_edn  # type: ignore
    from mitooshi.methods.score import (  # type: ignore
        Forecast, Observation, calibration_summary, climatology_gaussian,
        gaussian_crps, persistence_gaussian, score_pair, skill_score)

METHODS = ("climatology", "persistence")


def series_histories(rows: list[dict]) -> dict[str, list[tuple[int, float]]]:
    """{series_id: [(observed_at, value), ...] sorted by observed_at} from a trail."""
    hist: dict[str, list[tuple[int, float]]] = {}
    for r in rows:
        if ":obs/series" in r and ":obs/observed-at" in r:
            hist.setdefault(r[":obs/series"], []).append(
                (int(r[":obs/observed-at"]), float(r[":obs/value"])))
    for sid in hist:
        hist[sid].sort()
    return hist


def forecast_next(sid: str, history: list[tuple[int, float]], target_at: int,
                  method: str = "climatology") -> Forecast | None:
    """Forecast series `sid` at `target_at` as a Gaussian distribution, using ONLY
    observations strictly before target_at (leak-free). Returns None if no prior history."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    prior = [(t, v) for (t, v) in history if t < target_at]
    if not prior:
        return None
    values = [v for _t, v in prior]
    info_as_of = max(t for t, _v in prior)            # G5 — newest fact the forecaster saw
    if method == "climatology":
        mu, sd = climatology_gaussian(values)
    else:
        mu, sd = persistence_gaussian(values)
    return Forecast(fid=f"fc.{sid}.{target_at}.{method}", dist_kind="gaussian",
                    info_as_of=info_as_of, use=":resilience", point_asserted=False,
                    mean=round(mu, 4), sd=round(sd, 6))


def forecast_trail(rows: list[dict], target_at: int, method: str = "climatology") -> list[dict]:
    """Forecast every series at target_at; score leak-free against the realizing obs if
    it is already in the trail. Returns rows: {series, forecast, [crps, climatology_crps,
    skill]}."""
    hist = series_histories(rows)
    actual = {(r[":obs/series"], int(r[":obs/observed-at"])): float(r[":obs/value"])
              for r in rows if ":obs/series" in r and ":obs/observed-at" in r}
    out: list[dict] = []
    for sid, h in sorted(hist.items()):
        fc = forecast_next(sid, h, target_at, method)
        if fc is None:
            continue
        row: dict = {"series": sid, "forecast": fc}
        if (sid, target_at) in actual:
            y = actual[(sid, target_at)]
            obs = Observation(oid=f"obs.{sid}.{target_at}", observed_at=target_at, value=y)
            s = score_pair(fc, obs)                       # raises on a G5 leak
            row["crps"] = round(s["crps"], 6)
            # skill vs the climatology baseline built from the same leak-free history
            prior = [v for t, v in h if t < target_at]
            cmu, csd = climatology_gaussian(prior)
            base = gaussian_crps(cmu, csd, y)
            row["climatology_crps"] = round(base, 6)
            row["skill"] = round(skill_score(s["crps"], base), 4)
        out.append(row)
    return out


def backtest_rolling(rows: list[dict], method: str = "climatology") -> dict:
    """Rolling-origin backtest: at EVERY observed-at origin (after the first), forecast
    each series from history strictly before it and score against the realized obs. This
    is the leak-free, all-origins answer to "does this method have skill?" — not a single
    cherry-picked target. Returns {method, n, mean_crps, mean_skill, calibration, per_origin}.
    """
    hist = series_histories(rows)
    targets = sorted({t for pairs in hist.values() for t, _v in pairs})
    crps_all, skill_all, pit_all = [], [], []
    per_origin: list[dict] = []
    for target_at in targets[1:]:                     # skip the first (no prior history)
        scored = [r for r in forecast_trail(rows, target_at, method) if "crps" in r]
        if not scored:
            continue
        o_crps = [r["crps"] for r in scored]
        o_skill = [r["skill"] for r in scored]
        crps_all += o_crps
        skill_all += o_skill
        for r in scored:                              # collect PIT for calibration
            fc, h = r["forecast"], hist[r["series"]]
            y = next(v for t, v in h if t == target_at)
            pit_all.append(score_pair(fc, Observation(oid="o", observed_at=target_at, value=y))["pit"])
        per_origin.append({"target_at": target_at, "n": len(scored),
                           "mean_crps": round(sum(o_crps) / len(o_crps), 6),
                           "mean_skill": round(sum(o_skill) / len(o_skill), 4)})
    n = len(crps_all)
    return {
        "method": method, "n": n,
        "mean_crps": round(sum(crps_all) / n, 6) if n else None,
        "mean_skill": round(sum(skill_all) / n, 4) if n else None,
        "calibration": calibration_summary(pit_all),
        "per_origin": per_origin,
    }


def compare_methods(rows: list[dict]) -> dict:
    """Rolling-origin backtest for every method → {method: summary}. The honest, all-origins
    method comparison (no cherry-picked target, leak-free at each origin)."""
    return {m: backtest_rolling(rows, m) for m in METHODS}


def emit_scorecard_edn(comparison: dict) -> str:
    L = [";; chokepoint-backtest-scorecard.kotoba.edn — ROLLING-ORIGIN leak-free backtest.",
         ";; Aggregate skill vs climatology over ALL origins (no cherry-picked target).",
         ";; G5 leak-free at each origin; G12 skill vs a documented baseline. DERIVED",
         ";; :representative. Live promotion G10-gated. ADR-2606051800.", "", "["]
    for m, s in sorted(comparison.items()):
        cal = s["calibration"]
        L.append(
            f' {{:fc.score/method :{m} :fc.score/n {s["n"]} '
            f':fc.score/mean-crps {s["mean_crps"]} :fc.score/mean-skill {s["mean_skill"]} '
            f':fc.score/pit-mean {round(cal["pit_mean"], 4)} '
            f':fc.score/calibration-deviation {round(cal["deviation"], 4)} '
            f':fc.score/sourcing :representative}}')
    L.append("]")
    return "\n".join(L) + "\n"


def emit_forecast_edn(forecasts: list[dict], target_at: int, method: str) -> str:
    L = [f";; chokepoint-forecast.kotoba.edn — DISTRIBUTION forecasts @ target={target_at} ({method}).",
         ";; G1 distribution-only (:forecast/point-asserted false, 非終末論). G5 leak-free",
         ";; (info-as-of < target). DERIVED :representative. Live promotion G10-gated. ADR-2606051800.",
         "", "["]
    for row in forecasts:
        fc = row["forecast"]
        L.append(
            f' {{:forecast/id "{fc.fid}" :forecast/series "{row["series"]}" '
            f':forecast/dist :gaussian :forecast/point-asserted false :forecast/use :resilience '
            f':forecast/info-as-of {fc.info_as_of} :forecast/target-at {target_at} '
            f':forecast/mean {fc.mean} :forecast/sd {fc.sd} :forecast/sourcing :representative}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    if "--trail" not in argv or ("--at" not in argv and "--backtest" not in argv):
        sys.exit(__doc__)
    trail = pathlib.Path(argv[argv.index("--trail") + 1])
    target_at = int(argv[argv.index("--at") + 1]) if "--at" in argv else 0
    method = argv[argv.index("--method") + 1] if "--method" in argv else "climatology"

    rows = load_edn(trail)

    if "--backtest" in argv:
        comp = compare_methods(rows)
        if "--out" in argv:
            outdir = pathlib.Path(argv[argv.index("--out") + 1])
            outdir.mkdir(parents=True, exist_ok=True)
            (outdir / "chokepoint-backtest-scorecard.kotoba.edn").write_text(emit_scorecard_edn(comp))
        print("mitooshi rolling-origin backtest (leak-free at each origin):")
        for m, s in sorted(comp.items()):
            print(f"  {m:12s} n={s['n']:3d}  mean-CRPS={s['mean_crps']}  "
                  f"mean-skill={s['mean_skill']:+}  PIT-mean={round(s['calibration']['pit_mean'], 3)}")
        return 0

    fcs = forecast_trail(rows, target_at, method)
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "chokepoint-forecast.kotoba.edn").write_text(
            emit_forecast_edn(fcs, target_at, method))

    scored = [r for r in fcs if "crps" in r]
    print(f"mitooshi forecast @ target={target_at} ({method}): {len(fcs)} series forecast, "
          f"{len(scored)} scored leak-free against the realized obs")
    for r in fcs:
        fc = r["forecast"]
        tail = (f"  CRPS {r['crps']} vs climatology {r['climatology_crps']} "
                f"(skill {r['skill']:+})") if "crps" in r else "  (no realized obs yet)"
        print(f"  {r['series']}: N(μ={fc.mean}, σ={fc.sd}) info-as-of={fc.info_as_of}{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
