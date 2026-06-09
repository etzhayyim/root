#!/usr/bin/env python3
"""itonami 営み — factory-operations KPI engine over scan-cycle observations.

ADR-2606082300. The charter-clean inversion of an "AI Factory Brain" / NVIDIA Factory
Operations Blueprint (FOX): it OBSERVES the running factory (kotoba-os scan-cycle Datoms +
sarutahiko/giemon line stations) and RECOMMENDS where to improve OEE / energy / quality —
it never actuates the line, and it cannot represent per-worker monitoring.

Reads a kotoba-EDN operations log: :station/* node maps + :tick/* scan-cycle observations.
Computes, aggregate-first, the canonical manufacturing metrics:

  OEE = Availability × Performance × Quality        (per station + line rollup)
  energy/good-unit (kWh)                             (the FOX "10% energy cut" lever)
  idle-energy fraction                               (energy burned while not producing)
  scrap-rate                                         (routed to vision inspection / manako)

CONSTITUTIONAL (read before any change):
  G1 — OBSERVE → RECOMMEND only. itonami NEVER actuates (no-server-key, liveActuation:false,
    consistent with kotoba-os C-carve-outs). The optimization is a proposal to a human/Council,
    never a write back to the OT bus.
  G2 — STATION / LINE scale ONLY. There is no :worker/* dimension; per-person productivity,
    pace, or presence is structurally unrepresentable (Wellbecoming §1.13, anti-labor-
    surveillance). Energy/quality gains route to EFFICIENCY, never to line-speed-up or
    labor intensification that harms the worker.
  G3 — non-adjudicating. Station states (:run/:idle/:down) and counts are DISCLOSED scan-cycle
    facts, never itonami verdicts.

Pure stdlib (no numpy) — runnable inside an itonami kotoba pywasm actor (componentize-py).
Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


RUN = ":run"          # producing
IDLE = ":idle"        # powered, not producing (changeover / starved / blocked)
DOWN = ":down"        # fault / unplanned stop
PRODUCING_STATES = {RUN}


def load(path: pathlib.Path):
    """Return (stations_by_id, ticks) from an itonami operations EDN log."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    stations, ticks = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":station/id" in f:
            stations[f[":station/id"]] = f
        elif ":tick/station" in f:
            ticks.append(f)
    return stations, ticks


def _num(v, default=0.0):
    try:
        return float(v if v is not None else default)
    except (TypeError, ValueError):
        return float(default)


def analyze(stations: dict, ticks: list):
    """Aggregate scan-cycle ticks into per-station OEE / energy / quality (G2: station scale).

    Returns {station_id: {availability, performance, quality, oee, kwh, idle_kwh,
                          energy_per_good, idle_energy_frac, cycles, good, scrap, ...}}
    plus a "_line" rollup and "_recommend" routed findings.
    """
    agg = defaultdict(lambda: dict(planned_s=0.0, run_s=0.0, idle_s=0.0, down_s=0.0,
                                   cycles=0.0, good=0.0, scrap=0.0, kwh=0.0, idle_kwh=0.0))
    for tk in ticks:
        sid = tk.get(":tick/station")
        if sid is None:
            continue
        a = agg[sid]
        dt = _num(tk.get(":tick/interval-s"), 0.0)
        state = tk.get(":tick/state")
        a["planned_s"] += dt
        if state == RUN:
            a["run_s"] += dt
        elif state == IDLE:
            a["idle_s"] += dt
        elif state == DOWN:
            a["down_s"] += dt
        a["cycles"] += _num(tk.get(":tick/cycles"))
        a["good"] += _num(tk.get(":tick/good"))
        a["scrap"] += _num(tk.get(":tick/scrap"))
        kwh = _num(tk.get(":tick/kwh"))
        a["kwh"] += kwh
        if state not in PRODUCING_STATES:
            a["idle_kwh"] += kwh   # energy burned while not producing — the cut lever

    out = {}
    for sid, a in agg.items():
        st = stations.get(sid, {})
        takt = _num(st.get(":station/takt-s"), 0.0)
        planned, run_s = a["planned_s"], a["run_s"]
        cycles, good = a["cycles"], a["good"]

        availability = run_s / planned if planned > 0 else 0.0
        # ideal cycle time = takt; performance = ideal busy time / actual run time
        performance = (takt * cycles) / run_s if run_s > 0 else 0.0
        quality = good / cycles if cycles > 0 else 0.0
        oee = availability * performance * quality
        out[sid] = dict(
            availability=availability, performance=performance, quality=quality, oee=oee,
            kwh=a["kwh"], idle_kwh=a["idle_kwh"],
            energy_per_good=(a["kwh"] / good if good > 0 else float("inf")),
            idle_energy_frac=(a["idle_kwh"] / a["kwh"] if a["kwh"] > 0 else 0.0),
            scrap_rate=(a["scrap"] / cycles if cycles > 0 else 0.0),
            cycles=cycles, good=good, scrap=a["scrap"],
            run_s=run_s, idle_s=a["idle_s"], down_s=a["down_s"], planned_s=planned,
        )

    out["_line"] = _line_rollup(out)
    out["_recommend"] = _recommend(out, stations)
    return out


