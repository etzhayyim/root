#!/usr/bin/env python3
"""subaru 昴 — coverage as §1.16 Social Security reach (G3; cash≡0 in-kind).

ADR-2606162355. Computes connectivity reach as the served unconnected / disaster service-areas
(the §1.16 in-kind entitlement), NOT a market map. Reach is the integral of incident :serves 縁
weighted by coverage-pct, over service-areas that are :area/unconnected or :area/disaster.

Pure stdlib. Usage: python3 coverage.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from link_budget import load, check_g1  # noqa: E402


def coverage(nodes: dict, edges: list):
    """§1.16 reach (computed on read; transient — N1)."""
    check_g1(nodes)
    areas = {nid: n for nid, n in nodes.items()
             if n.get(":organism/kind") == ":service-area"}
    served = {}
    for e in edges:
        if e.get(":en/kind") == ":serves" and e.get(":en/to") in areas:
            served[e[":en/to"]] = float(e.get(":en/coverage-pct", 0.0) or 0.0)

    rows, reach = [], 0.0
    for aid, a in areas.items():
        cov = served.get(aid, 0.0)
        priority = bool(a.get(":area/unconnected")) or bool(a.get(":area/disaster"))
        if priority:
            reach += cov
        rows.append({"area": aid, "label": a.get(":organism/label"),
                     "region": a.get(":area/region"), "coverage_pct": cov,
                     "ss_priority": priority,
                     "unconnected": bool(a.get(":area/unconnected")),
                     "disaster": bool(a.get(":area/disaster"))})
    rows.sort(key=lambda r: (-int(r["ss_priority"]), -r["coverage_pct"]))
    n_priority = sum(1 for r in rows if r["ss_priority"])
    return {"areas": rows, "ss_reach": reach, "n_priority": n_priority}


def report_md(nodes, edges, res) -> str:
    L = ["# subaru 昴 — coverage as §1.16 Social Security reach\n"]
    L.append("> **G3 — non-profit / no-ads / cash≡0.** Connectivity is §1.16 in-kind social "
             "security (covenantal-universal) — coverage is REACH to the unconnected + disaster "
             "zones, NOT a market/ARPU map. Service keyed to aggregate region (G1).\n")
    L.append("\n| service area (region) | coverage | §1.16 priority |")
    L.append("|---|---:|:--:|")
    for r in res["areas"]:
        tag = ("unconnected" if r["unconnected"] else
               "disaster" if r["disaster"] else "baseline")
        L.append(f"| {r['region']} ({tag}) | {r['coverage_pct']*100:.0f}% | "
                 f"{'✅' if r['ss_priority'] else '—'} |")
    L.append(f"\n**§1.16 reach (Σ coverage over {res['n_priority']} priority areas): "
             f"{res['ss_reach']:.2f}**\n")
    L.append("\n---\n_subaru 昴 · ADR-2606162355 · §1.16 in-kind · cash≡0 · no-ads._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-constellation.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = coverage(nodes, edges)
    (outdir / "coverage-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"subaru coverage: {res['n_priority']} §1.16-priority areas, reach "
          f"{res['ss_reach']:.2f} → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
