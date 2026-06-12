#!/usr/bin/env python3
"""itonami 営み — R1 optimization-proposal engine (ADR-2606082300).

Turns the R0 observation KPIs into two CONCRETE, QUANTIFIED improvement proposals — the
charter-clean form of the FOX "cut 10% energy" headline. Both are *proposals to a human /
Council*, never write-backs (G1), and never reach below the station/line scale (G2).

  1. idle power-down  — recoverable kWh by powering stations down during non-producing
     (idle/down) windows, with a CONSERVATIVE recoverable fraction (baseline draw can't be
     cut). Yields a line-level energy-reduction %.
  2. bottleneck relief — a serial line's OEE is its weakest station; raising that one station
     to the 2nd-weakest lifts the whole line's OEE to the 2nd-weakest value. Yields a
     throughput-uplift %.

Both proposals route to EFFICIENCY (less wasted energy / fewer stops), NOT to line-speed-up or
labor intensification (G2): the bottleneck-relief target is availability/performance recovery
(removing stoppages and energy waste), never raising the human-paced cycle below takt.

Pure stdlib (no numpy). Usage:
    python3 optimize.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

# Conservative share of non-producing energy that is actually recoverable by power-down.
# Representative + documented (G5): real plants keep a baseline (controllers, HVAC, standby
# heating). NOT presented as a guarantee — it is the assumption behind the proposal.
RECOVERABLE_IDLE_FRACTION = 0.7


def _stations(res: dict):
    return [s for s in res if not s.startswith("_")]


def idle_powerdown(res: dict, recoverable: float = RECOVERABLE_IDLE_FRACTION) -> dict:
    """Recoverable energy from powering down during non-producing windows."""
    sids = _stations(res)
    per = {}
    total_idle = 0.0
    total_kwh = 0.0
    for s in sids:
        idle_kwh = res[s]["idle_kwh"]
        per[s] = idle_kwh * recoverable
        total_idle += idle_kwh
        total_kwh += res[s]["kwh"]
    recoverable_kwh = total_idle * recoverable
    return {
        "per_station": per,
        "recoverable_kwh": recoverable_kwh,
        "line_kwh": total_kwh,
        "energy_reduction_frac": (recoverable_kwh / total_kwh if total_kwh > 0 else 0.0),
        "recoverable_fraction_assumed": recoverable,
        # the single station with the biggest power-down win (where to start)
        "top_station": (max(sids, key=lambda s: per[s]) if sids else None),
    }


def bottleneck_relief(res: dict) -> dict:
    """Lifting the worst station to the 2nd-worst raises the whole serial line's OEE."""
    sids = _stations(res)
    if len(sids) < 2:
        return {"current_line_oee": res["_line"]["oee"], "target_line_oee": res["_line"]["oee"],
                "oee_uplift_frac": 0.0, "bottleneck": None, "lifts_to": None}
    by_oee = sorted(sids, key=lambda s: res[s]["oee"])
    worst, second = by_oee[0], by_oee[1]
    cur = res[worst]["oee"]
    target = res[second]["oee"]  # new line OEE once the single bottleneck is relieved
    return {
        "current_line_oee": cur,
        "target_line_oee": target,
        "oee_uplift_frac": ((target - cur) / cur if cur > 0 else 0.0),
        "bottleneck": worst,
        "lifts_to": second,
        # relief is availability/performance recovery, never sub-takt speed-up (G2)
        "relief_levers": ["availability (remove unplanned stops)",
                          "performance (reduce minor stops / idle), within takt"],
    }


def optimize(stations: dict, ticks: list, res: dict | None = None) -> dict:
    if res is None:
        res = analyze(stations, ticks)
    return {
        "idle_powerdown": idle_powerdown(res),
        "bottleneck_relief": bottleneck_relief(res),
    }


def _label(stations, sid):
    return stations.get(sid, {}).get(":station/label", sid) if sid else "—"


def report_md(stations: dict, opt: dict) -> str:
    e = opt["idle_powerdown"]
    b = opt["bottleneck_relief"]
    L = []
    L.append("# itonami 営み — R1 optimization proposals (to a human / Council)\n")
    L.append("> **G1 — these are PROPOSALS with estimates, never write-backs.** itonami does "
             "not actuate. **G2** — relief targets availability/performance + energy waste, "
             "NEVER sub-takt speed-up or labor intensification. Energy fraction is a documented "
             "assumption, not a guarantee (G5).\n")

    L.append("\n## 1 · Idle power-down (energy reduction)\n")
    L.append(f"Recoverable energy by powering down during non-producing windows, assuming "
             f"**{e['recoverable_fraction_assumed']:.0%}** of non-producing draw is cuttable:\n")
    L.append(f"- **{e['recoverable_kwh']:.1f} kWh** recoverable of {e['line_kwh']:.0f} kWh "
             f"→ **{e['energy_reduction_frac']:.1%}** line energy reduction")
    L.append(f"- start at **{_label(stations, e['top_station'])}** "
             f"({e['per_station'].get(e['top_station'], 0):.1f} kWh recoverable)")

    L.append("\n## 2 · Bottleneck relief (throughput, within takt)\n")
    L.append(f"- bottleneck **{_label(stations, b['bottleneck'])}** OEE {b['current_line_oee']:.1%} "
             f"→ lifting it to **{_label(stations, b['lifts_to'])}** raises line OEE to "
             f"**{b['target_line_oee']:.1%}** (**+{b['oee_uplift_frac']:.1%}**)")
    L.append(f"- levers (G2-safe): {', '.join(b['relief_levers'])}")

    L.append("\n---\n_itonami 営み R1 · ADR-2606082300 · proposals-only · no-actuation · "
             "efficiency-not-intensification._\n")
    return "\n".join(L)


def emit_proposals(opt: dict, tx: int = 1) -> str:
    """Transient EAVT proposal datoms (computed on read, never durable — G3)."""
    e, b = opt["idle_powerdown"], opt["bottleneck_relief"]
    L = [";; itonami R1 optimization proposals — TRANSIENT (:bond/is-transient true), G1/G3.",
         "["]
    L.append(f"[:line.sarutahiko-a :ops/proposal-energy-reduction-frac {e['energy_reduction_frac']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[:line.sarutahiko-a :ops/proposal-recoverable-kwh {e['recoverable_kwh']:g} {tx} :derived] ;; :bond/is-transient true")
    if b["bottleneck"]:
        L.append(f"[:line.sarutahiko-a :ops/proposal-bottleneck {b['bottleneck']} {tx} :derived] ;; :bond/is-transient true")
        L.append(f"[:line.sarutahiko-a :ops/proposal-oee-uplift-frac {b['oee_uplift_frac']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    opt = optimize(stations, ticks)
    (outdir / "optimization-proposals.md").write_text(report_md(stations, opt), encoding="utf-8")
    (outdir / "itonami-proposals.kotoba.edn").write_text(emit_proposals(opt, tx), encoding="utf-8")
    e, b = opt["idle_powerdown"], opt["bottleneck_relief"]
    print(f"itonami R1: energy -{e['energy_reduction_frac']:.1%} ({e['recoverable_kwh']:.1f} kWh) "
          f"· bottleneck {b['bottleneck']} OEE +{b['oee_uplift_frac']:.1%} → {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
