#!/usr/bin/env python3
"""itonami 営み — R5 throughput / line-balance planner (ADR-2606082300).

Translates OEE observations into ACTUAL output (units/day) through a SECOND lens distinct from
the R1 OEE-bottleneck: the takt-capacity bottleneck. A serial line's output rate is set by its
slowest station's capacity (uptime ÷ takt). The OEE-worst station and the throughput-worst
station are often DIFFERENT — surfacing that gap is exactly the operations intelligence FOX
sells. Output is a production plan: trucks/day now, and the availability-recovery uplift.

  station_capacity — per station: capacity at observed uptime vs at full availability
  line_plan        — line throughput bottleneck + units/window + units/day (documented hours)
  relief_plan      — recover the throughput-bottleneck's idle/down → new line throughput uplift

CONSTITUTIONAL (read before any change):
  G1 — RECOMMENDS a plan; never actuates the line or sets a rate on the OT bus.
  G2 — capacity relief is AVAILABILITY recovery (remove stops) WITHIN takt; it never proposes a
    sub-takt cycle / speed-up / labor intensification. Station/line scale only (no worker).
  G3 — capacity is a read-time aggregate; the operating-hours/day is a DOCUMENTED assumption
    (G5), not a fact.

Pure stdlib (no numpy). Usage:
    python3 plan.py [ops_seed.edn] [--hours H] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

# Documented operating-hours assumption (G5): 2 shifts. NOT a measured fact.
OPERATING_HOURS_PER_DAY = 16.0


def _stations(res: dict):
    return [s for s in res if not s.startswith("_")]


def station_capacity(stations: dict, res: dict) -> dict:
    """Per station: cycle capacity over the window at observed uptime vs at full availability."""
    out = {}
    for sid in _stations(res):
        takt = float(stations.get(sid, {}).get(":station/takt-s", 0) or 0)
        r = res[sid]
        cap_run = (r["run_s"] / takt) if takt > 0 else 0.0          # at observed uptime
        cap_planned = (r["planned_s"] / takt) if takt > 0 else 0.0  # if fully available
        out[sid] = dict(takt=takt, capacity_run=cap_run, capacity_planned=cap_planned,
                        actual_cycles=r["cycles"], quality=r["quality"])
    return out


def _window_s(res: dict) -> float:
    return max((res[s]["planned_s"] for s in _stations(res)), default=0.0)


def line_plan(stations: dict, res: dict, hours: float = OPERATING_HOURS_PER_DAY) -> dict:
    """Line throughput = the slowest station's capacity (takt + availability limited)."""
    cap = station_capacity(stations, res)
    sids = list(cap)
    if not sids:
        return {}
    window_s = _window_s(res)
    bn = min(sids, key=lambda s: cap[s]["capacity_run"])  # throughput bottleneck
    units_per_window = cap[bn]["capacity_run"]
    day_scale = (hours * 3600.0 / window_s) if window_s > 0 else 0.0
    line_quality = res["_line"]["good"] / (res["_line"]["good"] + res["_line"]["scrap"]) \
        if (res["_line"]["good"] + res["_line"]["scrap"]) > 0 else 1.0
    return {
        "throughput_bottleneck": bn,
        "units_per_window_gross": units_per_window,
        "units_per_day_gross": units_per_window * day_scale,
        "units_per_day_good": units_per_window * day_scale * line_quality,
        "window_s": window_s, "hours_per_day": hours, "line_quality": line_quality,
        "capacity": cap,
    }


def relief_plan(stations: dict, res: dict, plan: dict | None = None,
                hours: float = OPERATING_HOURS_PER_DAY) -> dict:
    """Recover the throughput-bottleneck's idle/down → new line throughput (availability lever)."""
    if plan is None:
        plan = line_plan(stations, res, hours)
    cap = plan["capacity"]
    bn = plan["throughput_bottleneck"]
    sids = list(cap)
    # bottleneck at full availability, then the next-slowest still caps the line
    bn_recovered = cap[bn]["capacity_planned"]
    others = [cap[s]["capacity_run"] for s in sids if s != bn]
    new_units_per_window = min([bn_recovered] + others) if others else bn_recovered
    cur = plan["units_per_window_gross"]
    day_scale = (hours * 3600.0 / plan["window_s"]) if plan["window_s"] > 0 else 0.0
    return {
        "bottleneck": bn,
        "current_units_per_window": cur,
        "recovered_units_per_window": new_units_per_window,
        "uplift_frac": ((new_units_per_window - cur) / cur if cur > 0 else 0.0),
        "current_units_per_day": cur * day_scale,
        "recovered_units_per_day": new_units_per_window * day_scale,
        "lever": "availability recovery (remove idle/down stops) within takt; per-cycle pace unchanged",
        # honest note: if still takt-limited after recovery, say so
        "still_takt_limited": new_units_per_window <= cap[bn]["capacity_planned"] + 1e-9
        and abs(new_units_per_window - bn_recovered) < 1e-9,
    }


