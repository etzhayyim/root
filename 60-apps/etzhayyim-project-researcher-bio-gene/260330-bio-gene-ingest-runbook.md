# Bio Gene Ingest Runbook

## Scope
- literature feeds: PubMed, bioRxiv, medRxiv
- curated variant/db sources: ClinVar, dbSNP, gnomAD, OMIM
- pathway/protein sources: UniProt, KEGG, Reactome
- omics repositories: GEO, ENA, ArrayExpress, Single Cell Portal

## Pipeline
1. Source scheduler emits `source-delta` job with `source_id`, `watermark`, `priority`.
2. `bio-gene-literature-worker` fetches metadata and raw payload.
3. Normalizer resolves gene, variant, disease, pathway aliases into canonical IDs.
4. Claim extractor emits evidence rows with provenance pointers.
5. Evidence rows are routed:
   - variant-heavy rows -> `bio-gene-variant-worker`
   - omics/cohort rows -> `bio-gene-omics-worker`
   - assay/protocol rows -> `bio-gene-assay-planner`
6. `bio-gene-governance-policy` stamps release eligibility.
7. `bio-gene-evidence-store` persists snapshots and index entries.

## Output Shapes
- `source_snapshot`
- `normalized_entity`
- `evidence_row`
- `claim_table`
- `research_packet`

## Guardrails
- never drop source-native IDs
- keep raw payload checksum for replay
- distinguish peer-reviewed vs preprint evidence
- separate population frequency from pathogenicity claim
- block public packet release when provenance or governance checks are incomplete
