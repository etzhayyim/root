---
id: adr-2606101000-rasen-public-genetics-mirror
title: "ADR-2606101000: rasen 螺旋 public-genetics KG mirror (gene-scale sibling of inochi 命)"
status: accepted
doc_type: adr
topic: rasen-public-genetics-mirror
authoritative: true
last_verified: 2026-06-10
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the gene/variant-scale coverage gap below inochi's species scale, with a hard public-reference-only, no-individual-genotype inversion."
authoritative_for:
  - rasen 螺旋 actor (public-genetics / 公開遺伝 KG mirror)
  - genome-ontology
depends_on:
  - 2606073000
  - 2606073800
  - 2606011000
  - 2606011500
  - 2605312345
  - 2605215000
  - 2605181100
related:
  - 2606014500
  - 2606014600
supersedes: []
superseded_by: []
---

# ADR-2606101000: rasen 螺旋 public-genetics KG mirror

**Status**: accepted
**Date**: 2026-06-10
**Deciders**: Jun Kawasaki

# Context

inochi 命 (ADR-2606073000) closed the largest mission-integrity gap — the biosphere — but
deliberately stops at the **species / ecosystem / biome** scale. The roster carried **no
actor for the molecular scale of life**: the shared, PUBLIC reference text of genetics
(genes, variants, gene–disease linkage, pathways, population-aggregate allele frequencies)
that underlies human medicine, conservation, agriculture and antimicrobial-resistance work.

There is real public reference data here — Ensembl/HGNC gene models, dbSNP variant ids,
ClinVar/OMIM clinical significance, GO/Reactome pathways, gnomAD super-population frequencies
— and there are existing `*-compat` connectors (ncbi/ebi/ddbj, benchling/ginkgo/twist) that
can *store* such shapes, but no **native, first-party, mirror-architecture actor** that hosts
public reference genetics in the kotoba Datom log and analyses it under the charter.

The hazard is obvious and must be inverted up front: a genetics store is one decision away
from an individual-genotype registry, a discrimination/insurance/eugenic tool, or a forensic
re-identification aid. The charter's answer is the same inversion inochi applies to at-risk
taxa (a restoration map, never a target-list) and tsugite applies to displaced peoples (a
continuity map at collective scale, never a person-tracker).

# Decision

Introduce **rasen 螺旋** ("the double helix"), the **gene-scale sibling of inochi 命**, with
the same KG-mirror architecture (edge-primary, aggregate-first, non-adjudicating,
mirror-not-target, Datom-as-canonical-state, Murakumo-only narration, pywasm-runnable
pure-stdlib methods).

- **Vocabulary**: `genome-ontology` (`00-contracts/schemas/genome-ontology.kotoba.edn`) —
  nodes `:gene | :variant | :phenotype | :population | :pathway`; edges `:located-in |
  :associated-with | :linked-to | :participates-in | :allele-frequency | :interacts-with`
  carrying `:en/grasping-load` and a DISCLOSED `:en/clinsig`.
- **Lens**: edge-primary integrated clinical/functional evidence. A gene's **care-priority**
  = Σ incident variant-association (attributed through `:located-in`) + gene-linkage load ×
  disclosed clinsig weight, computed **on read** — routed to **CARE & RESEARCH**.
  Secondary readouts: **locus-burden** (the 取-holding variant) and **pleiotropy** (cascade
  breadth across phenotypes/pathways).
- **Scope spans life, not just humans**: the seed includes Homo sapiens medical genetics plus
  non-human public reference genetics (elephant TP53 expansion — cross-linking inochi; rice
  SUB1A; bacterial TEM-1 AMR).
- **Three cells**: `analyze.py` → care-report; `datom_emit.py` → EAVT Datom log;
  `coverage_report.py` → honest coverage + gap map.

## Hard gates