def _label(stations, sid):
    return stations.get(sid, {}).get(":station/label", sid) if sid else "—"


def report_md(stations: dict, res: dict, plan: dict, relief: dict) -> str:
    oee_bn = res["_recommend"]["bottleneck"]["station"]
    L = []
    L.append("# itonami 営み — R5 throughput / line-balance plan\n")
    L.append("> **G1** recommends a plan, never actuates. **G2** relief = availability recovery "
             "WITHIN takt, never sub-takt speed-up / intensification. **G5** operating-hours is "
             "a documented assumption, not a fact.\n")
    L.append(f"\n**Two bottlenecks, two lenses:** the OEE-worst station is "
             f"**{_label(stations, oee_bn)}**, but the THROUGHPUT-worst (takt-capacity) station "
             f"is **{_label(stations, plan['throughput_bottleneck'])}** — relieve the right one "
             "for the right goal.\n")
    L.append(f"\n- line throughput: **{plan['units_per_window_gross']:.1f}** units/window → "
             f"**{plan['units_per_day_good']:.1f}** good units/day "
             f"(@ {plan['hours_per_day']:.0f} h/day, quality {plan['line_quality']:.1%})")
    L.append(f"- recovering {_label(stations, relief['bottleneck'])} idle/down → "
             f"**{relief['recovered_units_per_window']:.1f}** units/window "
             f"(**+{relief['uplift_frac']:.1%}** → {relief['recovered_units_per_day']:.1f}/day)")
    if relief["still_takt_limited"]:
        L.append(f"  - note: {_label(stations, relief['bottleneck'])} remains takt-limited after "
                 "recovery; further gain needs process (takt) change, out of itonami scope")

    L.append("\n## Station capacity (units/window)\n")
    L.append("| station | takt s | at uptime | if fully available |")
    L.append("|---|---:|---:|---:|")
    for sid in sorted(plan["capacity"], key=lambda s: plan["capacity"][s]["capacity_run"]):
        c = plan["capacity"][sid]
        L.append(f"| {_label(stations, sid)} | {c['takt']:.0f} | {c['capacity_run']:.1f} | "
                 f"{c['capacity_planned']:.1f} |")

    L.append("\n---\n_itonami 営み R5 · ADR-2606082300 · plan-not-actuate · "
             "availability-not-speedup · documented-hours._\n")
    return "\n".join(L)


def emit(plan: dict, relief: dict, tx: int = 1) -> str:
    """Transient EAVT plan datoms (computed on read, never durable — G3)."""
    L = [";; itonami R5 throughput plan — TRANSIENT (:bond/is-transient true), G1/G3.", "["]
    L.append(f"[:line.sarutahiko-a :ops/throughput-bottleneck {plan['throughput_bottleneck']} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[:line.sarutahiko-a :ops/units-per-day-good {plan['units_per_day_good']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[:line.sarutahiko-a :ops/throughput-uplift-frac {relief['uplift_frac']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    hours = float(argv[argv.index("--hours") + 1]) if "--hours" in argv else OPERATING_HOURS_PER_DAY
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    res = analyze(stations, ticks)
    plan = line_plan(stations, res, hours)
    relief = relief_plan(stations, res, plan, hours)
    (outdir / "throughput-plan.md").write_text(report_md(stations, res, plan, relief), encoding="utf-8")
    (outdir / "itonami-plan.kotoba.edn").write_text(emit(plan, relief, tx), encoding="utf-8")
    print(f"itonami R5: throughput bottleneck {plan['throughput_bottleneck']} · "
          f"{plan['units_per_day_good']:.1f} good/day · relief +{relief['uplift_frac']:.1%} → {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
