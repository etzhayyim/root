#!/usr/bin/env python3
"""hoshimori 星守 — orbital COVERAGE report (ADR-2606073600).

Honest coverage of the orbital graph: by orbital regime, by operator kind, by hazard kind,
by service kind — with a gap map naming thin/missing buckets. Coverage of all catalogued
objects is ~0 by design (a bounded :representative seed at shell-aggregate granularity); this
makes the covered regime/hazard backbone measurable and names the next wave.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators for the OBJECT count (we model shells, not objects — by design)
DENOMINATORS = [
    ("Active satellites (~)", 10_000),
    ("Tracked debris >10cm (~)", 36_000),
    ("Estimated debris >1cm (~)", 1_000_000),
]

REGIMES = [":leo-low", ":leo-high", ":sso", ":meo", ":geo", ":heo"]
OP_KINDS = [":constellation", ":single-asset", ":station", ":agency"]
HAZARDS = [":debris-density", ":conjunction", ":congestion", ":asat-debris-event",
           ":space-weather", ":deorbit-shortfall"]
SERVICES = [":pnt", ":broadband", ":earth-observation", ":weather", ":science"]
THIN = 1  # at shell granularity a single shell per regime is expected; flag only zero


def report(nodes: dict, edges: list) -> str:
    shells = [n for n in nodes.values() if n.get(":organism/kind") == ":shell"]
    ops = [n for n in nodes.values() if n.get(":organism/kind") == ":operator"]
    hazs = [n for n in nodes.values() if n.get(":organism/kind") == ":hazard"]
    svcs = [n for n in nodes.values() if n.get(":organism/kind") == ":service"]

    reg_c = Counter(s.get(":shell/regime") for s in shells)
    op_c = Counter(o.get(":op/kind") for o in ops)
    hz_c = Counter(h.get(":hazard/kind") for h in hazs)
    sv_c = Counter(s.get(":service/kind") for s in svcs)

    L = []
    L.append("# hoshimori 星守 — orbital coverage report\n")
    L.append("> Honest denominator: hoshimori models orbital SHELLS (regime-aggregate), not "
             "per-object ephemeris — coverage of all catalogued objects is ~0 BY DESIGN (G1). "
             "This names the regime/hazard backbone covered and the next-wave gaps.\n")
    L.append(f"**Seed**: {len(shells)} shells · {len(ops)} operators · {len(hazs)} hazards · "
             f"{len(svcs)} services · {len(edges)} 縁\n")

    L.append("\n## Object-population context (modelled as shells, not objects — by design)\n")
    L.append("| denominator | count |")
    L.append("|---|---:|")
    for name, denom in DENOMINATORS:
        L.append(f"| {name} | {denom:,} |")

    def _bucket(title, keys, counter, thin=THIN):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < thin else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Orbital-regime coverage", REGIMES, reg_c)
    _bucket("Operator-kind coverage", OP_KINDS, op_c)
    _bucket("Hazard-kind coverage", HAZARDS, hz_c)
    _bucket("Service-kind coverage", SERVICES, sv_c)

    missing = [r.lstrip(':') for r in REGIMES if reg_c.get(r, 0) == 0] + \
              [o.lstrip(':') for o in OP_KINDS if op_c.get(o, 0) == 0] + \
              [h.lstrip(':') for h in HAZARDS if hz_c.get(h, 0) == 0] + \
              [s.lstrip(':') for s in SERVICES if sv_c.get(s, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines.")
    L.append("\n---\n_hoshimori 星守 · ADR-2606073600 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-orbit-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"hoshimori coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