- **G1 — CARE/RESEARCH map, NEVER an individual-genotype registry or discrimination tool.**
  No individual genotypes / sample / family sequence. The unit is gene/variant/population-
  aggregate. Allele frequencies are super-population aggregate only; chromosomal location is
  coarse (cytoband). Routing is care, research and equity — never insurance / employment /
  eugenic / forensic targeting.
- **G2 — edge-primary (N1).** Evidence lives only on `:en/grasping-load` × disclosed
  `:en/clinsig`; care-priority is the integral computed on read; no `:genome/score-of-gene`.
- **G3 — non-adjudicating (N3).** Clinical-significance categories are DISCLOSED curated
  facts (ClinVar/OMIM/GWAS-Catalog), never rasen verdicts; rasen never diagnoses or rates a
  person.
- **G4 — public venue.** PUBLIC reference data only; open-source + on-chain + 1 SBT = 1 vote.
- **G5 — sourcing honesty.** Every record `:authoritative | :representative`; coverage of all
  genes/variants ~0 by design.
- **G6 — Murakumo-only narration.**
- **G7 — outward-gated.** Live ingest (ClinVar/gnomAD/Ensembl/GWAS-Catalog) requires Council
  + operator DID. R0 = analyzer + schema + seed only.
- **G8 — no git-lfs.** Large reference assets (FASTA/VCF) via DataLad → IPFS (`80-data/genome`).

# Consequences

- **Positive**: closes the molecular-scale coverage gap below inochi; gives a charter-clean,
  public-reference-only home for genetics; reuses the inochi method/test/wasm pattern verbatim
  (10 tests green, deterministic, pywasm-ready); cross-links the gene scale back to the
  organism/biosphere scale via `:genome/links`.
- **Negative / risks**: the individual-genotype hazard is permanent — any future move beyond
  public reference data (cohort/clinical ingest) is explicitly **out of scope for rasen** and
  would require a separate, himotoki-enveloped, consent-bound, Council-approved actor; it must
  never be bolted onto rasen.
- **Status**: 🟢 R1 — public ingest live. The WASM deploy wave remains gated (ADR-2606014500).

# Addendum (2026-06-10): public IPFS ingest implemented

The "公開遺伝子データを kotoba IPFS で取り込む" request is implemented as a fourth cell,
`cell:rasen.ingest` (`methods/ingest.py`), promoting rasen from R0 (seed-only) to R1
(public-ingest live). It deliberately stays inside G1: **no individual data, public +
aggregate only.**

- **Sources (PUBLIC, no auth)**: MyGene.info and MyVariant.info (BioThings) — aggregators of
  Ensembl/NCBI gene models, ClinVar clinical significance, and gnomAD allele frequencies.
  Declared in `data/ingest-sources.edn` with a bounded gene/rsID allowlist (G5).
- **G1 by construction**: the ingest only calls aggregate endpoints and only reads the gnomAD
  **super-population** `af_*` fields (mapped to `:global :AFR :AMR :EAS :EUR :SAS`); it stores
  a gene's **coarse cytoband** (`map_location`), never precise coordinates; sex-stratified and
  any individual/cohort fields are never read. A test (`test_g1_*`) enforces this.
- **kotoba IPFS content-address**: `methods/cid.py` computes a CIDv1 (raw codec 0x55,
  sha2-256, base32 multibase 'b') that is **byte-identical to `ipfs add --cid-version=1
  --raw-leaves`** (verified against ipfs 0.41.0), mirroring the repo's WASM-loader content
  trust anchor (`*/wasm/verify.mjs`, ADR-2605231525). The ingested EDN + its Datom projection
  are each content-addressed; `ipfs add` pins them best-effort and the pinned CID is asserted
  to match the locally-computed one. Verifiable with **no daemon**.
- **First run (2026-06-10)**: 20 genes + 12 variants fetched, 0 errors → 88 nodes / 103 縁;
  graph CID `bafkreidtkdiz5cantzxgbwalugqovpvsn6yc3rlnat2jr2uwckfm7yvdmy` (pin matched).
  Provenance (sources, licenses, counts, CID, pin result) recorded in
  `out/ingest-provenance.json`. 15 tests green (network-free).
