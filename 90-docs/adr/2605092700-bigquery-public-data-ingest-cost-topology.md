---
id: adr-2605092700-bigquery-public-data-ingest-cost-topology
title: BigQuery Public Data Ingest Cost + RisingWave Graph Topology
status: proposed
doc_type: adr
topic: bigquery-public-data-risingwave-ingest
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - bigquery-public-data-ingest-cost-model
  - public-dataset-risingwave-vertex-edge-mv-topology
  - llm-training-public-data-source-policy
related:
  - adr-2605070700-rw-native-model-training-weight-lineage
  - adr-2605092345-runpod-l40s-fp8-multimodal-model-design
  - adr-2605081430-osm-ingest-rw-tuning-and-k8s-utilization
  - adr-2604251024-patent-bulk-ingest-and-blob-cid
  - adr-0057-common-crawl-domain-ingest-coverage-topology
  - 90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md
---

# Goal

BigQuery で公開されている大規模データセット、公式 API/file ingest、
Common Crawl、自前 domain collectors を、RisingWave の `vertex_*`,
`edge_*`, `mv_*`, index、training dataset snapshot に接続する。

同時に、BigQuery の on-demand scan cost が PB 級で破綻しないように、
どこを BigQuery に任せ、どこを自前 ingest に残すかを固定する。

# Decision

BigQuery は canonical graph store ではない。BigQuery は以下に限定する。

- public dataset の発見、schema sampling、source catalog 作成
- 巨大表の column projection、dedupe、entity matching、window aggregation
- RisingWave に入れる delta / narrow projection の生成
- LLM training 用 corpus の sampling、license / language / quality filter

RisingWave は以下の source of truth とする。

- `vertex_*`: canonical facts
- `edge_*`: graph relation / provenance / training lineage
- `mv_*`: intel, coverage, training manifest, operator status
- `vertex_ingest_run`, `vertex_ingest_cursor`, `vertex_ingest_artifact`: run,
  cursor, raw/export artifact lineage

巨大 raw payload は RisingWave に入れない。BigQuery export, Common Crawl
WARC/WET, OSM PBF, training JSONL shard, model weights は B2/GCS/IPFS 等の
object storage に置き、RisingWave には URI, hash, byte size, row count,
license, source dataset id を持たせる。

Initial scope is **P0 + P1 only**:

- **P0 catalog/sample**: discover every candidate public dataset broadly and
  record metadata, schema, size, license/terms pointers, cost estimates, and
  bounded samples.
- **P1 profiling**: for selected candidate datasets, compute null rates, key
  candidates, language/text statistics, top values, PII/training risk samples,
  and recommended RisingWave vertex/edge targets.

P2+ graph projection and production ingest are explicitly out of scope for this
ADR until P0/P1 outputs have been reviewed.

# P0/P1 Scope

P0/P1 answers "what exists, what does it cost to touch, and is it safe enough to
design an ingest adapter?" It does not move raw all-history data into
RisingWave.

## P0 Catalog/Sample

Required output:

```text
vertex_public_dataset_catalog
vertex_public_dataset_table
vertex_public_dataset_sample
vertex_bigquery_profile_run
vertex_ingest_artifact(kind='bigquery.catalog_sample')
mv_public_dataset_catalog_coverage
```

Required fields:

```text
dataset_id
provider
bq_project
bq_dataset
bq_table
description
homepage_url
marketplace_url
license
terms_url
last_modified_at
row_count_estimate
size_bytes_estimate
partitioning_json
clustering_json
schema_json
sample_rows_uri
sample_row_count
sample_hash
estimated_full_scan_cost_usd
estimated_delta_scan_cost_usd
pii_tier_guess
allowed_for_train_guess
allowed_for_embedding_guess
recommended_ingest_mode
candidate_vertex_targets_json
candidate_edge_targets_json
review_status
```

P0 query rules:

- query metadata first (`INFORMATION_SCHEMA`, table metadata, Marketplace/API
  metadata where available)
- sample only bounded rows per table
- never full scan a table in P0
- cap each sampling query with `maximum_bytes_billed <= 100 GiB`
- write all samples to object storage, not Hummock

P0 is sufficient for catalog/search and for deciding which datasets advance to
P1.

## P1 Profiling

Required output:

