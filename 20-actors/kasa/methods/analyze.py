#!/usr/bin/env python3
"""kasa 嵩 — analyze cell (stdlib only).

Reads the worldwide computing-capacity observation graph (data/seed-compute-capacity.kotoba.edn
or an ingested merge) and emits AGGREGATE-FIRST observations of the world's annual compute
MAGNITUDE and GROWTH (the founder's 年間増加量):
  - per-series year-over-year growth (:compute.growth :yoy — consecutive years)
  - per-series compound annual growth rate over the span (:compute.growth :cagr)
  - domain aggregates (:compute.agg — coverage-honest, within one domain×unit, never double-count)
  - out/intel-report.md  +  out/compute-growth.kotoba.edn

NON-ADJUDICATING (G2) / PLANNING-LENS (G9) / NO FORECAST (G4): every number here is either a
quantity a public source measured/estimated, or a transparent rate-of-change of two such
quantities. kasa reports what the world ADDED; it never ranks countries "ahead/behind", builds a
targeting list, advises an investment, or projects a FUTURE value (forecasting is mitooshi 見通し).

    python3 methods/analyze.py            # runs the seed graph alone
ADR-2606072000.
"""
from __future__ import annotations
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))
import kasa_edn  # noqa: E402

SEED = os.path.join(HERE, "data", "seed-compute-capacity.kotoba.edn")

UNIT_LABEL = {
    ":usd": "$", ":exabytes": "EB", ":units": "units", ":flops": "FLOP",
    ":watts": "W", ":ratio": "×",
}
SCALE_SUFFIX = {
    ":ones": "", ":thousands": "K", ":millions": "M", ":billions": "B",
    ":petaflops": " PFLOP/s", ":exaflops": " EFLOP/s", ":gigawatts": " GW",
}


def load(path):
    """→ (series{id:dict}, obs[list], sources{id:dict})"""
    rows = kasa_edn.read_file(path)
    series = {r[":compute.series/id"]: r for r in rows if ":compute.series/id" in r}
    obs = [r for r in rows if ":compute.obs/id" in r]
    sources = {r[":compute.source/id"]: r for r in rows if ":compute.source/id" in r}
    return series, obs, sources


def by_series_year(obs):
    """{series_id: {year: value}}"""
    out = {}
    for o in obs:
        sid = o[":compute.obs/series"]
        out.setdefault(sid, {})[int(o[":compute.obs/year"])] = float(o[":compute.obs/value"])
    return out


def derive_growth(sy):
    """→ list of :compute.growth dicts (all :synthesized): per-series YoY + full-span CAGR."""
    growth = []
    for sid, years in sy.items():
        ys = sorted(years)
        # YoY for each consecutive pair
        for prev, cur in zip(ys, ys[1:]):
            if cur == prev + 1 and years[prev] != 0:
                growth.append(_growth(sid, ":yoy", prev, cur,
                                      years[cur] / years[prev] - 1.0,
                                      f"obs[{cur}]/obs[{prev}]"))
        # CAGR over the full observed span
        if len(ys) >= 2 and years[ys[0]] > 0 and years[ys[-1]] > 0:
            span = ys[-1] - ys[0]
            cagr = (years[ys[-1]] / years[ys[0]]) ** (1.0 / span) - 1.0
            growth.append(_growth(sid, ":cagr", ys[0], ys[-1], cagr,
                                  f"(obs[{ys[-1]}]/obs[{ys[0]}])^(1/{span})-1"))
    return growth


def _growth(sid, kind, fr, to, value, basis):
    return {
        ":compute.growth/id": f"growth.{sid}.{fr}-{to}.{kind.lstrip(':')}",
        ":compute.growth/series": sid,
        ":compute.growth/kind": kind,
        ":compute.growth/from-year": fr,
        ":compute.growth/to-year": to,
        ":compute.growth/value": round(value, 4),
        ":compute.growth/basis": basis,
        ":compute.growth/sourcing": ":synthesized",
    }


