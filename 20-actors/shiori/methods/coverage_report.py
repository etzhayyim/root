#!/usr/bin/env python3
"""shiori 栞 — wellbecoming-detraction COVERAGE report (ADR-2606082100).

Honest coverage of the detraction graph: by cohort kind, by detractor kind, by detractor
severity, by driver kind, by mitigator kind — with a gap map naming thin/missing buckets.
Coverage of all cohorts/detractors is ~0 by design (a bounded :representative, AGGREGATE seed);
this makes the covered backbone measurable and names the next wave.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators (public wellbeing-research scale context)
DENOMINATORS = [
    ("Adults reporting frequent loneliness (~ share)", "1 in 4"),
    ("Workers reporting chronic work stress (~ share)", "~44%"),
    ("People in housing cost-overburden (OECD, ~)", "tens of millions"),
    ("Tracked Wellbecoming detractor kinds (this seed)", 12),
]

COHORT_KINDS = [":workers", ":gig-workers", ":youth", ":students", ":elderly", ":isolated-aged",
                ":unpaid-carers", ":low-income", ":chronically-ill", ":new-parents"]
DETRACTOR_KINDS = [":precarity", ":overwork", ":isolation", ":addictive-design", ":debt-burden",
                   ":housing-insecurity", ":chronic-pain", ":information-pollution",
                   ":discrimination", ":care-deprivation", ":meaning-deficit", ":sleep-deprivation"]
SEVERITY = [":critical", ":severe", ":moderate", ":mild"]
DRIVER_KINDS = [":always-on-work-culture", ":engagement-maximizing-design", ":high-cost-credit",
                ":thin-safety-net", ":unaffordable-housing-market", ":care-infrastructure-gap",
                ":algorithmic-feed", ":job-insecurity-norm"]
MITIGATOR_KINDS = [":social-connection", ":secure-housing", ":meaningful-work", ":rest-recovery",
                   ":mutual-aid", ":treatment-access", ":financial-stability",
                   ":information-hygiene", ":care-support", ":time-sovereignty"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    cohorts = [n for n in nodes.values() if n.get(":organism/kind") == ":cohort"]
    detrs = [n for n in nodes.values() if n.get(":organism/kind") == ":detractor"]
    drvs = [n for n in nodes.values() if n.get(":organism/kind") == ":driver"]
    mits = [n for n in nodes.values() if n.get(":organism/kind") == ":mitigator"]

    coh_c = Counter(c.get(":cohort/kind") for c in cohorts)
    detr_c = Counter(d.get(":detractor/kind") for d in detrs)
    sev_c = Counter(d.get(":detractor/severity") for d in detrs)
    drv_c = Counter(d.get(":driver/kind") for d in drvs)
    mit_c = Counter(m.get(":mitigator/kind") for m in mits)

    L = []
    L.append("# shiori 栞 — wellbecoming-detraction coverage report\n")
    L.append("> Honest denominator: coverage of all cohorts/detractors is ~0 by design (bounded "
             "AGGREGATE seed; G1 = no individuals). This names the covered backbone and the "
             "next-wave gaps.\n")
    L.append(f"**Seed**: {len(cohorts)} cohorts · {len(detrs)} detractors · {len(drvs)} drivers "
             f"· {len(mits)} mitigators · {len(edges)} 縁\n")

    L.append("\n## Scale context (modelled as cohorts, not individuals — by design, G1)\n")
    L.append("| denominator | value |")
    L.append("|---|---:|")
    for name, val in DENOMINATORS:
        L.append(f"| {name} | {val} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Cohort-kind coverage", COHORT_KINDS, coh_c)
    _bucket("Detractor-kind coverage", DETRACTOR_KINDS, detr_c)
    _bucket("Detractor-severity coverage (DISCLOSED)", SEVERITY, sev_c)
    _bucket("Driver-kind coverage (structural patterns)", DRIVER_KINDS, drv_c)
    _bucket("Mitigator-kind coverage (the 守り)", MITIGATOR_KINDS, mit_c)

    missing = [k.lstrip(':') for k in COHORT_KINDS if coh_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in DETRACTOR_KINDS if detr_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in DRIVER_KINDS if drv_c.get(k, 0) == 0] + \
              [k.lstrip(':') for k in MITIGATOR_KINDS if mit_c.get(k, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_shiori 栞 · ADR-2606082100 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-wellbecoming-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"shiori coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
