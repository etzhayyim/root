#!/usr/bin/env python3
"""hakoniwa 箱庭 — ensemble → outcome DISTRIBUTION + mitooshi-shaped forecast record.

ADR-2606111500. Turns the raw replica ensemble (simulate.ensemble) into the ONLY thing
hakoniwa asserts: a DISTRIBUTION over the population statistic — quantiles + histogram —
and a forecast record shaped for mitooshi 見通し (ADR-2606051800) proper-scoring.

CONSTITUTIONAL:
  G2 — DISTRIBUTION-ONLY. :forecast/point-asserted is structurally false; there is NO
    :forecast/point field. The p50 is reported as a quantile of the distribution, never as
    "the prediction". 非終末論 made structural.
  G3 — NON-STEERING. :forecast/use is drawn from a RESILIENCE-only enum
    (:resilience :preparedness :robustness :research); trade / wager / position / target /
    manipulate / campaign are NOT representable. A breach raises.
  G7 — LEAK-FREE as-of. The record carries :forecast/as-of; the conditioning info boundary is
    the caller's responsibility (mitooshi scores it leak-free).

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 distribution.py [scenario.edn] [--out OUTDIR] [--steps N] [--replicas K]
"""
from __future__ import annotations
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import world as W  # noqa: E402
import simulate as S  # noqa: E402

# RESILIENCE-only use enum (G3). Steering/speculation uses are NOT members → unrepresentable.
ALLOWED_USE = {":resilience", ":preparedness", ":robustness", ":research"}
HIST_BINS = 10  # over [0,1]