def aggregates(series, sy):
    """Σ per (domain, metric, unit, scale, year) — coverage-honest. Aggregation requires a COMMON
    metric+unit+SCALE (so TOP500 PFLOP/s is never summed with raw-FLOP training compute), and is
    confined to one domain — so memory (:dram/:nand), a subset of :semiconductor in a distinct
    domain key, is structurally never double-counted (G12)."""
    acc = {}
    for sid, years in sy.items():
        s = series.get(sid, {})
        domain = s.get(":compute.series/domain", ":unknown")
        metric = s.get(":compute.series/metric", ":unknown")
        unit = s.get(":compute.series/unit", ":unknown")
        scale = s.get(":compute.series/scale", ":ones")
        for y, v in years.items():
            key = (domain, metric, unit, scale, y)
            a = acc.setdefault(key, {"sum": 0.0, "n": 0})
            a["sum"] += v
            a["n"] += 1
    out = []
    for (domain, metric, unit, scale, y), a in sorted(acc.items(), key=lambda kv: kv[0]):
        out.append({
            ":compute.agg/id": f"agg.{domain.lstrip(':')}.{metric.lstrip(':')}.{unit.lstrip(':')}.{scale.lstrip(':')}.{y}",
            ":compute.agg/dimension": ":domain",
            ":compute.agg/key": domain,
            ":compute.agg/year": y,
            ":compute.agg/metric": metric,
            ":compute.agg/unit": unit,
            ":compute.agg/scale": scale,
            ":compute.agg/sum": round(a["sum"], 4),
            ":compute.agg/n": a["n"],
            ":compute.agg/sourcing": ":synthesized",
        })
    return out


def fmt_val(v, series):
    """Human-format a value given its series unit+scale."""
    unit = series.get(":compute.series/unit", "")
    scale = series.get(":compute.series/scale", ":ones")
    if unit == ":flops" and scale == ":ones":
        return f"{v:.1e} FLOP"
    sym = UNIT_LABEL.get(unit, "")
    suf = SCALE_SUFFIX.get(scale, "")
    if unit == ":usd":
        return f"${v:,.0f}{suf}"
    if unit == ":exabytes":
        return f"{v:,.0f} EB"
    if unit == ":units":
        return f"{v:,.0f}{suf} units"
    if unit == ":flops":
        return f"{v:,.0f}{suf}"
    if unit == ":watts":
        return f"{v:,.0f}{suf}"
    return f"{v:,.0f} {sym}{suf}".strip()


def pct(x):
    return f"{x*100:+.1f}%"


