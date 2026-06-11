#!/usr/bin/env python3
"""kadode 門出 — labour-exit COVERAGE report (ADR-2606112238).

Honest coverage of the resignation graph: scenario / ground / route / risk spread, plus two
integrity checks — (1) every scenario reaches a recommended lawful route, and (2) the UPL
invariant holds (no negotiation-needing scenario resolves to a non-negotiating 使者/self route).
Coverage of all employment situations is bounded by design (G5).

Pure stdlib. Usage: python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, recommend_route, NEGOTIATING_ACTORS  # noqa: E402

EMPLOYMENT = [":no-fixed-term", ":fixed-term", ":fixed-term-1yr+", ":probation", ":dispatch"]
ROUTE_ACTORS = [":worker-self", ":kadode-messenger", ":labor-union", ":lawyer"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    scen = [n for n in nodes.values() if n.get(":lx/kind") == ":scenario"]
    grounds = [n for n in nodes.values() if n.get(":lx/kind") == ":ground"]
    routes = [n for n in nodes.values() if n.get(":lx/kind") == ":route"]
    docs = [n for n in nodes.values() if n.get(":lx/kind") == ":document"]
    risks = [n for n in nodes.values() if n.get(":lx/kind") == ":risk"]

    emp_c = Counter(s.get(":scenario/employment") for s in scen)
    route_c = Counter(r.get(":route/actor") for r in routes)

    # integrity: every scenario routes, and UPL invariant holds
    unrouted, upl_violations = [], []
    for s in scen:
        sid = s[":lx/id"]
        rec = recommend_route(sid, nodes, edges)
        if not rec.get("route"):
            unrouted.append(sid)
        if rec.get("needs_negotiation") and rec.get("route_actor") not in NEGOTIATING_ACTORS:
            upl_violations.append(sid)

    # which employer-risk patterns have a countering ground
    countered = {e[":en/to"] for e in edges if e.get(":en/kind") == ":counters"}
    risk_ids = {r[":lx/id"] for r in risks}
    uncountered = sorted(risk_ids - countered)

    L = []
    L.append("# kadode 門出 — labour-exit coverage report\n")
    L.append("> Honest denominator: coverage of all employment situations is bounded by design "
             "(G5). PUBLIC Japanese labour law only; kadode is a 使者 + concierge, never the "
             "practice of law (G1).\n")
    L.append(f"**Seed**: {len(scen)} scenarios · {len(grounds)} grounds · {len(routes)} routes "
             f"· {len(docs)} documents · {len(risks)} employer-risk patterns · {len(edges)} 縁\n")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Employment-type coverage", EMPLOYMENT, emp_c)
    _bucket("Route coverage (the escalation ladder)", ROUTE_ACTORS, route_c)

    L.append("\n## Integrity — routing completeness + the UPL invariant\n")
    L.append(f"- scenarios reaching a lawful route: **{len(scen) - len(unrouted)}/{len(scen)}**"
             + ("" if not unrouted else f" (unrouted: {', '.join(unrouted)})"))
    L.append(f"- UPL invariant (negotiation ⇒ union/lawyer, never 使者/self): "
             + ("**holds for all scenarios** ✓" if not upl_violations
                else f"**VIOLATED** by {', '.join(upl_violations)} ✗"))
    L.append(f"- employer-risk patterns with a countering legal ground: "
             f"**{len(risk_ids) - len(uncountered)}/{len(risk_ids)}**"
             + ("" if not uncountered else f" (uncountered: {', '.join(uncountered)})"))

    miss_emp = [e.lstrip(':') for e in EMPLOYMENT if emp_c.get(e, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    L.append(("Missing employment buckets: " + ", ".join(miss_emp) + ".") if miss_emp
             else "No fully-missing employment buckets (thin buckets still listed above).")
    L.append("\n---\n_kadode 門出 · ADR-2606112238 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-resignation-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"kadode coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
