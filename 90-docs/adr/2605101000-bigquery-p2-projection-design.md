---
id: adr-2605101000-bigquery-p2-projection-design
title: BigQuery Public Data P2 Projection Design (SUPERSEDED by 2605262130)
status: superseded
doc_type: adr
topic: bigquery-public-data-p2-projection
authoritative: false
last_verified: 2026-05-10
authoritative_for:
  - bigquery-public-data-p2-projection-pattern
  - per-dataset-projection-adapter-contract
  - p2-budget-enforcement
related:
  - adr-2605092700-bigquery-public-data-ingest-cost-topology
  - adr-2605070700-rw-native-model-training-weight-lineage
  - adr-2605092345-runpod-l40s-fp8-multimodal-model-design
  - 90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md
supersedes: []
superseded_by:
  - adr-2605262130-kotoba-storage-substrate-unification
---

# Goal

Define how BigQuery public datasets that have advanced past P0 catalog and
P1 profile review (`vertex_public_dataset_catalog.review_status = 'approved'`,
`edge_dataset_produces_vertex_type` row exists, and where applicable
`edge_dataset_allowed_for_training_task` row exists) project into the canonical
Kotoba/Datomic domain `vertex_*`, `edge_*`, and training corpus surfaces — without
copying raw all-history payloads into Kotoba/Datomic or violating the cost ceilings
set in ADR 2605092700.

# Scope

P2 only runs against the approved subset. As of 2026-05-10 the catalog has 45
approved datasets (Tier 1 sample, Tier 2 large, Tier 3 curated mid-size). P2
does not enumerate, sample, or profile new datasets — those phases are owned by
P0 (`bigquery-public-dataset-catalog.mjs`) and P1
(`bigquery-public-dataset-profile.mjs`).

Out of scope for this ADR:

- automatic license inference (P0 SSoT covers this)
- training corpus build itself (downstream of `mv_training_source_eligibility`)
- live BigQuery → Kotoba/Datomic streaming (P2 is batch projection only)

# Decision

## D1. Per-dataset adapter modules

Every approved dataset has exactly one adapter under
`70-tools/scripts/projection/bigquery/<dataset_id_normalized>.mjs`. The adapter
exports a single function:

```js
export async function project({ runId, env, budget }) {
  // 1. validate edge_dataset_produces_vertex_type binding exists
  // 2. emit narrow projection query / queries
  // 3. write rows to RW vertex_*/edge_* tables and / or object storage
  // 4. record vertex_bigquery_ingest_job + vertex_ingest_artifact lineage
  // 5. return summary { rows_written, bytes_billed, cost_usd, errors }
}
```

The adapter is responsible for:

- **column projection**: never `SELECT *` from a public table; emit explicit
  column list per ADR 2605092700 §Guardrails.
- **partition filter**: time-partitioned tables MUST include a partition
  predicate or use `EXPORT DATA` with a partition WHERE clause; the
  partitioning hint comes from `vertex_public_dataset_table.partitioning_json`.
- **dedupe / canonical key**: surface a stable `vertex_id` derivation rule per
  the existing record-log convention (e.g. `at://did:web:<actor>.etzhayyim.com/<NSID>/<rkey>`).
- **license attribution**: copy `license`, `terms_url`, `provider`,
  `dataset_id` from the catalog row into every projected vertex `props.json`
  enrichment block so downstream training pipelines can filter on license at
  row level.

Adapters MUST NOT call `sdk.pds.dispatch` for domain projections; the data
plane stays Worker → Hyperdrive → Kotoba/Datomic per ADR-0036
(`Worker-direct Hyperdrive Persistence`). Domain `vertex_*` rows are not
federable AT records.

## D2. Three projection modes (mirror ingest_mode)

Every adapter is one of:

| ingest_mode | projection pattern |
|---|---|
| `self_ingest` | BQ → narrow projection rows INSERTed directly into `vertex_<domain>_*` via Kysely (`createKyselyDb(env.HYPERDRIVE).insertInto(...)`). |
| `bigquery_stage` | BQ → `EXPORT DATA OPTIONS(format='PARQUET', uri='gs://etzhayyim-bq-stage/<run_id>/<dataset>/<table>/*.parquet')` → object-store → RW `CREATE EXTERNAL SOURCE` Hummock load → narrow vertex rows. |
| `hybrid` | catalog + delta only. BQ join against an existing etzhayyim vertex (e.g. `vertex_legal_entity` for GLEIF reconciliation, `vertex_patent` for USPTO crosswalk) and write only the missing fields plus a provenance edge. |
| `reject` | adapter does not exist; no P2 projection. |
| `catalog_only` | adapter does not exist; the dataset stays metadata-only. |

