#!/usr/bin/env python3
"""mitooshi 見通し — multi-horizon skill-decay analysis.

ADR-2606051800. A real forecaster predicts at MANY lead times, and its skill decays as the
horizon grows — eventually a long-range forecast can do no better than climatology. This
module demonstrates that property honestly on a mean-reverting AR(1) process, scoring a
leak-free h-step forecaster against the climatology baseline at each horizon h = 1..H.

  AR(1):  y_t = μ + φ·(y_{t-1} − μ) + ε_t          (φ = 0.7, mean-reverting)
  optimal h-step mean:  μ + φ^h·(y_t − μ)  →  μ as h→∞   (reverts to the climatology mean)
  h-step sd:  σ_ε·sqrt((1 − φ^{2h})/(1 − φ²))  →  the unconditional σ as h→∞

So at short horizon the forecast uses recent state and beats climatology; at long horizon it
becomes climatology, and skill → 0. That decay is the thing this prints — and the thing that
keeps mitooshi honest about how far ahead it can usefully see (it never claims a flat-skill
crystal ball; 非終末論).

stdlib only. Usage:  python3 horizon.py [--out OUTDIR]
"""
from __future__ import annotations

import math
import pathlib
import sys

try:
    from score import Forecast, Observation, gaussian_crps, score_pair, skill_score
except ImportError:
    from mitooshi.methods.score import (  # type: ignore
        Forecast, Observation, gaussian_crps, score_pair, skill_score,
    )

MU = 10.0
PHI = 0.9                       # strong mean-reversion → clear short-horizon predictability
SIGMA_E = 1.0
SIGMA_UNCOND = SIGMA_E / math.sqrt(1.0 - PHI * PHI)


def _innov(t: int) -> float:
    """Deterministic, non-repeating, ~zero-mean innovation (no RNG — reproducible)."""
    return 1.1 * math.sin(2.3 * t) + 0.7 * math.cos(0.9 * t + 1.0) - 0.5 * math.sin(0.37 * t)


def build_path(n: int) -> list[float]:
    y = [MU]
    for t in range(1, n):
        y.append(MU + PHI * (y[-1] - MU) + _innov(t))
    return y


def _model_forecast(y_t: float, h: int) -> tuple[float, float]:
    mean = MU + (PHI ** h) * (y_t - MU)
    var = SIGMA_E * SIGMA_E * (1.0 - PHI ** (2 * h)) / (1.0 - PHI * PHI)
    return mean, math.sqrt(var)


def horizon_skill(n: int = 160, horizons=(1, 3, 6, 12)) -> list[dict]:
    """For each horizon, mean CRPS of the AR(1) forecaster vs the climatology baseline,
    aggregated leak-free over all valid origins. Returns one row per horizon."""
    y = build_path(n)
    rows = []
    for h in horizons:
        model_crps, clim_crps = [], []
        for t in range(2, n - h):           # origin t sees y[0..t]; target t+h is strictly after
            target = t + h
            yt = y[target]
            mu, sd = _model_forecast(y[t], h)
            fc = Forecast(f"f{t}.{h}", "gaussian", info_as_of=t, mean=mu, sd=sd)
            sc = score_pair(fc, Observation(f"o{target}", observed_at=target, value=yt))  # leak-checked
            model_crps.append(sc["crps"])
            clim_crps.append(gaussian_crps(MU, SIGMA_UNCOND, yt))   # climatology baseline
        mc = sum(model_crps) / len(model_crps)
        cc = sum(clim_crps) / len(clim_crps)
        rows.append({"h": h, "mean_crps": mc, "clim_crps": cc,
                     "skill_vs_clim": skill_score(mc, cc), "n": len(model_crps)})
    return rows


def render_md(rows: list[dict]) -> str:
    L = [f"# mitooshi 見通し — multi-horizon skill decay (AR(1), φ={PHI})", "",
         "_Skill vs climatology decays as the lead time grows — a long-range forecast eventually_",
         "_does no better than the climatological mean. mitooshi never claims flat-skill foresight (非終末論)._", "",
         "| horizon h | mean CRPS | climatology CRPS | skill vs clim | n |",
         "|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['h']} | {r['mean_crps']:.4f} | {r['clim_crps']:.4f} | {r['skill_vs_clim']:.4f} | {r['n']} |")
    L += ["", "→ CRPS rises and skill falls with horizon; the useful-foresight range is where skill > 0.", ""]
    return "\n".join(L)


def main(argv: list[str]) -> int:
    rows = horizon_skill()
    print(f"mitooshi multi-horizon skill (AR(1), φ={PHI}):")
    for r in rows:
        print(f"  h={r['h']}: CRPS={r['mean_crps']:.4f} skill_vs_clim={r['skill_vs_clim']:.4f}")
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "horizon-skill.md").write_text(render_md(rows))
        print(f"  → {outdir/'horizon-skill.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
