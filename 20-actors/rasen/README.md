# rasen 螺旋

Public-genetics (公開遺伝) Knowledge Graph mirror — the **gene-scale sibling of inochi 命**.

rasen hosts and analyses **PUBLIC reference genetics only** — genes, sequence variants, the
conditions they associate with, the pathways they sit in, and **population-aggregate** allele
frequencies — across humans, animals, plants and microbes, woven into the kotoba Datom log.

It is a **CARE / RESEARCH map, never an individual-genotype registry or discrimination tool**
(G1). No individual genotypes, no personal sequence, no precise coordinates: the unit is
always a gene / variant / population aggregate, and clinical-significance is a *disclosed*
fact (ClinVar/OMIM style), never a rasen verdict (N3).

```bash
cd 20-actors/rasen
python3 methods/analyze.py          # → out/care-report.md          (gene care-priority)
python3 methods/datom_emit.py       # → out/genome-datoms.kotoba.edn (EAVT canonical state)
python3 methods/coverage_report.py  # → out/coverage-report.md       (honest coverage + gaps)
python3 methods/ingest.py           # OUTWARD (G7): public APIs → kotoba EDN/Datom → IPFS CID (+pin)
python3 methods/publish.py          # OUTWARD (G7): pin + IPNS-publish + snapshot to 80-data/genome
python3 wasm/app.py analyze         # the WASM component's export body, dev mode
python3 tests/test_analyze.py && python3 tests/test_coverage.py && python3 tests/test_ingest.py && python3 tests/test_wasm.py  # 23 green
```

`ingest.py` pulls a bounded, **public + aggregate-only** slice (MyGene.info + MyVariant.info +
Reactome → Ensembl/NCBI + ClinVar + gnomAD super-population frequencies + GO & Reactome
pathways), normalises it into the genome-ontology kotoba graph, and content-addresses it to a
kotoba IPFS CIDv1 that matches `ipfs add --cid-version=1 --raw-leaves` (verifiable without a
daemon). `publish.py` pins + IPNS-publishes it and snapshots the durable record into
`80-data/genome/`. `wasm/` is the build-ready componentize-py component. No individual data, ever.

See `CLAUDE.md` for the constitutional gates and ontology, and
`00-contracts/schemas/genome-ontology.kotoba.edn` for the vocabulary. Status: 🟢 R1+ — public
ingest (3 sources) + publish + WASM-ready; scope expansion is operator/Council-gated (G7).