```text
vertex_public_dataset_profile
edge_public_dataset_profiles_table
edge_public_dataset_candidate_for_vertex_type
edge_public_dataset_candidate_for_training_task
mv_public_dataset_profile_rank
mv_training_source_eligibility
```

Required profile metrics:

```text
profile_run_id
table_vertex_id
columns_profiled_json
key_candidate_json
null_rate_json
distinct_estimate_json
top_values_json
text_columns_json
language_distribution_json
text_length_stats_json
timestamp_range_json
geo_coverage_json
pii_signal_json
license_decision
allowed_for_train
allowed_for_embedding
dedupe_strategy
delta_strategy
recommended_risingwave_tables_json
recommended_edges_json
estimated_monthly_refresh_scan_tib
estimated_monthly_refresh_cost_usd
profile_artifact_uri
profile_hash
review_status
```

P1 query rules:

- only run on datasets selected from P0
- cap each profiling query with `maximum_bytes_billed <= 2 TiB`
- cap monthly P1 scan to 20 TiB unless explicitly approved
- compute approximate metrics where exact scan would exceed cap
- `allowed_for_train=false` unless license and PII checks pass

P1 is sufficient to create a concrete P2 projection design, but P1 itself does
not create production domain `vertex_*` / `edge_*` rows beyond catalog/profile
state.

# Source Split

| source family | BigQuery role | self-ingest role | RisingWave destination |
|---|---|---|---|
| BigQuery public datasets / Marketplace | primary staging, projection, delta, dedupe | export/import runner | `vertex_public_dataset_*`, domain `vertex_*`, `edge_*` |
| GitHub / StackOverflow / Wikipedia / Google Trends | history scan, language/topic sampling, repo/page/user aggregate | graph write + training filter | code/text vertices, `v_training_text`, repo/topic edges |
| GDELT / news / trend data | event dedupe, entity co-occurrence, time windows | intel normalization and source policy | event/news/intel vertices, mention edges |
| Google Patents / public patent data | batch scan, assignee/inventor/citation projection | official-source reconciliation | patent vertices, citation/assignee edges |
| Overture Maps / geospatial public tables | coarse global extracts, join-heavy matching | OSM PBF / Overpass / region diff ingest | map vertices, location edges, chunk MVs |
| NOAA / weather / climate | partitioned time/geography projection | domain importer and cache | weather/time-series vertices, location edges |
| blockchain public datasets | chain aggregate, address clustering candidates | live chain watcher / private chain ingest | transaction/address/risk vertices, clustering edges |
| Recruit ATS | employer fuzzy matching and anchoring | direct Greenhouse/Lever/Ashby fetch remains canonical | `vertex_job_posting`, employer edges |
| GLEIF / BLS / sanctions / public registries | join-heavy reconciliation only | official API/file is source-of-truth | legal entity, cohort, sanctions vertices |
| Crossref / DataCite / NDL / ISBN | DOI/ISBN bulk dedupe and sampling | official API/OAI-PMH/image OCR/blob path | work/book/blob/training vertices |
| Common Crawl | URL frontier and host/domain statistics | WARC/WET fetch, extraction, OCR, policy gate | page/text/entity vertices and edges |

# Standard Graph Shape

Every public dataset family must resolve to this minimum graph contract:

```text
vertex_public_dataset_catalog
vertex_bigquery_ingest_job
vertex_ingest_run
vertex_ingest_cursor
vertex_ingest_artifact
domain vertex_*
domain edge_*
mv_*_ingest_status
mv_*_coverage
mv_training_source_eligibility
```

For training:

```text
vertex_training_document
edge_training_document_source
edge_training_document_mentions_entity
mv_training_corpus_manifest
mv_training_corpus_stats_by_license
```

`v_training_text` remains the common read surface, but each row must be traceable
to source dataset, source license, language, quality score, PII decision, and
`allowed_for_train`.

# BigQuery Cost Model

Pricing checked against Google Cloud BigQuery pricing on 2026-05-09:

- on-demand query pricing: first 1 TiB/month free, then USD 6.25/TiB scanned.
- active logical BigQuery storage: about USD 23.552/TiB-month, first 10 GiB free.
- long-term storage starts after 90 unmodified days and is about 50% lower.
- Standard edition slots are USD 0.04/slot-hour pay-as-you-go; a 50-slot always
  on reservation is about USD 1,460/month before discounts.

