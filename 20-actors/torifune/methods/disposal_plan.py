#!/usr/bin/env python3
"""torifune 鳥船 — debris-responsibility / disposal plan (G5; couples hoshimori).

ADR-2606162355. Every :mission MUST carry at least one :disposes edge to a :disposal-plan; a
mission with none is REFUSED (raises). Emits the total added deorbit-debt as a
hoshimori-consumable stewardship input — torifune may not create the congestion hoshimori
routes around (G5).

Pure stdlib. Usage: python3 disposal_plan.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ascent_sim import load  # noqa: E402


def plan(nodes: dict, edges: list):
    """For each mission, gather its disposal plans; refuse a mission with none (G5)."""
    missions = [n for n in nodes.values() if n.get(":organism/kind") == ":mission"]
    out, total_debt = [], 0.0
    for m in missions:
        mid = m[":organism/id"]
        dplans = [nodes[e[":en/to"]] for e in edges
                  if e.get(":en/kind") == ":disposes" and e.get(":en/from") == mid
                  and e.get(":en/to") in nodes]
        if not dplans:
            raise ValueError(f"G5 violation: mission {mid} has NO disposal plan — refused")
        debt = sum(float(d.get(":disposal/deorbit-debt", 0.0)) for d in dplans)
        total_debt += debt
        out.append({"mission": mid, "label": m.get(":organism/label", mid),
                    "plans": [(d[":organism/id"], d.get(":disposal/method"),
                               float(d.get(":disposal/deorbit-debt", 0.0))) for d in dplans],
                    "deorbit_debt": debt})
    return {"missions": out, "total_deorbit_debt": total_debt}


def emit_edn(res) -> str:
    """A hoshimori-consumable disposal plan (deorbit-debt feeds the stewardship integral)."""
    L = [";; torifune 鳥船 — GENERATED disposal plan (ADR-2606162355). DO NOT hand-edit.",
         ";; G5 debris-responsibility — deorbit-debt is an INPUT to hoshimori stewardship.",
         "["]
    for m in res["missions"]:
        for pid, method, debt in m["plans"]:
            L.append(f'{{:disposal/of "{m["mission"]}" :disposal/plan "{pid}" '
                     f':disposal/method {method} :disposal/deorbit-debt {debt:g} '
                     f':routed-to :hoshimori-stewardship}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-ama-vehicle.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = plan(nodes, edges)
    (outdir / "disposal-plan.kotoba.edn").write_text(emit_edn(res), encoding="utf-8")
    print(f"torifune disposal: {len(res['missions'])} mission(s), total deorbit-debt "
          f"{res['total_deorbit_debt']:g} → {outdir/'disposal-plan.kotoba.edn'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
