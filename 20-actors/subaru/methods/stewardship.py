#!/usr/bin/env python3
"""subaru 昴 — orbital stewardship (G5; couples hoshimori + torifune G5).

ADR-2606162355. Every occupied :shell MUST carry a :disposes edge to a :disposal-plan; an
occupied shell with none is REFUSED (raises). Also checks night-sky brightness mitigation
(darksat, Wellbecoming §1.13) on the bus. Emits the deorbit-debt as a hoshimori-consumable
stewardship input — subaru must reduce, not add to, the congestion hoshimori routes around.

Pure stdlib. Usage: python3 stewardship.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from link_budget import load, check_g1  # noqa: E402


def stewardship(nodes: dict, edges: list):
    check_g1(nodes)
    occupied = [e[":en/to"] for e in edges if e.get(":en/kind") == ":occupies"]
    rows, total_debt = [], 0.0
    for sid in occupied:
        dplans = [nodes[e[":en/to"]] for e in edges
                  if e.get(":en/kind") == ":disposes" and e.get(":en/from") == sid
                  and e.get(":en/to") in nodes]
        if not dplans:
            raise ValueError(f"G5 violation: occupied shell {sid} has NO disposal plan — refused")
        debt = sum(float(d.get(":disposal/deorbit-debt", 0.0)) for d in dplans)
        total_debt += debt
        rows.append({"shell": sid, "label": nodes.get(sid, {}).get(":organism/label", sid),
                     "plans": [(d[":organism/id"], d.get(":disposal/method")) for d in dplans],
                     "deorbit_debt": debt})

    buses = [n for n in nodes.values() if n.get(":organism/kind") == ":bus"]
    darksat_all = bool(buses) and all(bool(b.get(":bus/darksat")) for b in buses)
    return {"shells": rows, "total_deorbit_debt": total_debt, "darksat_all": darksat_all,
            "g5_pass": all(r["deorbit_debt"] <= 0.0 for r in rows) and darksat_all}


def report_md(nodes, edges, res) -> str:
    L = ["# subaru 昴 — orbital stewardship report (G5; feeds hoshimori)\n"]
    L.append("> **G5 — orbital stewardship.** Low-deorbit-debt orbit + mandatory disposal plan "
             "+ night-sky brightness mitigation (darksat, Wellbecoming §1.13). subaru's "
             "footprint feeds hoshimori's congestion integral and must REDUCE, not add to it.\n")
    L.append("\n| occupied shell | disposal method(s) | deorbit-debt |")
    L.append("|---|---|---:|")
    for r in res["shells"]:
        methods = ", ".join(m.lstrip(":") for _, m in r["plans"])
        L.append(f"| {r['label']} | {methods} | {r['deorbit_debt']:g} |")
    L.append(f"\n**Total deorbit-debt routed to hoshimori: {res['total_deorbit_debt']:g}** · "
             f"darksat applied to all buses: {'✅' if res['darksat_all'] else '❌'}\n")
    L.append(f"\n**G5: {'✅ PASS' if res['g5_pass'] else '❌ FAIL'}**\n")
    L.append("\n---\n_subaru 昴 · ADR-2606162355 · orbital-stewardship · couples hoshimori._\n")
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
    res = stewardship(nodes, edges)
    (outdir / "stewardship-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"subaru stewardship: {len(res['shells'])} occupied shell(s), debt "
          f"{res['total_deorbit_debt']:g}, G5 {'PASS' if res['g5_pass'] else 'FAIL'} "
          f"→ {outdir/'stewardship-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