References:

- https://cloud.google.com/bigquery/pricing
- https://docs.cloud.google.com/bigquery/docs/best-practices-costs

Formula:

```text
on_demand_query_cost_usd =
  max(0, scanned_tib - 1) * 6.25

active_logical_storage_usd_per_month =
  stored_tib * 23.552

standard_slot_month_usd =
  slots * 0.04 * 730
```

Important: querying public datasets charges this project for bytes processed,
not for storing the public dataset. Storage cost appears only for tables we
create or copy into our project. Therefore the expensive mistakes are:

- scanning all columns when only stable ids / timestamps / text snippets are
  needed
- repeatedly re-scanning raw public tables instead of materializing smaller
  staging tables
- copying entire public datasets into our project
- exporting raw all-history data into RisingWave / Hummock

# Cost Estimate

There is no stable price for "all BigQuery public data" because public datasets
and table sizes change. The table below is the operational estimate for our
planned categories, using scanned TiB as the controlling variable.

| tier | intent | one-pass BigQuery scan | BQ query cost | staging storage | BQ storage/month | decision |
|---|---:|---:|---:|---:|---:|---|
| P0 catalog/sample | schema, row counts, bounded samples | 10 TiB | ~$56 | 0.1 TiB | ~$2 | accepted scope |
| P1 profiling | selected datasets: keys, null rates, text/license/PII, ingest target design | 20 TiB/month default, 100 TiB hard cap | ~$119/month default, ~$619 hard cap | 1 TiB | ~$24 | accepted scope |
| P2 broad graph projection | major public datasets, selected columns, delta outputs only | 1 PiB | ~$6,394 | 10 TiB | ~$236 | approval required |
| P3 raw all-history projection | broad "scan everything useful once" pass | 10 PiB | ~$63,994 | 100 TiB | ~$2,355 | not default |
| P4 unbounded "all public data, all columns" | literal full-copy posture | 100 PiB+ | ~$639k+ | 1 PiB+ | ~$24k+/month | rejected |

These costs exclude:

- object storage for exported JSONL/Parquet/WARC/PBF artifacts
- network egress if data leaves Google Cloud or crosses billable boundaries
- RisingWave compute scale-up and B2/Hummock growth
- LLM embedding / OCR / labeling / training GPU costs

Current RisingWave monthly baseline is already tracked separately in infra docs.
This ADR treats BigQuery as incremental preprocessing cost, not as a replacement
for RisingWave.

# Guardrails

Every BigQuery-backed ingest must enforce:

- dry-run or query validator before production execution
- `maximum_bytes_billed`
- explicit column lists; never `SELECT *` from public raw tables
- partition/time filters where available
- materialized stage tables with TTL for large intermediate results
- export only narrow canonical deltas to object storage
- write one `vertex_bigquery_ingest_job` or `vertex_ingest_artifact` row with
  job id, query hash, scanned bytes, row count, export URI, and source license
- `allowed_for_train=false` by default until source license and PII checks pass

Default budget caps:

| environment | max bytes billed per query | max monthly scan | expected monthly BQ cost |
|---|---:|---:|---:|
| dev | 100 GiB | 1 TiB | free tier / near zero |
| P0 catalog/sample | 100 GiB | 10 TiB | <= ~$56 |
| P1 profiling default | 2 TiB | 20 TiB | <= ~$119 |
| P1 profiling hard cap | 2 TiB | 100 TiB | <= ~$619 |
| production P2 | 100 TiB | 1 PiB | <= ~$6,394 |

# Implementation Plan

1. Add P0/P1 catalog/profile schema:
   - `vertex_public_dataset_catalog`
   - `vertex_public_dataset_table`
   - `vertex_public_dataset_sample`
   - `vertex_public_dataset_profile`
   - `vertex_bigquery_ingest_job`
   - `vertex_bigquery_export_artifact`
   - `vertex_bigquery_profile_run`
   - `edge_dataset_produces_vertex_type`
   - `edge_dataset_allowed_for_training_task`
   - `mv_public_dataset_ingest_status`
   - `mv_public_dataset_catalog_coverage`
   - `mv_public_dataset_profile_rank`
   - `mv_training_source_eligibility`