def _line_rollup(per: dict) -> dict:
    sids = [s for s in per if not s.startswith("_")]
    if not sids:
        return dict(oee=0.0, kwh=0.0, idle_kwh=0.0, good=0.0, scrap=0.0, energy_per_good=0.0)
    kwh = sum(per[s]["kwh"] for s in sids)
    idle_kwh = sum(per[s]["idle_kwh"] for s in sids)
    good = sum(per[s]["good"] for s in sids)
    scrap = sum(per[s]["scrap"] for s in sids)
    # line OEE is gated by its weakest station (a serial line is its bottleneck)
    line_oee = min(per[s]["oee"] for s in sids)
    return dict(
        oee=line_oee, kwh=kwh, idle_kwh=idle_kwh, good=good, scrap=scrap,
        energy_per_good=(kwh / good if good > 0 else float("inf")),
        idle_energy_frac=(idle_kwh / kwh if kwh > 0 else 0.0),
        scrap_rate=(scrap / (good + scrap) if (good + scrap) > 0 else 0.0),
        n_stations=len(sids),
    )


def _recommend(per: dict, stations: dict) -> dict:
    """Route observed inefficiency to IMPROVEMENT (G2: efficiency, not labor intensification)."""
    sids = [s for s in per if not s.startswith("_")]
    if not sids:
        return {}

    def argmax(key):
        return max(sids, key=lambda s: per[s][key])

    def argmin(key):
        return min(sids, key=lambda s: per[s][key])

    bottleneck = argmin("oee")
    energy_hog = argmax("energy_per_good")
    idle_waste = argmax("idle_kwh")
    quality_alert = argmax("scrap_rate")
    return {
        # the line's OEE-limiting station — raise its availability/performance first
        "bottleneck": dict(station=bottleneck, oee=per[bottleneck]["oee"]),
        # highest kWh per good unit — the FOX "cut energy" lever (efficiency, not speed-up)
        "energy_target": dict(station=energy_hog, energy_per_good=per[energy_hog]["energy_per_good"]),
        # most energy burned while NOT producing — schedule / power-down opportunity
        "idle_energy_target": dict(station=idle_waste, idle_kwh=per[idle_waste]["idle_kwh"]),
        # highest scrap-rate — route to vision inspection (manako) + root-cause, never to the worker
        "quality_target": dict(station=quality_alert, scrap_rate=per[quality_alert]["scrap_rate"]),
    }


def _label(stations, sid):
    return stations.get(sid, {}).get(":station/label", sid)


def report_md(stations: dict, ticks: list, res: dict) -> str:
    line = res["_line"]
    rec = res["_recommend"]
    sids = sorted((s for s in res if not s.startswith("_")), key=lambda s: res[s]["oee"])

    L = []
    L.append("# itonami 営み — factory-operations report (aggregate-first)\n")
    L.append("> **G1 — OBSERVE → RECOMMEND only.** itonami never actuates the line "
             "(no-server-key, liveActuation:false). **G2 — STATION/LINE scale ONLY**; "
             "per-worker monitoring is structurally unrepresentable (Wellbecoming §1.13). "
             "Gains route to EFFICIENCY, never to line-speed-up or labor intensification. "
             "States/counts are DISCLOSED scan-cycle facts, not itonami verdicts (G3).\n")
    L.append(f"**Line**: {line['n_stations']} stations · OEE {line['oee']:.1%} (gated by "
             f"weakest station) · {line['kwh']:.0f} kWh · {line['energy_per_good']:.1f} kWh/good · "
             f"idle-energy {line['idle_energy_frac']:.1%} · scrap {line['scrap_rate']:.1%}\n")

    L.append("\n## Per-station OEE (worst-first — the order to improve)\n")
    L.append("| station | OEE | avail | perf | qual | kWh/good | idle-E% |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for s in sids:
        r = res[s]
        epg = "∞" if r["energy_per_good"] == float("inf") else f"{r['energy_per_good']:.1f}"
        L.append(f"| {_label(stations, s)} | {r['oee']:.1%} | {r['availability']:.1%} | "
                 f"{r['performance']:.1%} | {r['quality']:.1%} | {epg} | {r['idle_energy_frac']:.1%} |")

    L.append("\n## Routed findings (to a human / Council — never a write-back)\n")
    L.append(f"- **Bottleneck** → {_label(stations, rec['bottleneck']['station'])} "
             f"(OEE {rec['bottleneck']['oee']:.1%}) — raise availability/performance first.")
    L.append(f"- **Energy target** → {_label(stations, rec['energy_target']['station'])} "
             f"({rec['energy_target']['energy_per_good']:.1f} kWh/good) — efficiency, not speed-up.")
    L.append(f"- **Idle-energy** → {_label(stations, rec['idle_energy_target']['station'])} "
             f"({rec['idle_energy_target']['idle_kwh']:.0f} kWh burned not producing) — "
             "schedule / power-down opportunity.")
    L.append(f"- **Quality** → {_label(stations, rec['quality_target']['station'])} "
             f"(scrap {rec['quality_target']['scrap_rate']:.1%}) — route to vision inspection "
             "(manako) + root-cause; never to the worker.")

    L.append("\n---\n_itonami 営み · ADR-2606082300 · observe→recommend · no-actuation · "
             "station-scale (no worker surveillance) · non-adjudicating. Live OT ingest is "
             "G6/Council-gated._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    res = analyze(stations, ticks)
    (outdir / "operations-report.md").write_text(report_md(stations, ticks, res), encoding="utf-8")
    line = res["_line"]
    rec = res["_recommend"]
    print(f"itonami: {len(stations)} stations, {len(ticks)} ticks → {outdir/'operations-report.md'}")
    print(f"  line OEE {line['oee']:.1%} · bottleneck {rec['bottleneck']['station']} "
          f"· energy target {rec['energy_target']['station']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
