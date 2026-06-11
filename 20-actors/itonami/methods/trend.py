#!/usr/bin/env python3
"""itonami 営み — R7 KPI trend / drift detector (ADR-2606082300).

A factory brain must track TRAJECTORIES, not a single window: kotoba is an as-of history and
Wellbecoming (§1.13) is a trajectory, not a static value. This reads the durable daily ops-KPI
snapshots (:opsday/*) and surfaces DRIFT — an OEE slowly degrading, scrap creeping up, energy
per unit rising — before any single day looks alarming. The continuous-monitoring half of what
FOX promises, made charter-clean.

  load_history  — read durable :opsday/* snapshots (the as-of series; ground state)
  analyze_trends — per (scope, KPI): first/last, relative change, least-squares slope, and a
                   polarity-aware direction {:improving :flat :degrading} + regression flag

CONSTITUTIONAL (read before any change):
  G1 — surfaces drift and RECOMMENDS attention; never actuates.
  G2 — scope is line/station only; there is no :worker/* series (anti-labor-surveillance). A
    trajectory of a person is unrepresentable.
  G3 — non-adjudicating. Directions are computed read-time aggregates over disclosed snapshots,
    flagged transient; the snapshots themselves are the durable as-of facts.

Pure stdlib (no numpy). Usage:
    python3 trend.py [history.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import read_edn  # noqa: E402

# KPI polarity: True = higher is better, False = lower is better.
KPI_POLARITY = {":opsday/oee": True, ":opsday/scrap-rate": False, ":opsday/energy-per-good": False}
FLAT_REL_THRESHOLD = 0.05   # |relative change| below this over the window → :flat


def load_history(path: pathlib.Path) -> list:
    forms = read_edn(path.read_text(encoding="utf-8"))
    recs = [f for f in forms if isinstance(f, dict) and ":opsday/day" in f]
    for r in recs:
        for bad in (":worker/", ":person/", ":operator/"):
            if any(str(k).startswith(bad) for k in r):
                raise ValueError(f"G2 violation: ops history carries a person/worker series ({bad})")
    return recs


def _slope(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def _direction(first: float, last: float, higher_better: bool) -> str:
    base = abs(first) if first != 0 else 1.0
    rel = (last - first) / base
    if abs(rel) < FLAT_REL_THRESHOLD:
        return ":flat"
    improving = (rel > 0) if higher_better else (rel < 0)
    return ":improving" if improving else ":degrading"


def analyze_trends(records: list) -> dict:
    """Per scope, per KPI: first/last/rel_change/slope/direction/regression."""
    by_scope = defaultdict(list)
    for r in records:
        by_scope[r[":opsday/scope"]].append(r)

    out = {}
    for scope, recs in by_scope.items():
        recs = sorted(recs, key=lambda r: r[":opsday/day"])
        days = [float(r[":opsday/day"]) for r in recs]
        kpis = {}
        for attr, higher_better in KPI_POLARITY.items():
            ys = [float(r[attr]) for r in recs if attr in r]
            if len(ys) < 2:
                continue
            first, last = ys[0], ys[-1]
            base = abs(first) if first != 0 else 1.0
            direction = _direction(first, last, higher_better)
            kpis[attr] = dict(
                first=first, last=last, rel_change=(last - first) / base,
                slope=_slope(days[:len(ys)], ys), direction=direction,
                regression=(direction == ":degrading"),
            )
        out[scope] = kpis
    return out


def regressions(trends: dict) -> list:
    """Flat list of (scope, kpi, rel_change) for every degrading series — the attention list."""
    rows = []
    for scope, kpis in trends.items():
        for attr, t in kpis.items():
            if t["regression"]:
                rows.append((scope, attr, t["rel_change"]))
    return sorted(rows, key=lambda r: -abs(r[2]))


def report_md(trends: dict) -> str:
    regs = regressions(trends)
    L = []
    L.append("# itonami 営み — R7 KPI trend / drift report (as-of trajectory)\n")
    L.append("> **G1** surfaces drift + recommends attention, never actuates. **G2** line/"
             "station scope only — no worker trajectory. **G3** directions are read-time over "
             "disclosed daily snapshots; the snapshots are the durable as-of facts.\n")
    L.append(f"\n**{len(regs)} degrading series** (attention, worst rel-change first):\n")
    for scope, attr, rel in regs:
        L.append(f"- {scope} · {attr.split('/')[-1]} · {rel:+.1%} over window")

    L.append("\n## All series\n")
    L.append("| scope | KPI | first → last | direction |")
    L.append("|---|---|---|---|")
    for scope in sorted(trends):
        for attr, t in trends[scope].items():
            L.append(f"| {scope} | {attr.split('/')[-1]} | {t['first']:g} → {t['last']:g} | "
                     f"{t['direction'].lstrip(':')} |")
    L.append("\n---\n_itonami 営み R7 · ADR-2606082300 · trajectory-not-snapshot · "
             "drift-surfacing · recommend-not-actuate · station-scale._\n")
    return "\n".join(L)


def emit(trends: dict, tx: int = 1) -> str:
    """Transient EAVT trend datoms (computed on read, never durable — G3)."""
    L = [";; itonami R7 KPI trends — TRANSIENT (:bond/is-transient true), G1/G3.", "["]
    for scope in sorted(trends):
        for attr, t in trends[scope].items():
            short = attr.split("/")[-1]
            L.append(f"[{scope} :trend/{short}-direction {t['direction']} {tx} :derived] ;; :bond/is-transient true")
            if t["regression"]:
                L.append(f"[{scope} :trend/{short}-regression true {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-ops-history.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    records = load_history(seed)
    trends = analyze_trends(records)
    (outdir / "trend-report.md").write_text(report_md(trends), encoding="utf-8")
    (outdir / "itonami-trends.kotoba.edn").write_text(emit(trends, tx), encoding="utf-8")
    regs = regressions(trends)
    print(f"itonami R7: {len(records)} snapshots, {len(trends)} scopes, "
          f"{len(regs)} degrading series → {outdir}")
    for scope, attr, rel in regs:
        print(f"  ↓ {scope} {attr.split('/')[-1]} {rel:+.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