2. Add `70-tools/scripts/bigquery-public-dataset-catalog.mjs` for P0.
3. Add `70-tools/scripts/bigquery-public-dataset-profile.mjs` for P1.
4. Generate catalog samples into object storage and record
   `vertex_ingest_artifact(kind='bigquery.catalog_sample')`.
5. Generate P1 profiles only for reviewed P0 candidates.
6. Stop. Do not implement P2 projection until the P0/P1 review produces an
   explicit dataset allowlist, expected scan budget, and RisingWave schema plan.

# Acceptance Criteria

P0 is complete when:

- all configured public dataset sources have catalog rows
- every table row has schema, size estimate, row estimate where available, and
  source/license/terms pointers
- every sample has an artifact URI and hash
- `mv_public_dataset_catalog_coverage` shows missing metadata counts by provider

P1 is complete when:

- every selected P0 candidate has a profile row
- profile artifacts include key/null/text/language/PII/license/training metrics
- each candidate has a recommended ingest mode:
  `reject`, `catalog_only`, `bigquery_stage`, `self_ingest`, or `hybrid`
- `mv_training_source_eligibility` defaults to deny and only allows explicitly
  reviewed sources
- monthly P1 scan remains under 20 TiB by default or has an explicit approval
  note in `vertex_bigquery_profile_run`

# etzhayyim World-Coverage Mapping

The 352-dataset `bigquery-public-data` catalog crosswalks onto a defined subset
of `dim_world_domain` app_hosts in `mv_world_coverage_live`. As of 2026-05-10
the live cluster reports overall coverage `1.077B / 12.43T = 0.0087%` across
493 domains (230 below 0.01%, 120 already at or above 100%). This section
records what BigQuery can and cannot do against that frontier so future
adapters do not over-promise.

## BQ-coverable domains (≈17)

Each row is the etzhayyim `app_host` plus the BigQuery dataset family that can feed
it. "Estimated post-BQ coverage" assumes the relevant adapters are written and
the projection budget in §"Cost Estimate" is honored.

| etzhayyim app_host | feeding BQ dataset family | post-BQ coverage estimate |
|---|---|---:|
| `patent` | `patents`, `patents_cpc`, `patents_dsep`, `uspto_oce_*`, `usitc_investigations` | ~100% of US patent universe |
| `blockchain` | 32 `crypto_*` / `goog_blockchain_*` / `blockchain_*` mainnets | >>100% (transaction-level overflow) |
| `weather` | `noaa_*`, `ghcn_*`, `national_water_model` | ~95% of public weather record stream |
| `iryo` | `cms_*`, `medicare`, `fda_drug`, `nlm_rxnorm`, `nih_*`, `clinvar`, `open_targets_platform` | ~5–15% of medical record universe |
| `iryo-genomics` | `gnomAD`, `deepmind_alphafold`, `ebi_mgnify`, `ebi_chembl` | ~80% of public genomics references |
| `maps` | `open_buildings`, `overture_maps`, `geo_us_roads`, `geo_us_boundaries` | ~50–80% (heavy in US/global building, road) |
| `gov` (US federal) | `census_bureau_*`, `sdoh_*`, `hud_*`, `irs_990`, `fec`, `nppes` | ~98% of US federal record set |
| `talent` (US) | `bls`, `bls_qcew` | ~70% of US occupation/wage stats |
| `bank` (US) | `fdic_banks` | small but specific to FDIC scope |
| `finance` (US) | `cfpb_complaints`, `sec_quarterly_financials` | <5% of global financial universe |
| `shizen` | `epa_*`, `usfs_fia`, `usda_nass_agriculture`, `nrel_nsrdb`, `openaq` | overflow (>100% of US scope) |
| `tentai` | `wise_all_sky_data_release` | ~60% of NASA WISE survey scope |
| `text-corpus` | `wikipedia`, `stackoverflow`, `google_books_ngrams_2020`, `the_general_index`, `hacker_news` | corpus-size dependent |
| `code` / `package-metadata` | `deps_dev_v1`, `pypi`, `libraries_io`, `github_archive` | ~40% of public package graph |
| `kuruma-transport` (US) | `nhtsa_*`, `faa`, `new_york_taxi_trips`, `chicago_taxi_trips`, `dot_*` | ~30% (US scope only) |
| `civic` (US cities) | 9 `austin_*`, `chicago_*`, `new_york_*`, `san_francisco_*`, `baltimore_*`, `seattle_*`, `london_*` | bounded by city scope |
| `vision` | `open_images`, `idc_v23_*` (medical imaging) | sample-size dependent |