- **Boundary unchanged**: G7 still gates *scope expansion* (more ids/sources, or anything
  beyond public reference data) behind Council + operator DID. Any individual/cohort/clinical
  ingest remains **out of scope for rasen** and would require a separate himotoki-enveloped,
  consent-bound actor — never bolted onto rasen.

# Closing (session 2026-06-10)

- **Landed**: actor `20-actors/rasen/` (manifest.jsonld · CLAUDE.md · README.md · deps.toml ·
  data/{seed,ingest-sources}.edn · methods/{analyze,datom_emit,coverage_report,ingest,cid}.py ·
  tests/{test_analyze,test_coverage,test_ingest}.py + fixture · wasm/README.md · out/*) and the
  schema `00-contracts/schemas/genome-ontology.kotoba.edn`.
- **SSoT updated**: `deps.toml` gains the `[[adrs]]` entry for 2606101000 + two `[[modules]]`
  (actor + schema); `20-actors/rasen/deps.toml` declares the per-actor manifest (pure-stdlib,
  no third-party deps). CLAUDE.md Status gains the `rasen 螺旋` Tier-B row.
- **Verified**: 15 tests green (network-free); live ingest 0 errors (88 nodes / 103 縁);
  kotoba-IPFS CID byte-identical to `ipfs add` and ipfs-pin match confirmed; offline
  re-address reproduces the same CID.
- **Open / next**: (1) public publish/pin beyond the local ipfs node (Pinata / `ipfs name
  publish` / DataLad → `80-data/genome`) — NOT done this session; (2) componentize-py WASM
  build + DID-doc CID advertisement (gated, ADR-2606014500/2606014600); (3) widen the bounded
  allowlist or add sources — G7 (Council + operator DID); (4) ~~pathway/GO ingest~~ **DONE**
  (see GO addendum below).
- **Deciders**: Jun Kawasaki. **Status**: 🟢 R1 — public ingest live.

# Addendum (2026-06-10): live GO pathway ingest

Closes next-step (4): `:participates-in` (gene→pathway) edges are now populated from **live
public data**, not just the hand seed.

- **Source**: Gene Ontology / EBI-GOA annotations via MyGene `go.BP` (already a fetched
  field — no new endpoint, same bounded gene allowlist, still PUBLIC + no individual data).
- **Normalisation** (`build_gene_pathways`): per gene, dedupe GO terms by accession, keep the
  **best evidence weight** (`GO_EVIDENCE_WEIGHT`: experimental IDA/IMP/IPI 0.9 > author-stated
  TAS/NAS 0.7 > phylogenetic IBA 0.6 > computational IEA 0.4 — the GO annotation is the
  DISCLOSED fact, rasen does not re-judge it, N3), and **cap** at `:ingest/go :max-per-gene`
  (default 6, G5 honesty). Each kept term → a `:pathway` node (`pw.go-<acc>`, `:pathway/source
  :GO`) + a `:participates-in` edge weighted by that evidence confidence.
- **Effect on analysis**: GO membership feeds the **pleiotropy / cascade** readout (the
  breadth of pathways/phenotypes a gene touches) — previously the ingested graph had zero
  pathway edges; genes now rank on real functional context.
- **Live run**: 20 genes + 12 variants → **192 nodes / 220 縁** (117 GO `:participates-in`
  edges, 104 GO pathway nodes), 0 errors; graph CID
  `bafkreicct2g36hnfoeavh3ztgplsyuq2fzlhfocv2oql2lemugmh7j27vi` (ipfs pin matched). Provenance
  gains `fetched.go_edges`. **17 tests green** (network-free; +2 GO dedup/weight/cap tests with
  a bundled `mygene_brca1_go.json` fixture).
- **Boundary unchanged**: still PUBLIC reference only; GO annotations carry no individual data.
  Adding non-GO pathway sources (Reactome/KEGG live) or widening the gene allowlist stays
  G7-gated.
