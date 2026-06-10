#!/usr/bin/env python3
"""rasen 螺旋 — edge-primary clinical/functional evidence analyzer over the public-genetics graph.

ADR-2606101000. Reads a kotoba-EDN genome graph (:genome/* nodes + :en/* 縁 over the
genome-ontology), and surfaces — aggregate-first — where integrated CLINICAL / FUNCTIONAL
evidence burden accumulates over a GENE, routed to CARE & RESEARCH (release), and where
pleiotropy makes that burden cascade across phenotypes / pathways.

CONSTITUTIONAL (read before any change):
  N1 / G2 — edge-primary. evidence/burden lives ONLY on edges (:en/grasping-load weighted by
    DISCLOSED :en/clinsig). A gene's care-priority is the INTEGRAL of its incident
    variant-association + gene-linkage 縁 — computed on READ, never a stored per-gene score.
    There is no :genome/score-of-gene.
  G1 — CARE / RESEARCH map, never an individual-genotype registry or discrimination tool. No
    individual genotypes / sample sequence are read or emitted; population readouts are
    super-population AGGREGATE only; chromosomal location is COARSE (cytoband). The routing is
    care, research and equity — never insurance / employment / eugenic / forensic targeting.
  N3 — non-adjudicating. Clinical-significance categories are DISCLOSED curated facts
    (ClinVar / OMIM / GWAS-Catalog style), never rasen verdicts. rasen never diagnoses, never
    rates a person, never asserts the worth of any genotype.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 analyze.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, pathlib
from collections import defaultdict

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


# ── disclosed clinical-significance → representative evidence weight (NOT a verdict; mirrors schema)
CLINSIG_WEIGHT = {":pathogenic": 1.0, ":likely-pathogenic": 0.8, ":risk-factor": 0.5,
                  ":drug-response": 0.4, ":uncertain": 0.3, ":vus": 0.3,
                  ":likely-benign": 0.1, ":benign": 0.05, ":protective": 0.1}

ASSOC_KINDS = {":associated-with"}          # variant → phenotype (attributed to its gene)
LINK_KINDS = {":linked-to"}                 # gene → phenotype (Mendelian, src IS the gene)
PATHWAY_KINDS = {":participates-in", ":interacts-with"}
LOCATED_KINDS = {":located-in"}             # variant → gene (provenance)
FREQ_KINDS = {":allele-frequency"}          # population → variant (AGGREGATE only)


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a public-genetics EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":genome/id" in f:
            nodes[f[":genome/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def analyze(nodes: dict, edges: list):
    """Edge-primary integrals (computed on read; transient — N1/G2).

    care_priority[gene]  = Σ (variant→phenotype association load × clinsig weight), attributed
                           through the variant's :located-in gene, PLUS Σ (gene→phenotype
                           :linked-to load × clinsig weight). The care/research surface.
    locus_burden[variant]= Σ outbound :associated-with load × clinsig weight (the 取-holding locus).
    pleiotropy[node]     = Σ incident :associated-with / :linked-to / pathway loads (cascade breadth).
    pop_freq[variant]    = list of (population, AGGREGATE allele frequency) — disclosed, never used
                           in priority; population-level only (G1).
    """
    # variant → gene provenance (from :located-in)
    variant_gene = {}
    for e in edges:
        if e.get(":en/kind") in LOCATED_KINDS:
            variant_gene[e.get(":en/from")] = e.get(":en/to")

    care = defaultdict(float)
    burden = defaultdict(float)
    pleiotropy = defaultdict(float)
    pop_freq = defaultdict(list)

    for e in edges:
        kind = e.get(":en/kind")
        load_ = float(e.get(":en/grasping-load", 0.0) or 0.0)
        src, dst = e.get(":en/from"), e.get(":en/to")
        if kind in ASSOC_KINDS:
            w = CLINSIG_WEIGHT.get(e.get(":en/clinsig"), 0.3)  # missing clinsig → :uncertain weight
            burden[src] += load_ * w
            gene = variant_gene.get(src)
            if gene:
                care[gene] += load_ * w
            pleiotropy[src] += load_
            pleiotropy[dst] += load_
        elif kind in LINK_KINDS:
            w = CLINSIG_WEIGHT.get(e.get(":en/clinsig"), 0.3)
            care[src] += load_ * w  # src IS the gene for a Mendelian linkage
            pleiotropy[src] += load_
            pleiotropy[dst] += load_
        elif kind in PATHWAY_KINDS:
            pleiotropy[src] += load_
            pleiotropy[dst] += load_
        elif kind in FREQ_KINDS:
            pop_freq[dst].append((src, load_))

    return {
        "care": dict(care),
        "burden": dict(burden),
        "pleiotropy": dict(pleiotropy),
        "pop_freq": {k: sorted(v, key=lambda pf: -pf[1]) for k, v in pop_freq.items()},
    }


def _rank(d: dict, nodes: dict, limit: int = 20):
    rows = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [(nid, nodes.get(nid, {}).get(":genome/label", nid), v) for nid, v in rows]


def report_md(nodes: dict, edges: list, res: dict) -> str:
    n_gene = sum(1 for n in nodes.values() if n.get(":genome/kind") == ":gene")
    n_var = sum(1 for n in nodes.values() if n.get(":genome/kind") == ":variant")
    n_ph = sum(1 for n in nodes.values() if n.get(":genome/kind") == ":phenotype")
    n_pop = sum(1 for n in nodes.values() if n.get(":genome/kind") == ":population")
    n_pw = sum(1 for n in nodes.values() if n.get(":genome/kind") == ":pathway")
    auth = sum(1 for n in nodes.values() if n.get(":genome/sourcing") == ":authoritative")

    L = []
    L.append("# rasen 螺旋 — public-genetics care/research-priority report (aggregate-first)\n")
    L.append("> **G1 — CARE / RESEARCH map, NEVER an individual-genotype registry or "
             "discrimination tool.** No individual genotypes; population readouts are "
             "super-population AGGREGATE only; chromosomal location is coarse (cytoband). "
             "Clinical-significance categories are DISCLOSED, not rasen verdicts (N3). "
             "Evidence lives only on edges, integrated on read (N1).\n")
    L.append(f"**Graph**: {len(nodes)} nodes ({n_gene} genes · {n_var} variants · "
             f"{n_ph} phenotypes · {n_pop} populations · {n_pw} pathways) · {len(edges)} 縁 · "
             f"{auth}/{len(nodes)} :authoritative\n")

    L.append("\n## Gene care-priority — genes bearing the most disclosed clinical/functional burden\n")
    L.append("_Σ incident variant-association + gene-linkage load × disclosed clinsig weight; "
             "routed to care & research, never to ranking persons._\n")
    L.append("| rank | gene | symbol | taxon | care-priority |")
    L.append("|---:|---|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["care"], nodes), 1):
        n = nodes.get(nid, {})
        sym = n.get(":gene/symbol", "—") or "—"
        taxon = (n.get(":gene/taxon", "—") or "—")
        L.append(f"| {i} | {label} | {sym} | {str(taxon).lstrip(':')} | {v:.3f} |")

    L.append("\n## Locus burden — variants/loci carrying the most pathogenic-association weight\n")
    L.append("_Σ outbound association load × disclosed clinsig; the burden-bearing locus "
             "(the 取-holder). DISCLOSED facts only (N3)._\n")
    L.append("| rank | variant | rsID | burden |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["burden"], nodes), 1):
        rsid = nodes.get(nid, {}).get(":variant/rsid", "—") or "—"
        L.append(f"| {i} | {label} | {rsid} | {v:.3f} |")

    L.append("\n## Pleiotropy / cascade — nodes touching the most phenotypes / pathways\n")
    L.append("| rank | node | kind | pleiotropy |")
    L.append("|---:|---|---|---:|")
    for i, (nid, label, v) in enumerate(_rank(res["pleiotropy"], nodes, 12), 1):
        kind = (nodes.get(nid, {}).get(":genome/kind", "—") or "—")
        L.append(f"| {i} | {label} | {str(kind).lstrip(':')} | {v:.3f} |")

    L.append("\n## Population allele frequency — AGGREGATE disclosure (G1: never individual)\n")
    L.append("_Super-population (gnomAD-scale) frequencies only. These describe populations, "
             "never persons, and can never reconstruct an individual genotype._\n")
    L.append("| variant | population | aggregate allele freq |")
    L.append("|---|:--:|---:|")
    for vid in sorted(res["pop_freq"]):
        vlabel = nodes.get(vid, {}).get(":genome/label", vid)
        for pop, af in res["pop_freq"][vid]:
            pcode = (nodes.get(pop, {}).get(":population/code", pop) or pop)
            L.append(f"| {vlabel} | {str(pcode).lstrip(':')} | {af:.4f} |")

    L.append("\n---\n_rasen 螺旋 · ADR-2606101000 · mirror-only · non-adjudicating · "
             "edge-primary · care/research-routed. Live ingest (ClinVar/gnomAD/Ensembl/"
             "GWAS-Catalog) is G7/Council-gated._\n")
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
    res = analyze(nodes, edges)
    (outdir / "care-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"rasen: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'care-report.md'}")
    top = _rank(res["care"], nodes, 1)
    if top:
        print(f"  top care-priority gene: {top[0][1]} ({top[0][2]:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