The mode is read from `vertex_public_dataset_catalog.recommended_ingest_mode`
at adapter dispatch time. Operators may override via review-update by writing
a new catalog row with a different `recommended_ingest_mode` before running P2.

## D3. Decided-binding gate

P2 refuses to run unless the adapter's target binding is recorded in
`edge_dataset_produces_vertex_type`. This row carries:

- `target_vertex_label`: the canonical RW vertex table (e.g. `vertex_patent`,
  `vertex_legal_entity`, `vertex_training_document`).
- `ingest_mode`: matches D2.
- `approved_by`: the human reviewer DID who decided the binding.
- `scan_budget_tib`: per-dataset monthly cap.

The runner queries this edge before issuing any BQ query. If absent → exit
with `binding_missing` error. This is the structural enforcement of ADR
2605092700 §Implementation Plan §6 ("Stop. Do not implement P2 ...").

For training corpora, an additional row is required in
`edge_dataset_allowed_for_training_task`. Without it, the projection does not
emit `vertex_training_document`. This is the structural enforcement of ADR
2605092700 §Acceptance Criteria ("`mv_training_source_eligibility` defaults to
deny and only allows explicitly reviewed sources").

## D4. Cost guardrails (per dataset)

Every BQ query issued by an adapter MUST set:

- `maximumBytesBilled` ≤ `edge_dataset_produces_vertex_type.scan_budget_tib`
  converted to bytes.
- `dryRun: true` first; the runner refuses to execute the wet query if the
  dry-run estimated bytes exceed `maximumBytesBilled` × 0.9 (10% safety
  margin).

Default `scan_budget_tib`:

| recommended_ingest_mode | default scan_budget_tib | rationale |
|---|---:|---|
| self_ingest | 0.1 (100 GiB) | small-dataset full scan + narrow projection |
| bigquery_stage | 1 (1 TiB) | partition delta of mid-large dataset |
| hybrid | 0.05 (50 GiB) | join-heavy reconciliation only |

Operator override via the `scan_budget_tib` column. Anything > 5 TiB requires
a `vertex_bigquery_profile_run.approval_note` reference recorded in the row.

## D5. Run header + artifact ledger

Every adapter run shares the existing run / job / artifact spine from ADR
2605092700:

- `vertex_bigquery_profile_run` — header (mode='projection', dataset_filter,
  status, budget, cost).
- `vertex_bigquery_ingest_job` — per BQ query (kind='projection.<adapter>',
  query_hash, bytes_billed, etc.).
- `vertex_bigquery_export_artifact` — per Parquet shard for `bigquery_stage`
  mode.
- `vertex_ingest_run` / `vertex_ingest_artifact` — generic ingest spine
  (already populated by P0/P1).
- `vertex_ingest_cursor` — used by `hybrid` adapters to drive incremental
  re-runs without rescanning history.

## D6. Orchestration

P2 batch runs are dispatched by the existing ingest orchestrator
(`90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md`). Each
adapter is a SpiffWorkflow service-task wrapping the `.mjs` runner. Cron / on-
demand:

- daily for time-partitioned tables (delta refresh)
- weekly for static reference tables
- on-demand for one-off backfills

The orchestrator enforces a global P2 monthly cap (default: 5 TiB across all
adapters) by reading the sum of `vertex_bigquery_ingest_job.total_bytes_billed`
for the current month before dispatch.

# Adapter Catalog (initial)

The 45 approved datasets sort into adapter targets as follows. Adapter
implementations land incrementally; this list is the planning surface, not a
schedule.

## Tier 1 — small / mid-size (11)

| dataset | target_vertex_label | mode | adapter file |
|---|---|---|---|
| epa_historical_air_quality | `vertex_air_quality_observation` (new) | self_ingest | `epa-historical-air-quality.mjs` |
| new_york_taxi_trips | `vertex_taxi_trip` (new) | self_ingest | `new-york-taxi-trips.mjs` |
| stackoverflow | `vertex_qa_post` (new) | self_ingest | `stackoverflow.mjs` |
| noaa_icoads | `vertex_marine_observation` (new) | self_ingest | `noaa-icoads.mjs` |
| cms_synthetic_patient_data_omop | `vertex_synthetic_patient` (new) | self_ingest | `cms-synthetic-omop.mjs` |
| usfs_fia | `vertex_forest_inventory` (new) | self_ingest | `usfs-fia.mjs` |
| open_targets_platform | `vertex_target_evidence` (new) | self_ingest | `open-targets-platform.mjs` |
| chicago_taxi_trips | `vertex_taxi_trip` | self_ingest | `chicago-taxi-trips.mjs` |
| ebi_surechembl | `vertex_chemistry_patent` (new) | self_ingest | `ebi-surechembl.mjs` |
| crypto_litecoin | `vertex_blockchain_block` + `vertex_blockchain_tx` | self_ingest | `crypto-litecoin.mjs` |
| crypto_dogecoin | `vertex_blockchain_block` + `vertex_blockchain_tx` | self_ingest | `crypto-dogecoin.mjs` |

## Tier 2 — large + license-clean (11 approved, 3 rejected, 1 deferred)

| dataset | target_vertex_label | mode |
|---|---|---|
| wikipedia | `vertex_encyclopedia_article` (new) per language | bigquery_stage |
| deps_dev_v1 | `vertex_package_metadata` + `edge_package_depends_on` | bigquery_stage |
| google_books_ngrams_2020 | `vertex_ngram_count` (new) per language | bigquery_stage |
| noaa_global_forecast_system | partition delta to `vertex_weather_forecast` (new) | bigquery_stage |
| crypto_solana_mainnet_us | `vertex_blockchain_block` + `vertex_blockchain_tx` (slot partition) | bigquery_stage |
| goog_blockchain_ethereum_mainnet_us | same shape, ethereum chain_id | bigquery_stage |
| crypto_ethereum | overlap-allowed compat ingest source | bigquery_stage |
| crypto_sui_mainnet_us / near / aptos / polygon | shared blockchain shape | bigquery_stage |

Rejected: `blockchain_analytics_ethereum_mainnet_us` (dup), `crypto_aptos_testnet_us`
(testnet), `crypto_polygon` (dup of `goog_blockchain_polygon_mainnet_us`).
Deferred: `pypi` (per-package license filter required first).

## Tier 3 — curated mid-size (34)

Drives the allowlist for first multilingual / public-domain corpus build:

- text + reference: `the_general_index`, `nih_sequence_read`, `noaa_goes16`,
  `noaa_goes17`, `usda_nass_agriculture`, `listenbrainz`, `nlm_rxnorm`,
  `geo_us_roads`, `nih_gudid`, `irs_990`, `uspto_oce_*`, `census_bureau_acs`,
  `bls`, `worldbank_wdi`, `cfpb_complaints`, `geo_us_boundaries`,
  `census_opportunity_atlas`, `noaa_gsod`, `moon_phases`
- bio: `deepmind_alphafold`, `gnomAD`, `nih_sequence_read`
- vision / map: `open_buildings`, `open_images`, `overture_maps`,
  `geo_whos_on_first`
- healthcare: `nppes`, `cms_medicare`, `medicare`, `fda_drug`,
  `covid19_open_data`, `covid19_open_data_eu`

Most map to `self_ingest` mode (sub-100 GiB). High-priority adapters:
`deepmind_alphafold`, `gnomAD`, `the_general_index`, `census_bureau_acs`,
`nppes`, `usda_nass_agriculture`.

# Acceptance Criteria

P2 is complete for a given dataset when:

- adapter exists at `70-tools/scripts/projection/bigquery/<dataset>.mjs`
- `edge_dataset_produces_vertex_type` row exists and references the adapter's
  target vertex label.
- adapter dry-run validator passes (no `SELECT *`, has partition filter where
  applicable, sets `maximumBytesBilled`).
- a successful run wrote rows to the target vertex table and a row to
  `vertex_bigquery_profile_run` with `mode='projection'`.
- (training corpus only) `edge_dataset_allowed_for_training_task` row exists,
  and `vertex_training_document` rows reference the dataset via
  `edge_training_document_source`.
- `mv_world_coverage_live` shows a non-zero record count for the new app_host
  if a new domain was added.

P2 is complete in aggregate when ≥ 30 of the 45 approved datasets have
landed adapter rows (the remainder may stay catalog-only or hybrid by
design).

# Cost Estimate

Initial P2 build for the 45 approved datasets, assuming the default budgets
in §D4 and one-time delta backfill:

| tier | datasets | mode | per-dataset cap | aggregate scan |
|---|---:|---|---|---:|
| Tier 1 | 11 | self_ingest | 100 GiB | ~1.1 TiB |
| Tier 2 | 11 | bigquery_stage | 1 TiB | ~11 TiB |
| Tier 3 | 34 | self_ingest | 100 GiB | ~3.4 TiB |
| **total** | **56** | mixed | — | **~15.5 TiB → ~$97** |

Within the ADR 2605092700 §"Cost Estimate" P2 row tolerance ($6.4k for 1 PiB
broad projection). Subsequent monthly delta refreshes for time-partitioned
sources (NOAA / blockchain / Stack Overflow / open_targets) project to ~5
TiB/month → ~$31/month.

Excluded: B2 / GCS storage for staged Parquet, Kotoba/Datomic compute scaling,
LLM training compute, OCR / labeling. Tracked separately in infra docs.

# Production Hardening (2026-05-11)

Lessons from the first end-to-end pilot runs that are now folded into
`70-tools/scripts/projection/bigquery/_lib.mjs`:

## Resumable cursors via `vertex_ingest_cursor`

Every adapter persists `(ingest_family, source_id, shard_key) →
(cursor_value, high_watermark, status, props)` so a 2nd run picks up
exactly where the 1st stopped, and a crash mid-INSERT does not force a
full-window rescan. Key states:

- `in_flight` — written before any INSERT; signals "do not trust
  durable state below high_watermark"
- `partial` — written by `onChunkFlush` after each successful periodic
  FLUSH; cursor_value is the max committed key (e.g. block_height,
  date_local, person_id)
- `complete` — written at shard end after `rwFlush()` succeeds

Two helpers expose the contract: `loadCursor({ ingestFamily, sourceId,
shardKey })` and `saveCursor({...})`. Adapters read at start, save
`in_flight` immediately, then `partial` per chunk via the hook, then
`complete` (or `partial` on error) at end.

## Periodic FLUSH inside `rwBatchInsert`

Kotoba/Datomic buffers DML until checkpoint. A single large INSERT loop
(observed 150k rows / Litecoin transactions) lost all uncommitted rows
when the cluster entered recovery mid-run. Fix: `rwBatchInsert` issues
`FLUSH` every `flushEveryNChunks` chunks (default 20 × chunkSize 100 =
2000 rows / flush). A failed FLUSH is best-effort — it reconnects the
client and continues; durability is guaranteed by the next successful
FLUSH or the final `rwFlush()`.

## `onChunkFlush` cursor advance hook

`rwBatchInsert` takes an optional `onChunkFlush({ slice, totalWritten })`
callback that fires only after a periodic FLUSH succeeds. The adapter
inspects `slice` (the rows that just became durable) to compute the
shard's max key and writes that to `vertex_ingest_cursor` with
`status="partial"`. Crash recovery is therefore bounded to at most one
flush window worth of rows. Combined with record-log upsert this gives
"at-least-once with O(2000-row) redo".

## Connection durability — fresh client per record + maintained client per INSERT loop

The pg-pool default `idleTimeoutMillis: 10000` race-conditions against
Kotoba/Datomic's silent connection drop during BigQuery polling (queries
take 10–60s with no pg activity). Adapters now:

