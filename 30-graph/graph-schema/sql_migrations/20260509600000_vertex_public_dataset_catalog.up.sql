-- ADR 2605092700 — BigQuery public dataset P0 catalog/sample schema.
--
-- P0 = "what exists, what does it cost to touch, is it safe enough to design
-- an ingest adapter?" This migration provisions the canonical RisingWave
-- vertex/MV surface for the P0 catalog + sampling pass. P1 profile tables
-- (`vertex_public_dataset_profile`, `mv_public_dataset_profile_rank`,
-- `mv_training_source_eligibility`, `edge_dataset_*`) are deferred to a
-- follow-up migration once P0 outputs have been reviewed.
--
-- Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
-- no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.
--
-- Sensitivity: Tier 1 (`sensitivity_ord = 1`). Catalog rows describe
-- public BigQuery datasets only; PII/license decisions surface through
-- guess columns and gate downstream P1 / P2 ingest. Raw payload binaries
-- live in object storage (B2/GCS) and are referenced by URI only.

CREATE TABLE IF NOT EXISTS vertex_public_dataset_catalog (
  vertex_id                    varchar PRIMARY KEY,
  _seq                         bigint,
  created_date                 date,
  sensitivity_ord              bigint DEFAULT 1,
  owner_did                    varchar,
  dataset_id                   varchar NOT NULL,
  provider                     varchar NOT NULL,
  bq_project                   varchar NOT NULL,
  bq_dataset                   varchar NOT NULL,
  description                  varchar,
  homepage_url                 varchar,
  marketplace_url              varchar,
  license                      varchar,
  terms_url                    varchar,
  last_modified_at             varchar,
  table_count                  bigint,
  total_size_bytes_estimate    bigint,
  pii_tier_guess               bigint,
  allowed_for_train_guess      varchar,
  allowed_for_embedding_guess  varchar,
  recommended_ingest_mode      varchar,
  candidate_vertex_targets_json varchar,
  candidate_edge_targets_json  varchar,
  review_status                varchar NOT NULL DEFAULT 'pending',
  review_note                  varchar,
  observed_at                  varchar NOT NULL,
  props                        varchar,
  actor_did                    varchar NOT NULL DEFAULT 'anon',
  org_did                      varchar NOT NULL DEFAULT 'anon',
  at_did                       varchar,
  created_at                   varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_catalog_provider
  ON vertex_public_dataset_catalog (provider, dataset_id);

CREATE INDEX IF NOT EXISTS idx_public_dataset_catalog_review
  ON vertex_public_dataset_catalog (review_status, recommended_ingest_mode);

CREATE INDEX IF NOT EXISTS idx_public_dataset_catalog_observed
  ON vertex_public_dataset_catalog (observed_at);

CREATE TABLE IF NOT EXISTS vertex_public_dataset_table (
  vertex_id                       varchar PRIMARY KEY,
  _seq                            bigint,
  created_date                    date,
  sensitivity_ord                 bigint DEFAULT 1,
  owner_did                       varchar,
  dataset_vertex_id               varchar NOT NULL,
  dataset_id                      varchar NOT NULL,
  bq_project                      varchar NOT NULL,
  bq_dataset                      varchar NOT NULL,
  bq_table                        varchar NOT NULL,
  description                     varchar,
  table_kind                      varchar,
  schema_json                     varchar,
  partitioning_json               varchar,
  clustering_json                 varchar,
  row_count_estimate              bigint,
  size_bytes_estimate             bigint,
  last_modified_at                varchar,
  estimated_full_scan_cost_usd    double precision,
  estimated_delta_scan_cost_usd   double precision,
  review_status                   varchar NOT NULL DEFAULT 'pending',
  observed_at                     varchar NOT NULL,
  props                           varchar,
  actor_did                       varchar NOT NULL DEFAULT 'anon',
  org_did                         varchar NOT NULL DEFAULT 'anon',
  at_did                          varchar,
  created_at                      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_table_dataset
  ON vertex_public_dataset_table (dataset_vertex_id);

CREATE INDEX IF NOT EXISTS idx_public_dataset_table_fqn
  ON vertex_public_dataset_table (bq_project, bq_dataset, bq_table);

CREATE INDEX IF NOT EXISTS idx_public_dataset_table_size
  ON vertex_public_dataset_table (size_bytes_estimate);

CREATE TABLE IF NOT EXISTS vertex_public_dataset_sample (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  table_vertex_id    varchar NOT NULL,
  dataset_id         varchar NOT NULL,
  run_id             varchar NOT NULL,
  job_id             varchar,
  query_hash         varchar,
  query_text_uri     varchar,
  sample_rows_uri    varchar NOT NULL,
  sample_format      varchar NOT NULL,
  sample_row_count   bigint NOT NULL,
  sample_byte_size   bigint,
  sample_hash        varchar,
  bytes_billed       bigint,
  observed_at        varchar NOT NULL,
  props              varchar,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_sample_table
  ON vertex_public_dataset_sample (table_vertex_id);

CREATE INDEX IF NOT EXISTS idx_public_dataset_sample_run
  ON vertex_public_dataset_sample (run_id);

CREATE INDEX IF NOT EXISTS idx_public_dataset_sample_hash
  ON vertex_public_dataset_sample (sample_hash);

CREATE TABLE IF NOT EXISTS vertex_bigquery_ingest_job (
  vertex_id                varchar PRIMARY KEY,
  _seq                     bigint,
  created_date             date,
  sensitivity_ord          bigint DEFAULT 1,
  owner_did                varchar,
  job_id                   varchar NOT NULL,
  run_id                   varchar NOT NULL,
  query_kind               varchar NOT NULL,
  query_hash               varchar,
  query_text_uri           varchar,
  bq_project               varchar NOT NULL,
  bq_location              varchar,
  statement_type           varchar,
  destination_table        varchar,
  maximum_bytes_billed     bigint,
  total_bytes_processed    bigint,
  total_bytes_billed       bigint,
  slot_ms                  bigint,
  cache_hit                varchar,
  dry_run                  varchar,
  status                   varchar NOT NULL,
  error_reason             varchar,
  error_message            varchar,
  started_at               varchar,
  finished_at              varchar,
  estimated_cost_usd       double precision,
  observed_at              varchar NOT NULL,
  props                    varchar,
  actor_did                varchar NOT NULL DEFAULT 'anon',
  org_did                  varchar NOT NULL DEFAULT 'anon',
  at_did                   varchar,
  created_at               varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_bigquery_ingest_job_run
  ON vertex_bigquery_ingest_job (run_id);

CREATE INDEX IF NOT EXISTS idx_bigquery_ingest_job_kind_status
  ON vertex_bigquery_ingest_job (query_kind, status);

CREATE INDEX IF NOT EXISTS idx_bigquery_ingest_job_hash
  ON vertex_bigquery_ingest_job (query_hash);

CREATE TABLE IF NOT EXISTS vertex_bigquery_export_artifact (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  run_id             varchar NOT NULL,
  job_id             varchar,
  artifact_kind      varchar NOT NULL,
  source_dataset_id  varchar,
  source_table       varchar,
  export_uri         varchar NOT NULL,
  format             varchar NOT NULL,
  byte_size          bigint,
  row_count          bigint,
  sha256             varchar,
  license            varchar,
  observed_at        varchar NOT NULL,
  props              varchar,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_bigquery_export_artifact_run
  ON vertex_bigquery_export_artifact (run_id);

CREATE INDEX IF NOT EXISTS idx_bigquery_export_artifact_kind
  ON vertex_bigquery_export_artifact (artifact_kind);

CREATE INDEX IF NOT EXISTS idx_bigquery_export_artifact_sha256
  ON vertex_bigquery_export_artifact (sha256);

CREATE TABLE IF NOT EXISTS vertex_bigquery_profile_run (
  vertex_id                  varchar PRIMARY KEY,
  _seq                       bigint,
  created_date               date,
  sensitivity_ord            bigint DEFAULT 1,
  owner_did                  varchar,
  run_id                     varchar NOT NULL,
  mode                       varchar NOT NULL,
  bq_project                 varchar NOT NULL,
  provider_filter            varchar,
  dataset_filter             varchar,
  started_at                 varchar NOT NULL,
  finished_at                varchar,
  status                     varchar NOT NULL,
  datasets_seen              bigint,
  tables_seen                bigint,
  samples_taken              bigint,
  total_bytes_billed         bigint,
  total_cost_usd             double precision,
  max_bytes_billed_per_query bigint,
  monthly_scan_budget_tib    double precision,
  monthly_scan_used_tib      double precision,
  approval_note              varchar,
  error_message              varchar,
  props                      varchar,
  actor_did                  varchar NOT NULL DEFAULT 'anon',
  org_did                    varchar NOT NULL DEFAULT 'anon',
  at_did                     varchar,
  created_at                 varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_bigquery_profile_run_mode_status
  ON vertex_bigquery_profile_run (mode, status);

CREATE INDEX IF NOT EXISTS idx_bigquery_profile_run_started
  ON vertex_bigquery_profile_run (started_at);

-- ── mv_public_dataset_catalog_coverage ────────────────────────────────────
-- Per-provider rollup so the P0 review gate can see "missing metadata" at a
-- glance. Bounded GROUP BY (provider count <= ~50) — safe for streaming MV
-- per CLAUDE.md MV memory guardrails.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_public_dataset_catalog_coverage AS
SELECT
  c.provider,
  COUNT(*)                                                        AS dataset_count,
  SUM(CASE WHEN c.license IS NOT NULL AND c.license <> ''
           THEN 1 ELSE 0 END)                                     AS datasets_with_license,
  SUM(CASE WHEN c.terms_url IS NOT NULL AND c.terms_url <> ''
           THEN 1 ELSE 0 END)                                     AS datasets_with_terms,
  SUM(CASE WHEN c.recommended_ingest_mode IS NOT NULL
           THEN 1 ELSE 0 END)                                     AS datasets_with_recommendation,
  SUM(CASE WHEN c.review_status = 'approved' THEN 1 ELSE 0 END)   AS datasets_approved,
  SUM(CASE WHEN c.review_status = 'rejected' THEN 1 ELSE 0 END)   AS datasets_rejected,
  SUM(CASE WHEN c.review_status = 'pending' THEN 1 ELSE 0 END)    AS datasets_pending,
  SUM(COALESCE(c.table_count, 0))                                 AS table_count_total,
  MAX(c.observed_at)                                              AS last_observed_at
FROM vertex_public_dataset_catalog c
GROUP BY c.provider;

GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_catalog TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_catalog TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_table TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_table TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_sample TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_sample TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_ingest_job TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_ingest_job TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_export_artifact TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_export_artifact TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_profile_run TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_bigquery_profile_run TO kaisya_app;
-- RisingWave requires `MATERIALIZED VIEW` keyword on GRANT for streaming MVs;
-- the ungated form returns "is not a table" because the catalog row only
-- becomes visible to GRANT once the MV's create-job finishes, but the
-- explicit form resolves through the MV catalog directly.
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_catalog_coverage TO root;
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_catalog_coverage TO kaisya_app;