def report(series, obs, sources, sy, growth, aggs):
    L = []
    A = L.append
    sids = sorted(sy.keys())
    years_all = sorted({y for ys in sy.values() for y in ys})
    pubs = sorted({sources[o[":compute.obs/source"]][":compute.source/publisher"]
                   for o in obs if o.get(":compute.obs/source") in sources})
    A("# kasa 嵩 — worldwide computing-capacity growth report")
    A("")
    A("> Aggregate-first, **non-adjudicating** (G2), **planning-lens** (G9 — sizes the compute")
    A("> commons, never a country/company ranking or a targeting list), **no forecast** (G4 — past/")
    A("> present actuals + measured growth only; future projection is mitooshi 見通し). Every figure")
    A("> is either a quantity a public source measured/estimated, or a transparent rate-of-change of")
    A("> two such figures (`:synthesized`, G5). Seed values are `:representative` headline figures —")
    A("> see the honesty note.")
    A("")
    A("## Coverage")
    A("")
    A(f"- **Series**: {len(sids)} · **Observations**: {len(obs)} · **Years**: "
      f"{years_all[0]}–{years_all[-1]} · **Growth points derived**: {len(growth)}")
    A(f"- **Public sources**: {', '.join(p.lstrip(':') for p in pubs)} "
      f"(public headline / open-dataset only — NO paid report / terminal, G1)")
    A(f"- **Sourcing**: headline figures `:representative` (rounded); frontier-training + "
      f"datacenter-power rows `:estimated` (analyst/Epoch-AI estimate, with method). "
      f"Authoritative dataset parse = G7 operator-gated (`ingest.py`).")
    A("")
    A(f"## World compute snapshot — latest observed year per series")
    A("")
    A("| Domain | Series | Latest yr | Value | YoY | CAGR (span) |")
    A("|---|---|--:|--:|--:|--:|")
    gidx = {}
    for g in growth:
        gidx.setdefault((g[":compute.growth/series"], g[":compute.growth/kind"]), []).append(g)
    for sid in sids:
        s = series.get(sid, {})
        years = sy[sid]
        last = max(years)
        dom = s.get(":compute.series/domain", "").lstrip(":")
        label = s.get(":compute.series/label", sid).split(" / ")[0]
        # latest YoY = the yoy ending at `last`
        yoy = next((g[":compute.growth/value"] for g in gidx.get((sid, ":yoy"), [])
                    if g[":compute.growth/to-year"] == last), None)
        cagr = next((g[":compute.growth/value"] for g in gidx.get((sid, ":cagr"), [])), None)
        A(f"| {dom} | {label} | {last} | {fmt_val(years[last], s)} | "
          f"{pct(yoy) if yoy is not None else '—'} | {pct(cagr) if cagr is not None else '—'} |")
    A("")
    A("_YoY / CAGR are `:synthesized` rates of change of disclosed/estimated figures. Values across")
    A("series are in DIFFERENT units (revenue vs exabytes vs FLOP) and are NOT directly comparable._")
    A("")
    A("## Annual increase (年間増加量) — per-series year-over-year")
    A("")
    A("| Series | " + " | ".join(f"{a}→{b}" for a, b in zip(years_all, years_all[1:])) + " |")
    A("|---|" + "--:|" * (len(years_all) - 1))
    for sid in sids:
        label = series.get(sid, {}).get(":compute.series/label", sid).split(" / ")[0]
        cells = []
        ymap = {(g[":compute.growth/from-year"], g[":compute.growth/to-year"]): g[":compute.growth/value"]
                for g in gidx.get((sid, ":yoy"), [])}
        for a, b in zip(years_all, years_all[1:]):
            v = ymap.get((a, b))
            cells.append(pct(v) if v is not None else "—")
        A(f"| {label} | " + " | ".join(cells) + " |")
    A("")
    A("## Domain aggregates (coverage-honest — read against `n`, never a market total; G3/G12)")
    A("")
    A("| Domain | Metric | Year | Σ | n series |")
    A("|---|---|--:|--:|--:|")
    # latest year only, to keep it aggregate-first
    latest = years_all[-1]
    for a in aggs:
        if a[":compute.agg/year"] != latest:
            continue
        ser = {":compute.series/unit": a[":compute.agg/unit"], ":compute.series/scale": a[":compute.agg/scale"]}
        A(f"| {a[':compute.agg/key'].lstrip(':')} | {a[':compute.agg/metric'].lstrip(':')} | "
          f"{a[':compute.agg/year']} | {fmt_val(a[':compute.agg/sum'], ser)} | {a[':compute.agg/n']} |")
    A("")
    A("> Σ is bounded by the series ingested in that (domain, unit) — NOT a market total. Memory")
    A("> (:dram / :nand) is a SUBSET of :semiconductor and lives in a distinct domain key, so it is")
    A("> structurally NEVER summed into the semiconductor total (no double-count). Absence ≠ zero.")
    A("")
    A("## Honesty (R0)")
    A("")
    A("- Bounded `:representative` seed of public headline figures (WSTS/SIA · TrendForce · IDC · JPR")
    A("  · TOP500) + `:estimated` rows (Epoch AI frontier-training · datacenter power). \"Ingest the")
    A("  world's compute-capacity stats\" is the **R1** goal — full open-dataset parse is **G7**")
    A("  Council + operator gated (`ingest.py`).")
    A("- Figures are rounded headline numbers, NOT the exact dataset row; estimates carry a method.")
    A("- kasa does NOT forecast (future projection is mitooshi 見通し), does not rank countries, does")
    A("  not build an export-control / targeting list, and gives no investment advice. It records how")
    A("  much compute the world ADDED and the arithmetic of that growth.")
    return "\n".join(L) + "\n"


def edn_dump(growth, aggs):
    L = [";; kasa 嵩 — derived growth + aggregates (GENERATED by analyze.py)",
         ";; ADR-2606072000 · all :synthesized (G5) — NEVER re-ingested as observations.",
         "["]
    for g in growth:
        L.append(" {" + " ".join(f"{k} {_v(v)}" for k, v in g.items()) + "}")
    for a in aggs:
        L.append(" {" + " ".join(f"{k} {_v(v)}" for k, v in a.items()) + "}")
    L.append("]")
    return "\n".join(L) + "\n"


def _v(v):
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(v)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SEED
    series, obs, sources = load(src)
    sy = by_series_year(obs)
    growth = derive_growth(sy)
    aggs = aggregates(series, sy)
    outdir = os.path.join(HERE, "out")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "intel-report.md"), "w") as f:
        f.write(report(series, obs, sources, sy, growth, aggs))
    with open(os.path.join(outdir, "compute-growth.kotoba.edn"), "w") as f:
        f.write(edn_dump(growth, aggs))
    print(f"kasa analyze: {len(series)} series · {len(obs)} obs · {len(sources)} sources · "
          f"{len(growth)} growth · {len(aggs)} aggregates")
    print(f"  → out/intel-report.md")
    print(f"  → out/compute-growth.kotoba.edn")


if __name__ == "__main__":
    main()