- use **fresh `pg.Client` per record (ledger / cursor) call** — `rwQuery`
  helper creates + connects + queries + ends on every invocation
- use **a single maintained client per INSERT loop** — `rwBatchInsert`
  keeps one connection across all chunks, recreates on transient error,
  and force-closes on completion
- attach a `keepAlive: true` TCP option + `idleTimeoutMillis: 0` on any
  pool that does exist

## RW health gate between adapter runs

A worker-node loss observed mid-Litecoin run produced "No worker node
found for worker slot id: [...]" errors and required a multi-minute
recovery. The smoke runner inserts a small DDL-queue drain wait
between adapters (`SELECT count(*) FROM rw_catalog.rw_ddl_progress`
polled until 0). Long-running production adapters should call
`rw-health-gate.sh` (per `30-graph/graph-schema/CLAUDE.md`) before
starting; the in-tree helper has not yet been added but is tracked.

# etzhayyim Coverage Impact

The 45 approved datasets feed ~17 `dim_world_domain` app_hosts (per ADR
2605092700 §"etzhayyim World-Coverage Mapping"). Realistic coverage delta when all
P2 adapters land:

| etzhayyim app_host | current % | post-P2 estimate | dominant feeder |
|---|---:|---:|---|
| `patent` | 0.002 | ~100 | `patents`, `uspto_oce_*` (14 ds) |
| `blockchain` | 0.001 | overflow | 32 `crypto_*` / `goog_blockchain_*` |
| `weather` | sub-1 | ~95 | NOAA family (5+ ds) |
| `gov` (US fed) | 77 | ~98 | `census_bureau_*`, `sdoh_*`, `nppes`, `irs_990` |
| `talent` (US) | 0.025 | ~70 | `bls`, `bls_qcew` |
| `iryo` | 0.03 | 5–15 | `cms_*`, `nlm_rxnorm`, `fda_drug`, `nih_*` |
| `iryo-genomics` | n/a | ~80 | `gnomAD`, `deepmind_alphafold`, `ebi_*` |
| `maps` | 0.78 | 50–80 | `open_buildings`, `overture_maps`, `geo_us_roads` |
| `tentai` | 0.57 | ~60 | `wise_all_sky_data_release` |
| `shizen` | overflow | overflow | `epa_*`, `usfs_fia`, `usda_nass` |
| `text-corpus` | n/a | corpus-bound | `wikipedia`, `stackoverflow`, `google_books_ngrams`, `the_general_index` |
| `code`/`package-metadata` | n/a | ~40 | `deps_dev_v1`, `pypi`, `libraries_io` |
| `civic` (US cities) | bounded | bounded | 9 city open-data datasets |

