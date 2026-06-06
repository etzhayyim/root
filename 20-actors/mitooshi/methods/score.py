#!/usr/bin/env python3
"""mitooshi 見通し — proper-scoring-rule engine. The empirical heart of the actor.

ADR-2606051800 · vocabulary: forecasting-ontology.kotoba.edn (00-contracts/schemas/).

This is where FACT meets FORECAST and the model error falls out. Given a probabilistic
forecast and the observation that later realized it, it computes the proper scoring
rules that a forecast can be honestly judged by — and refuses to score a pairing that
would leak future information.

  CRPS    — Continuous Ranked Probability Score (Gaussian closed form + ensemble form)
  pinball — quantile / pinball loss (CRPS for a quantile forecast)
  logscore— negative log predictive density
  brier   — categorical / binary
  PIT     — probability integral transform F(y); Uniform(0,1) iff calibrated
  skill   — 1 − score_model / score_baseline; > 0 iff the model beats the baseline

CONSTITUTIONAL framing (enforcement-point of the invariants):
  G5 — leak-free: score_pair() RAISES if obs.observed_at <= forecast.info_as_of. On an
       append-only Datom log a backtest physically cannot see the future; this asserts
       it. Skill is measured against a documented baseline, never cherry-picked.
  G1 — distribution-only: a forecast with point_asserted=True is rejected at the door.
  G12— anti-pseudoscience: a model is "skilled" ONLY if skill > 0 vs a real baseline.

stdlib only (math.erf gives Φ). Lower CRPS / pinball / logscore / brier = better.
Usage:  python3 -m mitooshi.methods.score   (run as a smoke), or import the functions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

_SQRT2 = math.sqrt(2.0)
_SQRT_PI = math.sqrt(math.pi)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)


# ───────────────────────────── normal helpers ──────────────────────────────
def _phi(z: float) -> float:
    """Standard normal pdf."""
    return _INV_SQRT_2PI * math.exp(-0.5 * z * z)


def _Phi(z: float) -> float:
    """Standard normal cdf via erf."""
    return 0.5 * (1.0 + math.erf(z / _SQRT2))


# ───────────────────────────── proper scoring rules ────────────────────────
def gaussian_crps(mu: float, sigma: float, y: float) -> float:
    """CRPS of N(mu, sigma^2) at outcome y (Gneiting & Raftery 2007, closed form).

    CRPS = sigma * [ z*(2*Phi(z) - 1) + 2*phi(z) - 1/sqrt(pi) ],  z = (y - mu)/sigma.
    Always >= 0; equals |y-mu| in the sigma->0 limit (collapses to MAE), which is the
    honest degenerate case — a point forecast scored as a spike. Lower is better.
    """
    if sigma <= 0.0:
        return abs(y - mu)
    z = (y - mu) / sigma
    return sigma * (z * (2.0 * _Phi(z) - 1.0) + 2.0 * _phi(z) - 1.0 / _SQRT_PI)


def gaussian_logscore(mu: float, sigma: float, y: float) -> float:
    """Negative log predictive density of N(mu, sigma^2) at y. Lower is better."""
    if sigma <= 0.0:
        sigma = 1e-9
    return 0.5 * math.log(2.0 * math.pi * sigma * sigma) + (y - mu) ** 2 / (2.0 * sigma * sigma)


def gaussian_pit(mu: float, sigma: float, y: float) -> float:
    """Probability integral transform F(y) for a Gaussian forecast. Uniform iff calibrated."""
    if sigma <= 0.0:
        return 1.0 if y >= mu else 0.0
    return _Phi((y - mu) / sigma)


def pinball_loss(quantiles: dict[float, float], y: float) -> float:
    """Mean pinball / quantile loss over a quantile forecast {level: value}.

    L_tau(q, y) = (y - q)*tau         if y >= q
                = (q - y)*(1 - tau)    otherwise.
    Averaged over the quantile levels, this is a discrete approximation to CRPS. Lower
    is better.
    """
    if not quantiles:
        raise ValueError("pinball_loss: empty quantile forecast")
    total = 0.0
    for tau, q in quantiles.items():
        total += (y - q) * tau if y >= q else (q - y) * (1.0 - tau)
    return total / len(quantiles)


def quantile_pit(quantiles: dict[float, float], y: float) -> float:
    """Approximate PIT for a quantile forecast: the level whose value the outcome sits at.

    Linear-interpolates between the bracketing quantiles; clamps to [0,1] outside the
    forecast's quantile span (an honest tail-miss reads as 0 or 1).
    """
    items = sorted(quantiles.items())
    if y <= items[0][1]:
        return 0.0
    if y >= items[-1][1]:
        return 1.0
    for (t0, q0), (t1, q1) in zip(items, items[1:]):
        if q0 <= y <= q1:
            if q1 == q0:
                return t0
            return t0 + (t1 - t0) * (y - q0) / (q1 - q0)
    return 0.5


def ensemble_crps(members: list[float], y: float) -> float:
    """CRPS of an ensemble forecast {x_1..x_m} at outcome y — the empirical (energy) form:

        CRPS = (1/m) Σ|x_i − y|  −  1/(2 m²) ΣΣ|x_i − x_j|.

    The first term rewards closeness to the fact; the second rewards (subtracts) ensemble
    spread, so a confident-and-right ensemble beats a vague one. Lower is better; reduces
    to |x−y| for a 1-member ensemble (a point forecast scored honestly as a spike).
    """
    m = len(members)
    if m == 0:
        raise ValueError("ensemble_crps: empty ensemble")
    term1 = sum(abs(x - y) for x in members) / m
    term2 = sum(abs(a - b) for a in members for b in members) / (2.0 * m * m)
    return term1 - term2


def ensemble_pit(members: list[float], y: float) -> float:
    """PIT-analogue for an ensemble: the fraction of members at or below the outcome.
    Uniform over the ensemble ranks iff calibrated."""
    m = len(members)
    if m == 0:
        raise ValueError("ensemble_pit: empty ensemble")
    return sum(1 for x in members if x <= y) / m


def brier_score(probs: dict[str, float], realized_class: str) -> float:
    """Multi-class Brier score: sum_k (p_k - o_k)^2, o_k = 1 for the realized class.

    Ranges [0, 2]; 0 = a perfect confident correct forecast. Lower is better.
    """
    if not probs:
        raise ValueError("brier_score: empty categorical forecast")
    total = 0.0
    classes = set(probs) | {realized_class}
    for c in classes:
        o = 1.0 if c == realized_class else 0.0
        total += (probs.get(c, 0.0) - o) ** 2
    return total


def categorical_logscore(probs: dict[str, float], realized_class: str) -> float:
    """Negative log probability assigned to the realized class. Lower is better."""
    p = max(probs.get(realized_class, 0.0), 1e-12)
    return -math.log(p)


def categorical_pit(probs: dict[str, float], realized_class: str) -> float:
    """A PIT-analogue for a categorical forecast: the probability mass at-or-below the
    realized class under the natural ordering of class keys (calibration proxy)."""
    items = sorted(probs.items())
    cum = 0.0
    for c, p in items:
        cum += p
        if c == realized_class:
            return cum
    return cum


# ───────────────────────────── baselines (the skill yardstick) ─────────────
def climatology_gaussian(history: list[float]) -> tuple[float, float]:
    """Climatology baseline: forecast = N(historical mean, historical sd)."""
    if not history:
        raise ValueError("climatology needs history")
    n = len(history)
    mu = sum(history) / n
    var = sum((x - mu) ** 2 for x in history) / max(n - 1, 1)
    return mu, math.sqrt(var) if var > 0 else 1e-9


def persistence_gaussian(history: list[float], spread: float | None = None) -> tuple[float, float]:
    """Persistence baseline: forecast = last value, sd = stdev of first differences."""
    if not history:
        raise ValueError("persistence needs history")
    mu = history[-1]
    if spread is not None:
        return mu, max(spread, 1e-9)
    if len(history) < 2:
        return mu, 1e-9
    diffs = [history[i] - history[i - 1] for i in range(1, len(history))]
    md = sum(diffs) / len(diffs)
    var = sum((d - md) ** 2 for d in diffs) / max(len(diffs) - 1, 1)
    return mu, math.sqrt(var) if var > 0 else 1e-9


def skill_score(model_score: float, baseline_score: float) -> float:
    """Skill = 1 - model/baseline. > 0 ⇔ the model beats the baseline. The G12 gate:
    a model is only ever "skilled" when this is positive against a real baseline."""
    if baseline_score == 0.0:
        return 0.0 if model_score == 0.0 else float("-inf")
    return 1.0 - model_score / baseline_score


# ───────────────────────────── the leak-free pair scorer ───────────────────
@dataclass
class Forecast:
    fid: str
    dist_kind: str                       # gaussian | quantile | categorical
    info_as_of: int                      # G5 — latest ts the forecaster could see
    use: str = "resilience"              # G2 — must be in the allowed set
    point_asserted: bool = False         # G1 — must be False
    mean: float = 0.0
    sd: float = 1.0
    quantiles: dict[float, float] = field(default_factory=dict)
    probs: dict[str, float] = field(default_factory=dict)
    members: list[float] = field(default_factory=list)


@dataclass
class Observation:
    oid: str
    observed_at: int                     # G5 — must be strictly after info_as_of
    value: float = 0.0
    cls: str = ""


ALLOWED_USE = (":resilience", ":planning", ":nowcast", ":early-warning", ":research",
               "resilience", "planning", "nowcast", "early-warning", "research")


def score_pair(fc: Forecast, obs: Observation) -> dict[str, float]:
    """Score one forecast against the observation that realized it. RAISES on a charter
    violation (G1 point-assertion, G2 illegal use, G5 look-ahead leak)."""
    # G1 — distribution-only.
    if fc.point_asserted:
        raise ValueError(f"G1: forecast {fc.fid!r} asserts a deterministic point; unrepresentable (非終末論)")
    # G2 — non-speculative use.
    if fc.use not in ALLOWED_USE:
        raise ValueError(f"G2: forecast {fc.fid!r} use {fc.use!r} not in the non-speculative set {ALLOWED_USE[:5]}")
    # G5 — leak-free: the outcome must arrive STRICTLY AFTER the forecaster's info.
    if obs.observed_at <= fc.info_as_of:
        raise ValueError(
            f"G5 LEAK: obs {obs.oid!r} observed_at={obs.observed_at} is not strictly "
            f"after forecast {fc.fid!r} info_as_of={fc.info_as_of}; scoring would see the future"
        )

    out: dict[str, float] = {}
    if fc.dist_kind in ("gaussian", ":gaussian"):
        out["crps"] = gaussian_crps(fc.mean, fc.sd, obs.value)
        out["log_score"] = gaussian_logscore(fc.mean, fc.sd, obs.value)
        out["pit"] = gaussian_pit(fc.mean, fc.sd, obs.value)
    elif fc.dist_kind in ("quantile", ":quantile"):
        out["pinball"] = pinball_loss(fc.quantiles, obs.value)
        out["pit"] = quantile_pit(fc.quantiles, obs.value)
    elif fc.dist_kind in ("categorical", ":categorical"):
        out["brier"] = brier_score(fc.probs, obs.cls)
        out["log_score"] = categorical_logscore(fc.probs, obs.cls)
        out["pit"] = categorical_pit(fc.probs, obs.cls)
    elif fc.dist_kind in ("ensemble", ":ensemble"):
        out["crps"] = ensemble_crps(fc.members, obs.value)
        out["pit"] = ensemble_pit(fc.members, obs.value)
    else:
        raise ValueError(f"unknown dist_kind {fc.dist_kind!r}")
    return out


# ───────────────────────────── calibration over a set of PITs ──────────────
def calibration_summary(pit_values: list[float], bins: int = 10) -> dict:
    """Reliability of a set of forecasts via their PIT histogram.

    For a calibrated forecaster PIT ~ Uniform(0,1): mean ≈ 0.5 and each of `bins` bins
    holds ≈ 1/bins of the mass. `deviation` is the L1 distance of the observed bin
    frequencies from uniform (0 = perfect, up to ~2 = pathological); it is the signal
    the calibration_gate refuses promotion on.
    """
    if not pit_values:
        return {"n": 0, "pit_mean": 0.5, "deviation": 0.0, "hist": []}
    n = len(pit_values)
    counts = [0] * bins
    for p in pit_values:
        idx = min(int(max(0.0, min(1.0, p)) * bins), bins - 1)
        counts[idx] += 1
    freqs = [c / n for c in counts]
    expected = 1.0 / bins
    deviation = sum(abs(f - expected) for f in freqs)
    return {
        "n": n,
        "pit_mean": sum(pit_values) / n,
        "deviation": deviation,
        "hist": freqs,
    }


def score_set(pairs: list[tuple[Forecast, Observation]],
              baseline: list[dict[str, float]] | None = None) -> dict:
    """Aggregate a set of leak-checked pairs into a scorecard + calibration + (optional)
    skill vs a parallel baseline score list. The model is `skilled` only if mean skill
    on the primary metric is > 0 (G12)."""
    rows = [score_pair(fc, obs) for fc, obs in pairs]
    metrics = ("crps", "pinball", "log_score", "brier")
    agg: dict[str, float] = {}
    for m in metrics:
        vals = [r[m] for r in rows if m in r]
        if vals:
            agg[m] = sum(vals) / len(vals)
    pit_vals = [r["pit"] for r in rows if "pit" in r]
    calib = calibration_summary(pit_vals)

    skilled = None
    skill = None
    if baseline:
        primary = "crps" if "crps" in agg else ("pinball" if "pinball" in agg else "brier" if "brier" in agg else None)
        if primary:
            b_vals = [b[primary] for b in baseline if primary in b]
            if b_vals:
                b_mean = sum(b_vals) / len(b_vals)
                skill = skill_score(agg[primary], b_mean)
                skilled = skill > 0.0
    return {
        "n": len(rows),
        "metrics": agg,
        "calibration": calib,
        "skill": skill,
        "skilled": skilled,
        "rows": rows,
    }


if __name__ == "__main__":  # tiny self-smoke
    fc = Forecast("f1", "gaussian", info_as_of=100, mean=10.0, sd=2.0)
    ob = Observation("o1", observed_at=101, value=11.0)
    print("CRPS:", round(gaussian_crps(10.0, 2.0, 11.0), 4))
    print("pair:", {k: round(v, 4) for k, v in score_pair(fc, ob).items()})
