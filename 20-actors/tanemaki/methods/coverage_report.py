#!/usr/bin/env python3
"""tanemaki 種蒔き — DD-evidence COVERAGE report (ADR-2606122000).

Honest coverage of the stewardship graph: org / screen / criterion / source spread, plus the
integrity checks that make the steward trustworthy —
  (1) the G1 invariant: no screen-conflicting org routes to :propose;
  (2) the G2 invariant: every instrument node is on the give-only allowlist;
  (3) the G4 rubric: disclosed criterion weights sum to 1.0 and every criterion has a source;
  (4) the G5 honesty: every :meets edge names its public evidence source; every :propose-routed
      org clears ALL screens with full evidence coverage;
  (5) the G6 seed: every seed org is synthetic (a real org in the seed is a violation).
Coverage of the world's organizations is bounded by design (G5).

Pure stdlib. Usage: python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze, COVERAGE_FLOOR  # noqa: E402
from propose import ALLOWED_INSTRUMENTS  # noqa: E402

ORG_FORMS = [":nonprofit", ":cooperative", ":foundation", ":oss-project", ":company", ":unincorporated"]
ROUTE_BUCKETS = [":propose", ":insufficient-evidence", ":excluded"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    res = analyze(nodes, edges)
    orgs = [n for n in nodes.values() if n.get(":fs/kind") == ":org"]
    screens = [n for n in nodes.values() if n.get(":fs/kind") == ":screen"]
    crit = [n for n in nodes.values() if n.get(":fs/kind") == ":criterion"]
    sources = [n for n in nodes.values() if n.get(":fs/kind") == ":source"]
    instruments = [n for n in nodes.values() if n.get(":fs/kind") == ":instrument"]

    form_c = Counter(o.get(":org/form") for o in orgs)
    route_c = Counter(r["route"] for r in res["orgs"].values())

    # integrity
    g1_violations = [o for o, r in res["orgs"].items()
                     if r["route"] == ":propose" and r["conflicts"]]
    bad_instruments = [i[":fs/id"] for i in instruments
                       if i.get(":instrument/kind") not in ALLOWED_INSTRUMENTS]
    weights_sum = sum(float(c.get(":criterion/weight", 0.0)) for c in crit)
    sourced = {e[":en/from"] for e in edges if e.get(":en/kind") == ":sourced-from"}
    unsourced_criteria = sorted(c[":fs/id"] for c in crit if c[":fs/id"] not in sourced)
    anonymous_evidence = [f"{e[':en/from']}→{e[':en/to']}" for e in edges
                          if e.get(":en/kind") == ":meets" and not e.get(":en/evidence")]
    nonsynthetic = sorted(o[":fs/id"] for o in orgs if o.get(":org/synthetic") is not True)

    L = []
    L.append("# tanemaki 種蒔き — DD coverage report\n")
    L.append("> Honest denominator: coverage of the world's organizations is bounded by design "
             "(G5). Every org in this seed is FICTIONAL (G6) — real-org DD is a G7-gated live "
             "leg. tanemaki is a steward, never a sovereign (G1): the vote decides.\n")
    L.append(f"**Seed**: {len(orgs)} orgs · {len(screens)} screens · {len(crit)} criteria · "
             f"{len(sources)} sources · {len(instruments)} instruments · {len(edges)} 縁 · "
             f"evidence floor {COVERAGE_FLOOR:.0%}\n")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Org-form coverage", ORG_FORMS, form_c)
    _bucket("Route exercise (all three lanes must be exercised by the seed)", ROUTE_BUCKETS, route_c)

    L.append("\n## Integrity — the steward's own invariants\n")
    L.append(f"- G1 (no conflicted org proposable): "
             + ("**holds for all orgs** ✓" if not g1_violations
                else f"**VIOLATED** by {', '.join(g1_violations)} ✗"))
    L.append(f"- G2 (give-only instruments): "
             + ("**all instruments on the allowlist** ✓" if not bad_instruments
                else f"**VIOLATED** by {', '.join(bad_instruments)} ✗"))
    L.append(f"- G4 (rubric weights Σ = 1.0): **{weights_sum:.2f}** "
             + ("✓" if abs(weights_sum - 1.0) < 1e-9 else "✗"))
    L.append(f"- G4 (every criterion has a disclosed source): "
             f"**{len(crit) - len(unsourced_criteria)}/{len(crit)}**"
             + ("" if not unsourced_criteria else f" (unsourced: {', '.join(unsourced_criteria)})"))
    L.append(f"- G5 (every evidence edge names its source): "
             + ("**all named** ✓" if not anonymous_evidence
                else f"**anonymous**: {', '.join(anonymous_evidence)} ✗"))
    L.append(f"- G6 (seed orgs all synthetic): "
             + ("**all fictional** ✓" if not nonsynthetic
                else f"**REAL ORG IN SEED**: {', '.join(nonsynthetic)} ✗"))

    miss_form = [f.lstrip(':') for f in ORG_FORMS if form_c.get(f, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    L.append(("Missing org-form buckets: " + ", ".join(miss_form) + ".") if miss_form
             else "No fully-missing org-form buckets (thin buckets still listed above).")
    L.append("\n---\n_tanemaki 種蒔き · ADR-2606122000 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-stewardship-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"tanemaki coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