Aggregate: P2 lifts overall `mv_world_coverage_live` from `0.0087%` to an
estimated `~0.05–0.10%` — a 5–10× jump driven mainly by the patent /
blockchain / weather / bio / US-gov / maps domains saturating their world
totals. The remaining 99.9% of world coverage stays in the JP-vertical /
industrial / private-data corner that BigQuery cannot reach (per ADR
2605092700 §"BQ-uncoverable domains"). P2 must therefore not block, gate, or
displace the existing collector pipelines.

## Pilot state as of 2026-05-11

Three target tables have landed pilot rows; the remaining seven have
adapters but await first run after RW-cluster stabilization. Cumulative
BigQuery scan across P0+P1+P2 = **7.9 TiB ≈ $48.27** (well under the ADR
2605092700 §"Cost Estimate" P1 default 20 TiB / $119 cap).

| target | rows | source | run-id |
|---|---:|---|---|
| `vertex_air_quality_observation` | 110,421 | epa_historical_air_quality (O3 daily, 2025) | p2-epa-pilot-20260511 |
| `vertex_blockchain_block` (ltc) | 612 | crypto_litecoin (last 2 days) | p2-ltc-onflush-20260511 |
| `vertex_blockchain_tx` (ltc) | 149,543 | crypto_litecoin (last 2 days, recovery via onChunkFlush) | p2-ltc-onflush-20260511 |
| `vertex_qa_post` | 0 | stackoverflow (adapter ready) | — |
| `vertex_marine_observation` | 0 | noaa_icoads (adapter ready) | — |
| `vertex_synthetic_patient` | 0 | cms_synthetic_patient_data_omop (adapter ready) | — |
| `vertex_forest_inventory` | 0 | usfs_fia (adapter ready) | — |
| `vertex_target_evidence` | 0 | open_targets_platform (adapter ready) | — |
| `vertex_chemistry_patent` | 0 | ebi_surechembl (adapter ready) | — |
| `vertex_taxi_trip` (nyc, chicago) | 0 | new_york_taxi_trips + chicago_taxi_trips (adapters ready) | — |
| `vertex_blockchain_block`/`_tx` (doge) | 0 | crypto_dogecoin (adapter ready) | — |

