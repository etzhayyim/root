#!/usr/bin/env python3
"""hinagata 雛形 — legal-template-commons COVERAGE report (ADR-2606111954).

Honest coverage measurement of the template graph: how much of the target space the seed
covers — by template-family / concept, by jurisdiction, by legal system, by clause role, by
citation force — plus a STATUTE-BINDING check (which clauses are NOT yet anchored to any
public statute) and a gap map naming what is thin/missing.

NOT a completeness claim: coverage of *all* template families / *all* jurisdictions is ~0 by
design (a bounded :representative seed). This makes the real, useful coverage (the
clause↔statute backbone) measurable and names the next wave's targets (more jurisdictions,
more families) — the worklist for the G7-gated legal-corpus binding (ADR-2605262800).

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, CITE_KINDS  # noqa: E402

# honest external denominators (orders of magnitude; the point is ~0 coverage by design)
CONCEPT_DENOM = [
    ("Common contract families (~)", 120),
    ("Distinct legal concepts in general practice (~)", 2_000),
]
JURISDICTION_DENOM = [
    ("UN member states (~)", 193),
    ("World legal jurisdictions incl. sub-national (~)", 320),
]

SYSTEMS = [":civil-law", ":common-law", ":mixed", ":religious", ":customary", ":international"]
CLAUSE_ROLES = [":definitions", ":payment", ":term", ":termination", ":confidentiality",
                ":ip-assignment", ":ip-license", ":warranty", ":liability", ":governing-law",
                ":dispute", ":privacy", ":data-rights", ":force-majeure", ":no-interest",
                ":cooling-off", ":signature", ":boilerplate"]
FORCES = [":mandated", ":cited", ":referenced"]
THIN = 2  # a bucket with < THIN members is flagged thin


def report(nodes: dict, edges: list) -> str:
    tmpls = [n for n in nodes.values() if n.get(":lt/kind") == ":template"]
    clauses = [n for n in nodes.values() if n.get(":lt/kind") == ":clause"]
    statutes = [n for n in nodes.values() if n.get(":lt/kind") == ":statute"]
    jurisdictions = [n for n in nodes.values() if n.get(":lt/kind") == ":jurisdiction"]
    concepts = [n for n in nodes.values() if n.get(":lt/kind") == ":concept"]

    sys_c = Counter(j.get(":jurisdiction/system") for j in jurisdictions)
    role_c = Counter(c.get(":clause/role") for c in clauses)
    force_c = Counter(e.get(":en/force") for e in edges if e.get(":en/force"))

    # which clauses cite at least one statute (the binding backbone) vs orphans
    cited_clauses = {e.get(":en/from") for e in edges
                     if e.get(":en/kind") in CITE_KINDS
                     and nodes.get(e.get(":en/from"), {}).get(":lt/kind") == ":clause"}
    clause_ids = {n[":lt/id"] for n in clauses}
    unbound = sorted(clause_ids - cited_clauses)

    L = []
    L.append("# hinagata 雛形 — legal-template-commons coverage report\n")
    L.append("> Honest denominator: coverage of all template families / all jurisdictions is "
             "~0 by design (bounded seed). This names the clause↔statute backbone covered and "
             "the next-wave gaps. PUBLIC, openly-licensed reference templates only — never "
             "advice (G1).\n")
    L.append(f"**Seed**: {len(tmpls)} templates · {len(clauses)} clauses · {len(statutes)} "
             f"statutes · {len(jurisdictions)} jurisdictions · {len(concepts)} concepts · "
             f"{len(edges)} 縁\n")

    L.append("\n## Concept / family coverage vs denominators\n")
    L.append("| denominator | count | seed concepts | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in CONCEPT_DENOM:
        L.append(f"| {name} | {denom:,} | {len(concepts)} | {len(concepts)/denom:.2e} |")

    L.append("\n## Jurisdiction coverage vs denominators\n")
    L.append("| denominator | count | seed jurisdictions | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in JURISDICTION_DENOM:
        L.append(f"| {name} | {denom:,} | {len(jurisdictions)} | {len(jurisdictions)/denom:.2e} |")

    L.append("\n## Citation-force spread (DISCLOSED facts, not verdicts)\n")
    L.append("| force | edges |")
    L.append("|:--:|---:|")
    for f in FORCES:
        L.append(f"| {f.lstrip(':')} | {force_c.get(f, 0)} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Legal-system coverage (law is plural)", SYSTEMS, sys_c)
    _bucket("Clause-role coverage", CLAUSE_ROLES, role_c)

    L.append("\n## Statute-binding integrity — clauses NOT yet anchored to any public statute\n")
    L.append("_Every clause SHOULD eventually cite the law it rests on (gap #2 of the design). "
             "Unbound clauses are the next-wave binding worklist, not a defect — they are "
             "honestly surfaced (G5)._\n")
    if unbound:
        L.append(f"**{len(unbound)}/{len(clauses)} clauses unbound**: "
                 + ", ".join(u.lstrip("cl.") if u.startswith("cl.") else u for u in unbound) + ".")
    else:
        L.append(f"All {len(clauses)} clauses cite at least one public statute.")

    missing = [s.lstrip(':') for s in SYSTEMS if sys_c.get(s, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing legal-system buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing legal-system buckets (thin buckets still listed above).")
    L.append("\n---\n_hinagata 雛形 · ADR-2606111954 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-legal-template-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"hinagata coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