These ~17 domains plus their `dim_world_domain` siblings are the realistic
target set for P2 projection. Everything else stays catalog-only.

## BQ-uncoverable domains

Domains that BigQuery public data cannot meaningfully fill. Each requires a
non-BigQuery ingest path:

| etzhayyim app_host | world_total | reason BQ does not have it | required alternate path |
|---|---:|---|---|
| `photos` | ~5T | no general image corpus in BQ public | Common Crawl image extraction, IPFS scrape |
| `kessai` (決済) | ~1T | JP payment infrastructure private | Stripe / Square API + JP 決済代行 partnerships |
| `serial`, `seizo`, `nimotsu`, `bim`, `mac`, `iot` | each 100B–1T | industrial telemetry / IoT / CAD; not public | per-device-class collectors, OPC-UA / MQTT bridges |
| `invoice`, `receipt` | each 500B | private commercial documents | OCR pipeline + B2B XML feed (Peppol/EDI) |
| `natural-person` | 108B | only fragments via `wikipedia` / patents inventors / SEC officers | LinkedIn / CV crawl (legal review), Mastodon/Bluesky social ingest |
| `shisan` (資産) | 50B | personal/legal portfolio holdings private | broker API (rakuten-shoken / SBI / Schwab), self-report |
| `haikibutsu` (廃棄物) | 50B | per-municipality administered | 環境省 + 自治体 OPEN data + RDF crawl |
| `kachiku` (家畜) | 30B | private agribusiness | 農協 / 農林水産省 / FAOSTAT |
| `phonenumber` | 15B | not in BQ public | telco partnership, SMS-spam DB |
| `malak` (threat intel) | 15B | partial via `rekor` only | VirusTotal / MISP / HUMAN, OTX feeds |
| `keiyaku` (契約) | 10B | private legal documents | M&A SaaS API, internal vault only |
| `software` (JP inventory) | 10B | not catalogued in BQ | Vector / Kakaku.com + internal inventory |
| JP-vertical (`anime`, `manga`, `gameya`, `mercari`, `rakuten`, `ndl_books`, `houbun_jp`) | varies | Japan-domain, BQ has English-world bias | NDL OAI-PMH, JNDL, 商用 API, in-house crawlers |

## Topology Decision

BigQuery is the **international-public-record substrate** (≈17 domains).
etzhayyim-internal, JP-vertical, industrial-IoT, private-transaction, and
PII-observation domains stay on dedicated collectors / partnerships. The two
paths converge at `vertex_*` / `edge_*` in RisingWave; they do not merge at
the BigQuery layer.

This makes the ADR's "BigQuery as preprocessing layer, RisingWave as canonical
graph store" claim concrete: BigQuery cannot be the single source of world
coverage even within its 17 covered domains, and especially cannot be the
source for the ~40 JP-vertical / industrial / private-data domains that
together account for the bulk of `world_total` mass (multi-trillion record
domains like `photos`, `kessai`, `serial`, `seizo`, `bim`, `invoice`,
`receipt`, `natural-person`).

# Rejected Approach

Reject literal "copy all BigQuery public data into RisingWave". It would turn
RisingWave into a raw data lake, force Hummock/B2 growth unrelated to graph
queries, and make LLM training lineage harder rather than easier. The accepted
pattern is: BigQuery raw public data -> narrow projections / artifacts ->
RisingWave graph and training manifests.

Reject "BigQuery is sufficient for etzhayyim world coverage". Per the §etzhayyim
World-Coverage Mapping above, BigQuery covers at most ~17 of the ~50+
high-mass `dim_world_domain` app_hosts. The 5T-scale `photos`, the 1T-scale
`kessai` / `serial` / `seizo`, the 500B-scale `invoice` / `receipt`, and the
JP-vertical ecosystem (NDL / JPN gov / Mercari / etc.) are structurally
absent from BigQuery public data. Coverage parity requires the existing
collector / partnership topology to continue in parallel.
