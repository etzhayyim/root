#!/usr/bin/env python3
"""tsugite 継ぎ手 — peoples-continuity COVERAGE report (ADR-2606073800).

Honest coverage of the peoples graph: by people kind, by language vitality, by pressure kind,
by haven kind — with a gap map naming thin/missing buckets. Coverage of all peoples/languages
is ~0 by design (a bounded :representative, AGGREGATE seed); this makes the covered backbone
measurable and names the next wave.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators
DENOMINATORS = [
    ("Forcibly displaced worldwide (UNHCR, ~)", 120_000_000),
    ("Stateless people (~)", 4_400_000),
    ("Living languages (Ethnologue, ~)", 7_160),
    ("Endangered languages (~)", 3_000),
]

PEOPLE_KINDS = [":refugee-population", ":stateless", ":displaced", ":indigenous",
                ":diaspora", ":language-community"]
VITALITY = [":vulnerable", ":definitely-endangered", ":severely-endangered",
            ":critically-endangered", ":extinct", ":safe"]
PRESSURE_KINDS = [":armed-conflict", ":persecution", ":statelessness", ":disaster-climate",
                  ":economic", ":assimilation-policy", ":language-shift", ":education-exclusion"]
HAVEN_KINDS = [":asylum-system", ":resettlement", ":statelessness-reduction",
               ":mother-tongue-education", ":revitalization-program", ":cultural-archive"]
THIN = 2


def report(nodes: dict, edges: list) -> str:
    peoples = [n for n in nodes.values() if n.get(":organism/kind") == ":people"]
    langs = [n for n in nodes.values() if n.get(":organism/kind") == ":language"]
    press = [n for n in nodes.values() if n.get(":organism/kind") == ":pressure"]
    havens = [n for n in nodes.values() if n.get(":organism/kind") == ":haven"]

    pk_c = Counter(p.get(":people/kind") for p in peoples)
    vit_c = Counter(l.get(":lang/vitality") for l in langs)
    pr_c = Counter(p.get(":pressure/kind") for p in press)
    hv_c = Counter(h.get(":haven/kind") for h in havens)

    L = []
    L.append("# tsugite 継ぎ手 — peoples-continuity coverage report\n")
    L.append("> Honest denominator: coverage of all peoples/languages is ~0 by design (bounded "
             "AGGREGATE seed; G1 = no individuals). This names the covered backbone and the "
             "next-wave gaps.\n")
    L.append(f"**Seed**: {len(peoples)} peoples · {len(langs)} languages · {len(press)} pressures "
             f"· {len(havens)} havens · {len(edges)} 縁\n")

    L.append("\n## Scale context (modelled as collectives, not individuals — by design, G1)\n")
    L.append("| denominator | count |")
    L.append("|---|---:|")
    for name, denom in DENOMINATORS:
        L.append(f"| {name} | {denom:,} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("People-kind coverage", PEOPLE_KINDS, pk_c)
    _bucket("Language-vitality coverage (DISCLOSED)", VITALITY, vit_c)
    _bucket("Pressure-kind coverage", PRESSURE_KINDS, pr_c)
    _bucket("Haven-kind coverage", HAVEN_KINDS, hv_c)

    missing = [p.lstrip(':') for p in PEOPLE_KINDS if pk_c.get(p, 0) == 0] + \
              [v.lstrip(':') for v in VITALITY if vit_c.get(v, 0) == 0] + \
              [p.lstrip(':') for p in PRESSURE_KINDS if pr_c.get(p, 0) == 0] + \
              [h.lstrip(':') for h in HAVEN_KINDS if hv_c.get(h, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_tsugite 継ぎ手 · ADR-2606073800 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-peoples-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"tsugite coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
