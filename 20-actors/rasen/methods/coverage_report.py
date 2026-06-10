#!/usr/bin/env python3
"""rasen 螺旋 — public-genetics COVERAGE report (ADR-2606101000).

Honest coverage measurement of the genome graph: how much of the target space the seed
covers — by external denominator (genes, ClinVar variants, dbSNP), by inheritance mode, by
clinical-significance spread, by taxon, by population-aggregate, and by pathway — and a gap
map naming what is thin/missing.

NOT a completeness claim: coverage of *all* genes/variants is ~0 by design (a bounded
:representative seed). This makes the real, useful coverage (the well-characterised
clinically-actionable backbone) measurable, and names the next wave's targets.

Pure stdlib (reuses analyze.load). Usage:
    python3 coverage_report.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load  # noqa: E402

# honest external denominators
GENE_DENOM = [
    ("Human protein-coding genes (~)", 20_000),
    ("HGNC named genes (~)", 43_000),
]
VARIANT_DENOM = [
    ("ClinVar submitted variants (~)", 3_500_000),
    ("ClinVar P/LP variants (~)", 800_000),
    ("dbSNP variants (~)", 1_100_000_000),
]

INHERITANCE = [":AD", ":AR", ":XL", ":mitochondrial", ":complex", ":somatic", ":trait"]
CLINSIG = [":pathogenic", ":likely-pathogenic", ":risk-factor", ":drug-response",
           ":uncertain", ":likely-benign", ":benign", ":protective"]
TAXA = [":homo-sapiens", ":loxodonta", ":oryza-sativa", ":bacteria"]
POPS = [":global", ":AFR", ":AMR", ":EAS", ":EUR", ":SAS"]
PATHWAY_SRC = [":GO", ":reactome", ":kegg"]
THIN = 2  # a bucket with < THIN members is flagged thin


def report(nodes: dict, edges: list) -> str:
    genes = [n for n in nodes.values() if n.get(":genome/kind") == ":gene"]
    variants = [n for n in nodes.values() if n.get(":genome/kind") == ":variant"]
    phenos = [n for n in nodes.values() if n.get(":genome/kind") == ":phenotype"]
    pops = [n for n in nodes.values() if n.get(":genome/kind") == ":population"]
    pathways = [n for n in nodes.values() if n.get(":genome/kind") == ":pathway"]

    inh_c = Counter(p.get(":phenotype/inheritance") for p in phenos)
    taxon_c = Counter(g.get(":gene/taxon") for g in genes)
    pop_c = Counter(p.get(":population/code") for p in pops)
    pw_c = Counter(p.get(":pathway/source") for p in pathways)
    clinsig_c = Counter(e.get(":en/clinsig") for e in edges if e.get(":en/clinsig"))

    L = []
    L.append("# rasen 螺旋 — public-genetics coverage report\n")
    L.append("> Honest denominator: coverage of all genes/variants is ~0 by design (bounded "
             "seed). This names the clinically-actionable backbone covered and the next-wave "
             "gaps. PUBLIC reference data only — no individual genotypes (G1).\n")
    L.append(f"**Seed**: {len(genes)} genes · {len(variants)} variants · {len(phenos)} "
             f"phenotypes · {len(pops)} populations · {len(pathways)} pathways · {len(edges)} 縁\n")

    L.append("\n## Gene coverage vs denominators\n")
    L.append("| denominator | count | seed | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in GENE_DENOM:
        L.append(f"| {name} | {denom:,} | {len(genes)} | {len(genes)/denom:.2e} |")

    L.append("\n## Variant coverage vs denominators\n")
    L.append("| denominator | count | seed | fraction |")
    L.append("|---|---:|---:|---:|")
    for name, denom in VARIANT_DENOM:
        L.append(f"| {name} | {denom:,} | {len(variants)} | {len(variants)/denom:.2e} |")

    L.append("\n## Clinical-significance spread (DISCLOSED facts, not verdicts)\n")
    L.append("| category | edges |")
    L.append("|:--:|---:|")
    for cat in CLINSIG:
        L.append(f"| {cat.lstrip(':')} | {clinsig_c.get(cat, 0)} |")

    def _bucket(title, keys, counter):
        L.append(f"\n## {title}\n")
        L.append("| bucket | count | status |")
        L.append("|---|---:|:--|")
        for k in keys:
            c = counter.get(k, 0)
            status = "— **MISSING**" if c == 0 else ("⚠ thin" if c < THIN else "ok")
            L.append(f"| {k.lstrip(':')} | {c} | {status} |")

    _bucket("Inheritance-mode coverage", INHERITANCE, inh_c)
    _bucket("Taxon coverage (life is broader than humans)", TAXA, taxon_c)
    _bucket("Population-aggregate coverage", POPS, pop_c)
    _bucket("Pathway-source coverage", PATHWAY_SRC, pw_c)

    missing = [b.lstrip(':') for b in INHERITANCE if inh_c.get(b, 0) == 0] + \
              [t.lstrip(':') for t in TAXA if taxon_c.get(t, 0) == 0] + \
              [p.lstrip(':') for p in POPS if pop_c.get(p, 0) == 0] + \
              [s.lstrip(':') for s in PATHWAY_SRC if pw_c.get(s, 0) == 0]
    L.append("\n## Gap map — next-wave targets\n")
    if missing:
        L.append("Missing buckets: " + ", ".join(missing) + ".")
    else:
        L.append("No fully-missing buckets in the tracked spines (thin buckets still listed above).")
    L.append("\n---\n_rasen 螺旋 · ADR-2606101000 · coverage honesty (G5)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-genome-graph.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    (outdir / "coverage-report.md").write_text(report(nodes, edges), encoding="utf-8")
    print(f"rasen coverage → {outdir/'coverage-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