Cursors: 2 rows in `vertex_ingest_cursor` (litecoin blocks + transactions,
both `complete`).

# Rejected Approaches

- **Single mega-adapter that ingests every dataset**: brittle, untestable,
  breaks the per-license attribution requirement.
- **Direct `EXPORT DATA OPTIONS(uri='hummock://...')`**: BQ has no Hummock
  driver; staging through GCS / B2 is mandatory.
- **Letting P1 profile rows imply approval**: rejected by ADR 2605092700.
  Approval is an explicit edge insertion, not a profile-row presence check.
- **Auto-promoting `recommended_ingest_mode` to `edge_dataset_produces_vertex_type`**:
  rejected. Recommended mode is a heuristic; the binding is a human decision.

# References

- ADR 2605092700 — BigQuery public data ingest cost topology (P0/P1 gate).
- ADR 0036 — Worker-direct Hyperdrive Persistence (data plane choice).
- ADR 0044 — Kotoba/Datomic UDF language strategy (selecting where projection
  logic lives).
- `90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md` —
  orchestration runtime.
- `30-graph/graph-schema/sql_migrations/20260509600000_vertex_public_dataset_catalog.up.sql`
  / `20260509610000_vertex_public_dataset_profile.up.sql` — schema this ADR
  consumes.
- `00-contracts/catalogs/bigquery/public-dataset-licenses.json` — license SSoT
  read by every adapter.
