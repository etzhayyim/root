#!/usr/bin/env python3
"""itonami 営み — R10 multi-line FLEET rollup (ADR-2606082300).

A plant brain oversees MORE than one line. fleet.py groups stations by :station/line, runs the
single-line analysis per line, and rolls up a plant view: per-line OEE / energy / scrap +
alert counts, then RANKS the lines by attention-need so the plant lead knows which line to walk
to first. The whole-plant scope FOX targets, made charter-clean.

  split_lines  — group (stations, ticks) by :station/line
  rollup       — per line: analyze + alert.evaluate → {oee, energy/good, scrap, critical, warn}
  rank         — order lines worst-first (critical alerts, then lowest OEE)

CONSTITUTIONAL (read before any change):
  G1 — observe → recommend (which line to attend to); never actuates any line.
  G2 — line/station scale only; no worker dimension. Ranking is of LINES, never of people.
  G3 — non-adjudicating; per-line KPIs are read-time aggregates, datoms transient.

Pure stdlib (no numpy). Usage:
    python3 fleet.py [fleet_seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402
import alert  # noqa: E402


def split_lines(stations: dict, ticks: list) -> dict:
    """Group (stations, ticks) into {line_id: (line_stations, line_ticks)}."""
    by_line_st = defaultdict(dict)
    for sid, st in stations.items():
        by_line_st[st.get(":station/line", ":line.unknown")][sid] = st
    out = {}
    for line, lst in by_line_st.items():
        lt = [tk for tk in ticks if tk.get(":tick/station") in lst]
        out[line] = (lst, lt)
    return out


def rollup(stations: dict, ticks: list, thresholds: dict | None = None) -> dict:
    """Per-line KPIs + alert counts, plus a plant aggregate and attention ranking."""
    lines = split_lines(stations, ticks)
    per_line = {}
    for line, (lst, lt) in lines.items():
        res = analyze(lst, lt)
        alerts = alert.evaluate(lst, res, thresholds)
        ac = alert.counts(alerts)
        L = res["_line"]
        per_line[line] = dict(
            oee=L["oee"], energy_per_good=L["energy_per_good"], scrap_rate=L["scrap_rate"],
            good=L["good"], kwh=L["kwh"], n_stations=L["n_stations"],
            critical=ac["critical"], warn=ac["warn"],
        )

    ranked = sorted(per_line, key=lambda ln: (-per_line[ln]["critical"], per_line[ln]["oee"]))
    plant = dict(
        n_lines=len(per_line),
        good=sum(per_line[l]["good"] for l in per_line),
        kwh=sum(per_line[l]["kwh"] for l in per_line),
        critical=sum(per_line[l]["critical"] for l in per_line),
        warn=sum(per_line[l]["warn"] for l in per_line),
        worst_line=(ranked[0] if ranked else None),
    )
    return {"per_line": per_line, "ranked": ranked, "plant": plant}


def report_md(fleet: dict) -> str:
    p = fleet["plant"]
    L = []
    L.append("# itonami 営み — R10 fleet (multi-line plant) rollup\n")
    L.append("> **G1** recommends which line to attend to; never actuates. **G2** ranks LINES, "
             "never people (no worker dimension). **G3** per-line KPIs are read-time aggregates.\n")
    L.append(f"\n**Plant**: {p['n_lines']} lines · {p['good']:.0f} good units · {p['kwh']:.0f} kWh "
             f"· {p['critical']} critical / {p['warn']} warn · attend first: **{p['worst_line']}**\n")
    L.append("\n## Lines (worst-first — attention order)\n")
    L.append("| rank | line | OEE | kWh/good | scrap | critical | warn |")
    L.append("|---:|---|---:|---:|---:|---:|---:|")
    for i, ln in enumerate(fleet["ranked"], 1):
        r = fleet["per_line"][ln]
        epg = "∞" if r["energy_per_good"] == float("inf") else f"{r['energy_per_good']:.1f}"
        L.append(f"| {i} | {ln} | {r['oee']:.1%} | {epg} | {r['scrap_rate']:.1%} | "
                 f"{r['critical']} | {r['warn']} |")
    L.append("\n---\n_itonami 営み R10 · ADR-2606082300 · plant-scope · "
             "recommend-not-actuate · ranks-lines-not-people._\n")
    return "\n".join(L)


def emit(fleet: dict, tx: int = 1) -> str:
    """Transient EAVT fleet datoms (computed on read, never durable — G3)."""
    L = [";; itonami R10 fleet rollup — TRANSIENT (:bond/is-transient true), G1/G3.", "["]
    for ln in fleet["ranked"]:
        r = fleet["per_line"][ln]
        L.append(f"[{ln} :fleet/oee {r['oee']:g} {tx} :derived] ;; :bond/is-transient true")
        L.append(f"[{ln} :fleet/critical-alerts {r['critical']} {tx} :derived] ;; :bond/is-transient true")
    if fleet["plant"]["worst_line"]:
        L.append(f"[:plant :fleet/attend-first {fleet['plant']['worst_line']} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-fleet-ops.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    fleet = rollup(stations, ticks)
    (outdir / "fleet-rollup.md").write_text(report_md(fleet), encoding="utf-8")
    (outdir / "itonami-fleet.kotoba.edn").write_text(emit(fleet, tx), encoding="utf-8")
    p = fleet["plant"]
    print(f"itonami R10: {p['n_lines']} lines · attend first {p['worst_line']} "
          f"· {p['critical']} critical → {outdir}")
    for ln in fleet["ranked"]:
        r = fleet["per_line"][ln]
        print(f"  {ln}: OEE {r['oee']:.1%}, {r['critical']} critical")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
