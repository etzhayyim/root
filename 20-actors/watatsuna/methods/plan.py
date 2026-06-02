#!/usr/bin/env python3
"""watatsuna 綿津綱 — resilience → watatsumi cable-laying mission planner.

The "watatsuna knows → watatsumi acts" link (ADR-2606012600). Reads the cable graph,
computes resilience, and emits a watatsumi cable-laying MISSION PLAN that tasks specific
robot classes to make the network MORE robust:

  :lay-diverse-route   for single-cable landing stations (redundancy gaps) — add a diverse
                       landing so one fault no longer isolates the station.
  :pre-stage-repair    for high chokepoint-load straits — pre-position repair capability so
                       restoration is fast when (not if) a fault occurs there.
  :monitor             for brittle systems (single charted chokepoint) — passive DAS watch.

CONSTITUTIONAL (G2 + watatsumi N8): every recommendation is REDUNDANCY or REPAIR or MONITOR.
There is NO interdiction/cut output by construction — the plan can only ADD resilience.
Tedori (grapnel recovery) is tasked REPAIR-ONLY against a faulted cable under a logged,
witness-quorum'd work-order; never against a healthy cable.

stdlib only. Usage:  python3 methods/plan.py [graph.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import analyze  # noqa: E402

# watatsumi cable-laying fleet (data/cable-laying-fleet.kotoba.edn), N8-bound
LAY_ROUTE = ["watatsumi.hibiki.survey", "watatsumi.tsuna-suki", "watatsumi.horinuki",
             "watatsumi.tsugite", "watatsumi.funamori.cable-ship"]
PRE_STAGE = ["watatsumi.tedori", "watatsumi.tsugite", "watatsumi.funamori.cable-ship"]
MONITOR = ["watatsumi.kikimimi"]

TOP_CHOKES = 4  # pre-stage repair at the N most loaded straits


def build_plan(cables, stations, a):
    recs = []

    # 1) redundancy gaps → lay a diverse route (priority = capacity at risk)
    for s in sorted(a["redundancy_gap"], key=lambda k: -a["station_capacity"][k]):
        st = stations[s]
        recs.append({
            ":plan/id": f"plan.lay.{s.split('.')[-1]}",
            ":plan/kind": ":lay-diverse-route",
            ":plan/target-station": s,
            ":plan/priority": a["station_capacity"][s],
            ":plan/rationale": (f"{st.get(':station/name', s)} is served by a single cable — "
                                f"one fault isolates {a['station_capacity'][s]} Tbps. Lay a "
                                f"geographically diverse second landing."),
            ":plan/robots": LAY_ROUTE,
            ":plan/n8-note": "ADD a route; never remove one (N8).",
        })

    # 2) high chokepoint-load → pre-stage repair (+ note diverse-route precedent)
    top = sorted(a["choke_load"], key=lambda k: -a["choke_load"][k])[:TOP_CHOKES]
    for cp in top:
        recs.append({
            ":plan/id": f"plan.repair.{cp.lstrip(':')}",
            ":plan/kind": ":pre-stage-repair",
            ":plan/target-chokepoint": cp.lstrip(":"),
            ":plan/priority": a["choke_load"][cp],
            ":plan/rationale": (f"{a['choke_load'][cp]} Tbps across {a['choke_count'][cp]} cables "
                                f"depend on {cp.lstrip(':')}. Pre-stage repair capability for fast "
                                f"restoration; route new builds diversely around it (cf. Bifrost "
                                f"avoiding the South China Sea)."),
            ":plan/robots": PRE_STAGE,
            ":plan/n8-note": "REPAIR-ONLY staging; Tedori recovers faulted cable under logged G4 quorum.",
        })

    # 3) brittle systems (single charted chokepoint) → DAS monitor
    for c in sorted(cables, key=lambda k: a["cable_diversity"][k]):
        if a["cable_diversity"][c] != 1:
            continue
        cb = cables[c]
        recs.append({
            ":plan/id": f"plan.monitor.{c.split('.')[-1]}",
            ":plan/kind": ":monitor",
            ":plan/target-cable": c,
            ":plan/priority": cb.get(":cable/design-capacity-tbps", 0.0),
            ":plan/rationale": (f"{cb.get(':cable/name', c)} depends on a single charted chokepoint "
                                f"(brittle). Passive DAS watch on its own fibre for early warning."),
            ":plan/robots": MONITOR,
            ":plan/n8-note": "Monitoring only; no location export beyond the cable's own route (G1).",
        })
    return recs


def render_md(recs):
    L = ["# watatsuna 綿津綱 → watatsumi 綿津見 — resilience fleet plan", "",
         "> ADR-2606012600 · **redundancy + repair + monitor ONLY** (G2 + watatsumi N8). "
         "No interdiction output by construction. watatsuna knows; watatsumi acts.", "",
         f"- recommendations: **{len(recs)}**", ""]
    for kind, title in [(":lay-diverse-route", "Lay diverse route (close redundancy gaps)"),
                        (":pre-stage-repair", "Pre-stage repair (high chokepoint-load)"),
                        (":monitor", "Monitor brittle systems (DAS)")]:
        group = [r for r in recs if r[":plan/kind"] == kind]
        if not group:
            continue
        L += [f"## {title}", ""]
        for r in sorted(group, key=lambda r: -r[":plan/priority"]):
            tgt = (r.get(":plan/target-station") or r.get(":plan/target-chokepoint")
                   or r.get(":plan/target-cable"))
            robots = ", ".join(x.split(".")[-1] for x in r[":plan/robots"])
            L += [f"- **{tgt}** _(priority {r[':plan/priority']})_ — {r[':plan/rationale']}",
                  f"  - fleet: `{robots}` · {r[':plan/n8-note']}"]
        L += [""]
    L += ["---", "*Generated by `watatsuna/methods/plan.py`. HONEST: R0/R2 design-only — "
          "recommendations over a bounded `:representative` seed; no live tasking; real "
          "deployment is Council + operator gated. Fleet acts lay/bury/splice/repair/monitor only.*"]
    return "\n".join(L) + "\n"


def render_edn(recs):
    def v(x):
        if isinstance(x, list):
            return "[" + " ".join(f'"{i}"' for i in x) + "]"
        if isinstance(x, str):
            return x if x.startswith(":") else f'"{x}"'
        return str(x)
    L = [";; watatsuna → watatsumi resilience fleet plan (GENERATED). :plan/* recommendations.",
         ";; G2/N8: redundancy + repair + monitor ONLY. ADR-2606012600. DO NOT hand-edit.", "["]
    for r in recs:
        L.append(" {" + " ".join(f"{k} {v(val)}" for k, val in r.items()) + "}")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    if len(argv) > 1 and not argv[1].startswith("--"):
        graph = pathlib.Path(argv[1])
    else:
        merged = here / "data" / "cable-graph.merged.kotoba.edn"
        graph = merged if merged.exists() else here / "data" / "seed-cable-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    cables, stations, links, segs, faults = analyze.classify(analyze.load_edn(graph))
    a = analyze.analyze(cables, stations, links, segs, faults)
    recs = build_plan(cables, stations, a)

    (outdir / "resilience-plan.md").write_text(render_md(recs), encoding="utf-8")
    (outdir / "resilience-plan.kotoba.edn").write_text(render_edn(recs), encoding="utf-8")

    by = lambda k: sum(1 for r in recs if r[":plan/kind"] == k)
    print(f"watatsuna plan from {graph.name}: {len(recs)} recommendations "
          f"({by(':lay-diverse-route')} lay-route · {by(':pre-stage-repair')} pre-stage-repair "
          f"· {by(':monitor')} monitor)")
    print(f"wrote {outdir/'resilience-plan.md'} + {outdir/'resilience-plan.kotoba.edn'}")


if __name__ == "__main__":
    main(sys.argv)