def quantile(sorted_vals, q: float) -> float:
    """Linear-interpolated quantile of an already-sorted list."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(pos)
    frac = pos - lo
    if lo + 1 >= len(sorted_vals):
        return sorted_vals[-1]
    return sorted_vals[lo] * (1 - frac) + sorted_vals[lo + 1] * frac


def histogram(vals, bins=HIST_BINS):
    counts = [0] * bins
    for v in vals:
        b = min(bins - 1, max(0, int(v * bins)))
        counts[b] += 1
    return counts


def distribution(results: list):
    s = sorted(results)
    n = len(s)
    mean = sum(s) / n if n else 0.0
    var = sum((v - mean) ** 2 for v in s) / n if n else 0.0
    return {
        "n": n,
        "mean": mean,
        "stdev": var ** 0.5,
        "quantiles": {":p10": quantile(s, 0.10), ":p25": quantile(s, 0.25),
                      ":p50": quantile(s, 0.50), ":p75": quantile(s, 0.75),
                      ":p90": quantile(s, 0.90)},
        "min": s[0] if s else 0.0,
        "max": s[-1] if s else 0.0,
        "histogram": histogram(s),
    }


def forecast_record(nodes: dict, dist: dict, meta: dict, as_of: str, use: str = ":preparedness"):
    """mitooshi-shaped forecast record — DISTRIBUTION-ONLY (G2), resilience-USE-only (G3)."""
    if use not in ALLOWED_USE:
        raise ValueError(f"G3 violation: :forecast/use {use} is not a resilience use "
                         f"({sorted(ALLOWED_USE)}); steering/speculation is unrepresentable")
    outs = W.outcomes(nodes)
    target = "outcome"
    if outs:
        o = next(iter(outs.values()))
        target = o.get(":sim/label", o.get(":sim/id", "outcome"))
    return {
        ":forecast/actor": ":hakoniwa",
        ":forecast/target": target,
        ":forecast/kind": ":distribution",
        ":forecast/point-asserted": False,        # G2 — structural; there is no point field
        ":forecast/horizon-steps": meta.get("steps"),
        ":forecast/replicas": meta.get("replicas"),
        ":forecast/quantiles": dist["quantiles"],
        ":forecast/histogram": dist["histogram"],
        ":forecast/mean": dist["mean"],
        ":forecast/stdev": dist["stdev"],
        ":forecast/use": use,                     # G3 — resilience-only enum
        ":forecast/as-of": as_of,                 # G7 — leak-free boundary (mitooshi scores it)
        ":forecast/sourced-from": ":hakoniwa-synthetic-ensemble",
    }


def report_md(nodes: dict, dist: dict, meta: dict, as_of: str) -> str:
    L = []
    L.append("# hakoniwa 箱庭 — forward-simulation outcome DISTRIBUTION (never a point)\n")
    L.append("> **G2 — DISTRIBUTION-ONLY.** hakoniwa asserts a distribution over possible "
             "futures, never a single foretold outcome (非終末論). **G1 — every agent is a "
             "SYNTHETIC latent persona**, not a real person (no PII). **G3 — routed to "
             "RESILIENCE / preparedness**, never to trading, targeting, or persuasion.\n")
    outs = W.outcomes(nodes)
    target = next(iter(outs.values())).get(":sim/label", "outcome") if outs else "outcome"
    L.append(f"**Scenario**: {target}")
    L.append(f"**Box**: {meta['personas']} synthetic personas · {meta['edges']} 縁 · "
             f"{meta['steps']} steps × {meta['replicas']} replicas (seed {meta['seed']}, "
             f"jitter {meta['jitter']}) · as-of {as_of}\n")

    q = dist["quantiles"]
    L.append("\n## Outcome distribution — town-wide mean adoption stance\n")
    L.append("| statistic | value |")
    L.append("|---|---:|")
    L.append(f"| mean | {dist['mean']:.4f} |")
    L.append(f"| stdev | {dist['stdev']:.4f} |")
    L.append(f"| p10 | {q[':p10']:.4f} |")
    L.append(f"| p25 | {q[':p25']:.4f} |")
    L.append(f"| **p50 (median, a quantile — NOT 'the prediction')** | {q[':p50']:.4f} |")
    L.append(f"| p75 | {q[':p75']:.4f} |")
    L.append(f"| p90 | {q[':p90']:.4f} |")
    L.append(f"| min / max | {dist['min']:.4f} / {dist['max']:.4f} |")

    L.append("\n## Histogram (10 bins over [0,1])\n")
    L.append("| bin | range | count |")
    L.append("|---:|---|---:|")
    for b, c in enumerate(dist["histogram"]):
        L.append(f"| {b} | [{b/10:.1f}, {(b+1)/10:.1f}) | {c} |")

    L.append("\n## Handoff to mitooshi 見通し\n")
    L.append("_This distribution is handed to mitooshi (ADR-2606051800) as a "
             "`:forecast/kind :distribution` record (`:forecast/point-asserted false`, "
             "`:forecast/use :preparedness`) for leak-free proper-scoring against the realised "
             "outcome. hakoniwa generates the ensemble; mitooshi scores the skill._\n")
    L.append("\n---\n_hakoniwa 箱庭 · ADR-2606111500 · synthetic-persona forward simulation · "
             "distribution-only · resilience-routed · transparent (相互監視). Live large-swarm "
             "runs + any social emission are G8/Council-gated._\n")
    return "\n".join(L)


def _fmt_edn(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, dict):
        return "{" + " ".join(f"{k} {_fmt_edn(val)}" for k, val in v.items()) + "}"
    if isinstance(v, list):
        return "[" + " ".join(_fmt_edn(x) for x in v) + "]"
    return str(v)


def forecast_edn(rec: dict) -> str:
    body = "\n ".join(f"{k} {_fmt_edn(v)}" for k, v in rec.items())
    return (";; hakoniwa 箱庭 — GENERATED mitooshi-shaped forecast record (ADR-2606111500).\n"
            ";; DISTRIBUTION-ONLY (G2): no :forecast/point field exists. resilience-USE-only (G3).\n"
            "{" + body + "}\n")


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    scenario = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-scenario.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])

    def opt(flag, default, cast):
        return cast(argv[argv.index(flag) + 1]) if flag in argv else default

    steps = opt("--steps", S.DEFAULT_STEPS, int)
    replicas = opt("--replicas", S.DEFAULT_REPLICAS, int)
    seed = opt("--seed", S.DEFAULT_SEED, int)
    as_of = opt("--as-of", "2026-06-11T00:00:00Z", str)
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = W.load(scenario)
    results, meta = S.ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
    dist = distribution(results)
    rec = forecast_record(nodes, dist, meta, as_of)

    (outdir / "distribution-report.md").write_text(report_md(nodes, dist, meta, as_of), encoding="utf-8")
    (outdir / "forecast-record.kotoba.edn").write_text(forecast_edn(rec), encoding="utf-8")
    print(f"hakoniwa distribution → {outdir/'distribution-report.md'}")
    print(f"  p10/p50/p90 = {dist['quantiles'][':p10']:.4f} / "
          f"{dist['quantiles'][':p50']:.4f} / {dist['quantiles'][':p90']:.4f} "
          f"(distribution-only, G2)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
