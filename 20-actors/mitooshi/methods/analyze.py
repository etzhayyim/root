#!/usr/bin/env python3
"""mitooshi 見通し — forecasting-observatory backtest analyzer.

ADR-2606051800 · vocabulary: forecasting-ontology.kotoba.edn (00-contracts/schemas/).

Reads a kotoba-EDN forecasting graph (:series/* :obs/* :forecast/* :fc.model/*
:baseline/*) and emits:

  1. an aggregate-first scorecard (out/scorecard.md): per-model mean CRPS / log-score,
     calibration (PIT mean + deviation), and SKILL vs the climatology + persistence
     baselines — the honest answer to "how wrong is the model, measured against fact".
  2. the derived score datoms (out/forecast-scorecard.kotoba.edn), flagged :derived —
     never re-ingested as authoritative fact.

It joins FACT to FORECAST leak-free: each forecast is scored only against the observation
whose :obs/observed-at is STRICTLY AFTER the forecast's :info-as-of (methods/score.py
raises otherwise). Baselines are built using ONLY observations the forecaster could see
(observed-at ≤ info-as-of), so the skill comparison is itself leak-free.

stdlib only. Usage:  python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import re
import sys

try:
    from score import (
        Forecast, Observation, brier_score, calibration_summary, climatology_gaussian,
        ensemble_crps, gaussian_crps, persistence_gaussian, pinball_loss, score_pair, skill_score,
    )
except ImportError:
    from mitooshi.methods.score import (  # type: ignore
        Forecast, Observation, brier_score, calibration_summary, climatology_gaussian,
        ensemble_crps, gaussian_crps, persistence_gaussian, pinball_loss, score_pair, skill_score,
    )

from collections import Counter

# ── minimal EDN reader (subset: [] {} :kw "str" num bool nil) — ported from hotaru/nusa
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while True:
            t2 = next(it)
            if t2 == ']':
                return out
            out.append(_parse_from(t2, it))
    if t == '{':
        out = {}
        while True:
            t2 = next(it)
            if t2 == '}':
                return out
            k = _parse_from(t2, it)
            v = _parse(it)
            out[k] = v
        return out
    return _atom(t)


def _parse_from(t, it):
    if t == '[':
        out = []
        while True:
            t2 = next(it)
            if t2 == ']':
                return out
            out.append(_parse_from(t2, it))
    if t == '{':
        out = {}
        while True:
            t2 = next(it)
            if t2 == '}':
                return out
            k = _parse_from(t2, it)
            v = _parse(it)
            out[k] = v
        return out
    return _atom(t)


def load_edn(path: pathlib.Path):
    return _parse(_tokens(path.read_text()))


# ───────────────────────────── metric-aware baselines ───────────────
def _empirical_quantiles(history: list[float], levels) -> dict[float, float]:
    h = sorted(history)
    n = len(h)
    out: dict[float, float] = {}
    for tau in levels:
        if n == 1:
            out[tau] = h[0]
            continue
        idx = tau * (n - 1)
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        out[tau] = h[lo] + (idx - lo) * (h[hi] - h[lo])
    return out


def _class_freqs(classes: list[str]) -> dict[str, float]:
    n = len(classes)
    return {k: v / n for k, v in Counter(classes).items()}


# ───────────────────────────── backtest (gaussian / quantile / categorical) ─
def backtest(records: list[dict]) -> dict:
    series = {r[":series/id"]: r for r in records if ":series/id" in r}
    obs = [r for r in records if ":obs/id" in r]
    forecasts = [r for r in records if ":forecast/id" in r]
    models = {r[":fc.model/id"]: r for r in records if ":fc.model/id" in r}

    # index full observations by series, sorted by observed-at
    by_series: dict[str, list[dict]] = {}
    for o in obs:
        by_series.setdefault(o[":obs/series"], []).append(o)
    for k in by_series:
        by_series[k].sort(key=lambda r: r[":obs/observed-at"])

    per_model: dict[str, dict] = {}
    for fc in forecasts:
        sid = fc[":forecast/series"]
        mid = fc.get(":forecast/model", "?")
        info = fc[":forecast/info-as-of"]
        target = fc[":forecast/target-at"]
        dk = fc[":forecast/dist-kind"].lstrip(":")
        use = fc.get(":forecast/use", ":resilience").lstrip(":")
        point = bool(fc.get(":forecast/point-asserted", False))

        hit = next((o for o in by_series.get(sid, []) if o[":obs/observed-at"] == target), None)
        if hit is None:
            continue
        # leak-free visible history (observed-at ≤ info)
        seen = [o for o in by_series[sid] if o[":obs/observed-at"] <= info]

        m = per_model.setdefault(mid, {
            "dist": dk, "metric": "", "primary": [], "logscore": [], "pit": [],
            "base_clim": [], "base_persist": [], "n": 0,
        })

        if dk == "gaussian":
            y = hit[":obs/value"]
            f = Forecast(fc[":forecast/id"], "gaussian", info_as_of=info,
                         mean=float(fc[":forecast/mean"]), sd=float(fc[":forecast/sd"]),
                         use=use, point_asserted=point)
            sc = score_pair(f, Observation(f"obs@{target}", observed_at=target, value=y))
            m["metric"] = "CRPS"
            m["primary"].append(sc["crps"])
            m["logscore"].append(sc["log_score"])
            hist = [o[":obs/value"] for o in seen]
            if len(hist) >= 2:
                cmu, csd = climatology_gaussian(hist)
                m["base_clim"].append(gaussian_crps(cmu, csd, y))
                pmu, psd = persistence_gaussian(hist)
                m["base_persist"].append(gaussian_crps(pmu, psd, y))

        elif dk == "quantile":
            y = hit[":obs/value"]
            q = {float(k): float(v) for k, v in fc[":forecast/quantiles"].items()}
            f = Forecast(fc[":forecast/id"], "quantile", info_as_of=info, quantiles=q,
                         use=use, point_asserted=point)
            sc = score_pair(f, Observation(f"obs@{target}", observed_at=target, value=y))
            m["metric"] = "pinball"
            m["primary"].append(sc["pinball"])
            hist = [o[":obs/value"] for o in seen]
            if len(hist) >= 2:
                m["base_clim"].append(pinball_loss(_empirical_quantiles(hist, q.keys()), y))

        elif dk == "categorical":
            cls = hit.get(":obs/class", "")
            probs = {str(k): float(v) for k, v in fc[":forecast/probs"].items()}
            f = Forecast(fc[":forecast/id"], "categorical", info_as_of=info, probs=probs,
                         use=use, point_asserted=point)
            sc = score_pair(f, Observation(f"obs@{target}", observed_at=target, cls=cls))
            m["metric"] = "Brier"
            m["primary"].append(sc["brier"])
            m["logscore"].append(sc["log_score"])
            histc = [o[":obs/class"] for o in seen if ":obs/class" in o]
            if histc:
                m["base_clim"].append(brier_score(_class_freqs(histc), cls))

        elif dk == "ensemble":
            y = hit[":obs/value"]
            members = [float(x) for x in fc[":forecast/members"]]
            f = Forecast(fc[":forecast/id"], "ensemble", info_as_of=info, members=members,
                         use=use, point_asserted=point)
            sc = score_pair(f, Observation(f"obs@{target}", observed_at=target, value=y))
            m["metric"] = "CRPS"
            m["primary"].append(sc["crps"])
            hist = [o[":obs/value"] for o in seen]
            if len(hist) >= 2:
                m["base_clim"].append(ensemble_crps(hist, y))   # visible history as a climatology ensemble
        else:
            continue

        m["pit"].append(sc["pit"])
        m["n"] += 1

    cards = []
    for mid, m in sorted(per_model.items()):
        n = m["n"]
        mean_primary = sum(m["primary"]) / n
        mean_ls = (sum(m["logscore"]) / len(m["logscore"])) if m["logscore"] else None
        calib = calibration_summary(m["pit"])
        skill_clim = skill_score(mean_primary, sum(m["base_clim"]) / len(m["base_clim"])) if m["base_clim"] else None
        skill_persist = skill_score(mean_primary, sum(m["base_persist"]) / len(m["base_persist"])) if m["base_persist"] else None
        if m["dist"] == "gaussian":
            skilled = bool(skill_clim and skill_clim > 0 and skill_persist and skill_persist > 0)
        else:
            skilled = bool(skill_clim is not None and skill_clim > 0)
        cards.append({
            "model": mid,
            "name": models.get(mid, {}).get(":fc.model/name", mid),
            "dist": m["dist"],
            "metric": m["metric"],
            "n": n,
            "mean_primary": mean_primary,
            "mean_logscore": mean_ls,
            "pit_mean": calib["pit_mean"],
            "calib_deviation": calib["deviation"],
            "pit_hist": calib["hist"],
            "skill_vs_climatology": skill_clim,
            "skill_vs_persistence": skill_persist,
            "skilled": skilled,
        })
    return {"series": series, "models": models, "cards": cards}


# ───────────────────────────── render ───────────────────────────────
def _fmt(x):
    return "n/a" if x is None else f"{x:.4f}"


def render_md(res: dict) -> str:
    L = ["# mitooshi 見通し — forecasting scorecard", "",
         "_Leak-free proper-scoring backtest. Lower CRPS / log-score = better; skill > 0 = beats the baseline._",
         "_All figures :representative (G11). 非終末論: this is a moving record, not a final verdict._", ""]
    for s in res["series"].values():
        L.append(f"- **series** `{s[':series/id']}` — {s.get(':series/name','')} "
                 f"({s.get(':series/kind','')}, {s.get(':series/unit','')}, source-class {s.get(':series/source-class','')})")
    L += ["", "## Per-model scorecard", "",
          "| model | dist | n | metric | mean score | PIT mean | calib dev | skill vs clim | skill vs persist | skilled? |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c in res["cards"]:
        L.append(
            f"| {c['name']} | {c['dist']} | {c['n']} | {c['metric']} | {_fmt(c['mean_primary'])} | "
            f"{_fmt(c['pit_mean'])} | {_fmt(c['calib_deviation'])} | {_fmt(c['skill_vs_climatology'])} | "
            f"{_fmt(c['skill_vs_persistence'])} | {'✅' if c['skilled'] else '❌ (honest)'} |"
        )
    L += ["", "## Reading this",
          "- **mean score** is a PROPER scoring rule (CRPS / pinball / Brier) — the distance between the forecast distribution and the realized fact; lower = better; it is the model error.",
          "- **PIT mean ≈ 0.5 + low calib-deviation** = the forecast's stated uncertainty matches reality (calibrated).",
          "- **skilled** is true ONLY when the model beats BOTH climatology and persistence (G12). An honest ❌",
          "  means: keep the baseline; do not promote (calibration_gate would refuse, G7/G12).",
          "- The residuals feeding online_update are exactly `y − mean` per forecast; that is what corrects the weights.",
          ""]
    return "\n".join(L)


def render_datoms(res: dict) -> str:
    L = [";; forecast-scorecard.kotoba.edn — DERIVED (:fc.score/derived true). Do NOT re-ingest as fact.",
         ";; ADR-2606051800 · generated by methods/analyze.py", "", "["]
    for c in res["cards"]:
        L.append(
            f' {{:fc.score/id "score-{c["model"]}" :fc.score/model "{c["model"]}" '
            f':fc.score/metric "{c["metric"]}" :fc.score/value {c["mean_primary"]:.6f} '
            f':fc.score/pit {c["pit_mean"]:.6f} '
            f':fc.score/skill {("nil" if c["skill_vs_climatology"] is None else f"{c['skill_vs_climatology']:.6f}")} '
            f':fc.model/skilled {str(c["skilled"]).lower()} :fc.score/derived true}}'
        )
    L.append("]")
    return "\n".join(L) + "\n"


def render_reliability(res: dict) -> str:
    """A text reliability diagram per model: the PIT histogram vs the uniform ideal.

    A calibrated forecaster has PIT ~ Uniform(0,1) → every bar ≈ the dashed ideal line.
    Bars far above/below the ideal reveal over/under-confidence — the G7 signal the
    calibration_gate refuses promotion on. (kami-engine-viz-ready: the per-bin frequencies
    are also emitted as datoms in reliability.kotoba.edn.)
    """
    L = ["# mitooshi 見通し — reliability diagrams (PIT calibration)", "",
         "_PIT ~ Uniform(0,1) ⇔ calibrated. Each `#` ≈ 2% of mass; `·` marks the 10% uniform ideal._",
         "_非終末論: a moving record (G7). All figures :representative._",
         "_HONEST small-sample caveat: each model here has only 3–6 PIT points over 10 bins, so the_",
         "_histogram is necessarily lumpy and `deviation` is inflated — a calibration verdict needs_",
         "_a far larger sample (R1, live-gated). The PIT MEAN (≈0.5 ⇔ unbiased) is the reliable signal here._", ""]
    for c in res["cards"]:
        hist = c.get("pit_hist") or []
        L += [f"## {c['name']} ({c['dist']}) — PIT mean {c['pit_mean']:.3f}, deviation {c['calib_deviation']:.3f}", ""]
        ideal = 1.0 / len(hist) if hist else 0.1
        ideal_cells = round(ideal * 50)
        for i, f in enumerate(hist):
            lo, hi = i / len(hist), (i + 1) / len(hist)
            bar_n = round(f * 50)
            bar = "#" * bar_n
            # place the ideal marker
            if ideal_cells <= bar_n:
                bar = bar[:ideal_cells] + "·" + bar[ideal_cells + 1:] if bar_n > ideal_cells else bar + "·"
            else:
                bar = bar + " " * (ideal_cells - bar_n) + "·"
            L.append(f"`[{lo:.1f}–{hi:.1f})` {bar} {f*100:4.0f}%")
        verdict = "calibrated" if c["calib_deviation"] <= 0.4 else "MISCALIBRATED → calibration_gate would refuse (G7)"
        L += ["", f"→ {verdict}", ""]
    return "\n".join(L)


def render_reliability_datoms(res: dict) -> str:
    L = [";; reliability.kotoba.edn — DERIVED PIT calibration (:fc.calib/*). Do NOT re-ingest as fact.",
         ";; ADR-2606051800 · generated by methods/analyze.py", "", "["]
    for c in res["cards"]:
        hist = " ".join(f"{f:.4f}" for f in (c.get("pit_hist") or []))
        L.append(
            f' {{:fc.calib/id "calib-{c["model"]}" :fc.calib/model "{c["model"]}" '
            f':fc.calib/pit-mean {c["pit_mean"]:.6f} :fc.calib/deviation {c["calib_deviation"]:.6f} '
            f':fc.calib/hist "[{hist}]"}}'
        )
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    here = pathlib.Path(__file__).resolve().parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here.parent / "data" / "seed-forecast-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    records = load_edn(seed)
    res = backtest(records)
    (outdir / "scorecard.md").write_text(render_md(res))
    (outdir / "forecast-scorecard.kotoba.edn").write_text(render_datoms(res))
    (outdir / "reliability.md").write_text(render_reliability(res))
    (outdir / "reliability.kotoba.edn").write_text(render_reliability_datoms(res))

    print(f"mitooshi: scored {sum(c['n'] for c in res['cards'])} forecast(s) across {len(res['cards'])} model(s)")
    for c in res["cards"]:
        print(f"  {c['name']} [{c['dist']}]: {c['metric']}={c['mean_primary']:.4f} "
              f"skill_vs_clim={_fmt(c['skill_vs_climatology'])} "
              f"skill_vs_persist={_fmt(c['skill_vs_persistence'])} "
              f"skilled={c['skilled']}")
    print(f"  → {outdir/'scorecard.md'} + {outdir/'reliability.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
