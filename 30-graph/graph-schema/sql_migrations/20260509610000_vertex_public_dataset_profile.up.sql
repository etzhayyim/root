-- ADR 2605092700 §P1 Profiling. Adds the canonical RisingWave surface
-- for the BigQuery public dataset P1 pass. P1 only runs against P0
-- candidates that have a `vertex_public_dataset_catalog` row with
-- `review_status` advanced past 'pending'; this migration provisions
-- the tables but does not seed any rows.
--
-- Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
-- no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.
--
-- Sensitivity: Tier 1 (`sensitivity_ord = 1`). Profiles describe public
-- BigQuery data; PII signal detection feeds the license / training
-- decision but the rows themselves carry only summary statistics.
--
-- MV safety: GROUP BY keys are bounded — `dataset_id` (~thousands),
-- `provider` (~tens), `recommended_ingest_mode` (5 values), `decision`
-- (3 values). No high-cardinality MAX(varchar) per CLAUDE.md MV memory
-- guardrails.

CREATE TABLE IF NOT EXISTS vertex_public_dataset_profile (
  vertex_id                            varchar PRIMARY KEY,
  _seq                                 bigint,
  created_date                         date,
  sensitivity_ord                      bigint DEFAULT 1,
  owner_did                            varchar,
  profile_run_id                       varchar NOT NULL,
  table_vertex_id                      varchar NOT NULL,
  dataset_id                           varchar NOT NULL,
  bq_project                           varchar NOT NULL,
  bq_dataset                           varchar NOT NULL,
  bq_table                             varchar NOT NULL,
  columns_profiled_json                varchar,
  key_candidate_json                   varchar,
  null_rate_json                       varchar,
  distinct_estimate_json               varchar,
  top_values_json                      varchar,
  text_columns_json                    varchar,
  language_distribution_json           varchar,
  text_length_stats_json               varchar,
  timestamp_range_json                 varchar,
  geo_coverage_json                    varchar,
  pii_signal_json                      varchar,
  license_decision                     varchar NOT NULL DEFAULT 'review',
  allowed_for_train                    varchar NOT NULL DEFAULT 'false',
  allowed_for_embedding                varchar NOT NULL DEFAULT 'false',
  dedupe_strategy                      varchar,
  delta_strategy                       varchar,
  recommended_risingwave_tables_json   varchar,
  recommended_edges_json               varchar,
  recommended_ingest_mode              varchar,
  estimated_monthly_refresh_scan_tib   double precision,
  estimated_monthly_refresh_cost_usd   double precision,
  profile_artifact_uri                 varchar,
  profile_hash                         varchar,
  bytes_billed                         bigint,
  profile_score                        double precision,
  review_status                        varchar NOT NULL DEFAULT 'pending',
  review_note                          varchar,
  observed_at                          varchar NOT NULL,
  props                                varchar,
  actor_did                            varchar NOT NULL DEFAULT 'anon',
  org_did                              varchar NOT NULL DEFAULT 'anon',
  at_did                               varchar,
  created_at                           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profile_run
  ON vertex_public_dataset_profile (profile_run_id);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profile_dataset
  ON vertex_public_dataset_profile (dataset_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profile_decision
  ON vertex_public_dataset_profile (license_decision, allowed_for_train);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profile_review
  ON vertex_public_dataset_profile (review_status, recommended_ingest_mode);

-- ── edge_public_dataset_profiles_table ────────────────────────────────────
-- Lineage: profile → BigQuery table that produced it. 1 row per
-- (profile, table). One table can be re-profiled across runs.

CREATE TABLE IF NOT EXISTS edge_public_dataset_profiles_table (
  edge_id            varchar PRIMARY KEY,
  src_vid            varchar NOT NULL,
  dst_vid            varchar NOT NULL,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  profile_run_id     varchar NOT NULL,
  dataset_id         varchar,
  bytes_billed       bigint,
  rows_scanned       bigint,
  observed_at        varchar NOT NULL,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profiles_table_src
  ON edge_public_dataset_profiles_table (src_vid);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profiles_table_dst
  ON edge_public_dataset_profiles_table (dst_vid);

CREATE INDEX IF NOT EXISTS idx_public_dataset_profiles_table_run
  ON edge_public_dataset_profiles_table (profile_run_id);

-- ── edge_public_dataset_candidate_for_vertex_type ────────────────────────
-- Profile → target RisingWave vertex label candidate. Many-to-many: a
-- profile can recommend multiple target tables; a target table can be
-- fed by multiple datasets. `mapping_quality` is 0..1 (proxy for column
-- coverage × type compatibility × identifier overlap).

CREATE TABLE IF NOT EXISTS edge_public_dataset_candidate_for_vertex_type (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,
  dst_vid              varchar NOT NULL,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  dataset_id           varchar,
  target_vertex_label  varchar NOT NULL,
  column_mapping_json  varchar,
  mapping_quality      double precision,
  rationale            varchar,
  review_status        varchar NOT NULL DEFAULT 'pending',
  observed_at          varchar NOT NULL,
  actor_did            varchar NOT NULL DEFAULT 'anon',
  org_did              varchar NOT NULL DEFAULT 'anon',
  at_did               varchar,
  created_at           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_candidate_vertex_src
  ON edge_public_dataset_candidate_for_vertex_type (src_vid);

CREATE INDEX IF NOT EXISTS idx_public_dataset_candidate_vertex_dst
  ON edge_public_dataset_candidate_for_vertex_type (dst_vid);

CREATE INDEX IF NOT EXISTS idx_public_dataset_candidate_vertex_label
  ON edge_public_dataset_candidate_for_vertex_type (target_vertex_label, mapping_quality);

-- ── edge_public_dataset_candidate_for_training_task ──────────────────────
-- Profile → training task candidate (e.g. `training.llm.text.curation`,
-- `training.embedding.image.captioning`, `training.eval.benchmark.bigbench`).
-- License + PII gates are read from the parent profile row.

CREATE TABLE IF NOT EXISTS edge_public_dataset_candidate_for_training_task (
  edge_id                 varchar PRIMARY KEY,
  src_vid                 varchar NOT NULL,
  dst_vid                 varchar NOT NULL,
  _seq                    bigint,
  created_date            date,
  sensitivity_ord         bigint DEFAULT 1,
  owner_did               varchar,
  dataset_id              varchar,
  training_task           varchar NOT NULL,
  estimated_token_count   bigint,
  estimated_image_count   bigint,
  license_compatible      varchar NOT NULL DEFAULT 'unknown',
  pii_risk_ord            bigint,
  review_status           varchar NOT NULL DEFAULT 'pending',
  rationale               varchar,
  observed_at             varchar NOT NULL,
  actor_did               varchar NOT NULL DEFAULT 'anon',
  org_did                 varchar NOT NULL DEFAULT 'anon',
  at_did                  varchar,
  created_at              varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_public_dataset_candidate_training_src
  ON edge_public_dataset_candidate_for_training_task (src_vid);

CREATE INDEX IF NOT EXISTS idx_public_dataset_candidate_training_task
  ON edge_public_dataset_candidate_for_training_task (training_task, license_compatible);

-- ── edge_dataset_produces_vertex_type ─────────────────────────────────────
-- Decided binding: `vertex_public_dataset_catalog` → target vertex label
-- after P0/P1 review. Promotes a candidate edge into an explicit
-- production binding consumed by P2 projection planning.

CREATE TABLE IF NOT EXISTS edge_dataset_produces_vertex_type (
  edge_id              varchar PRIMARY KEY,
  src_vid              varchar NOT NULL,
  dst_vid              varchar NOT NULL,
  _seq                 bigint,
  created_date         date,
  sensitivity_ord      bigint DEFAULT 1,
  owner_did            varchar,
  dataset_id           varchar,
  target_vertex_label  varchar NOT NULL,
  ingest_mode          varchar NOT NULL,
  approved_by          varchar,
  approved_at          varchar,
  scan_budget_tib      double precision,
  observed_at          varchar NOT NULL,
  actor_did            varchar NOT NULL DEFAULT 'anon',
  org_did              varchar NOT NULL DEFAULT 'anon',
  at_did               varchar,
  created_at           varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_dataset_produces_vertex_src
  ON edge_dataset_produces_vertex_type (src_vid);

CREATE INDEX IF NOT EXISTS idx_dataset_produces_vertex_label
  ON edge_dataset_produces_vertex_type (target_vertex_label);

-- ── edge_dataset_allowed_for_training_task ───────────────────────────────
-- Decided binding: dataset → training task after explicit license + PII
-- review. Default-deny — `mv_training_source_eligibility` only allows
-- combinations that have a row here.

CREATE TABLE IF NOT EXISTS edge_dataset_allowed_for_training_task (
  edge_id            varchar PRIMARY KEY,
  src_vid            varchar NOT NULL,
  dst_vid            varchar NOT NULL,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  dataset_id         varchar,
  training_task      varchar NOT NULL,
  license            varchar,
  approved_by        varchar,
  approved_at        varchar,
  observed_at        varchar NOT NULL,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_dataset_allowed_training_src
  ON edge_dataset_allowed_for_training_task (src_vid);

CREATE INDEX IF NOT EXISTS idx_dataset_allowed_training_task
  ON edge_dataset_allowed_for_training_task (training_task);

-- ── mv_public_dataset_profile_rank ────────────────────────────────────────
-- Per dataset: rank by review state and cost. GROUP BY dataset_id is
-- bounded by P1 candidate set (~thousands at most). Latest profile per
-- dataset chosen by MAX(observed_at).

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_public_dataset_profile_rank AS
SELECT
  p.dataset_id,
  p.bq_project,
  p.bq_dataset,
  COUNT(*)                                               AS profile_count,
  MAX(p.observed_at)                                     AS last_observed_at,
  MAX(p.profile_score)                                   AS best_profile_score,
  MIN(p.estimated_monthly_refresh_cost_usd)              AS cheapest_refresh_cost_usd,
  SUM(CASE WHEN p.review_status = 'approved' THEN 1 ELSE 0 END) AS profiles_approved,
  SUM(CASE WHEN p.review_status = 'rejected' THEN 1 ELSE 0 END) AS profiles_rejected,
  SUM(CASE WHEN p.review_status = 'pending'  THEN 1 ELSE 0 END) AS profiles_pending,
  SUM(CASE WHEN p.allowed_for_train = 'true' THEN 1 ELSE 0 END) AS profiles_allowed_for_train,
  SUM(CASE WHEN p.license_decision = 'allow' THEN 1 ELSE 0 END) AS profiles_license_allow
FROM vertex_public_dataset_profile p
GROUP BY p.dataset_id, p.bq_project, p.bq_dataset;

-- ── mv_training_source_eligibility ───────────────────────────────────────
-- Default-deny eligibility surface. A dataset is allowed for a training
-- task only when an explicit `edge_dataset_allowed_for_training_task`
-- row exists. This MV exposes the join so callers do not have to walk
-- the decision graph by hand.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_training_source_eligibility AS
SELECT
  e.dataset_id,
  e.training_task,
  e.license,
  e.approved_by,
  e.approved_at,
  c.provider,
  c.bq_project,
  c.bq_dataset,
  c.review_status                       AS dataset_review_status,
  c.recommended_ingest_mode             AS dataset_ingest_mode,
  COALESCE(c.observed_at, e.observed_at) AS observed_at
FROM edge_dataset_allowed_for_training_task e
LEFT JOIN vertex_public_dataset_catalog c
  ON c.dataset_id = e.dataset_id;

-- ── mv_public_dataset_ingest_status ──────────────────────────────────────
-- Provider × ingest_mode rollup. Bounded by ~50 providers × 5 modes.

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_public_dataset_ingest_status AS
SELECT
  c.provider,
  COALESCE(c.recommended_ingest_mode, 'unspecified') AS ingest_mode,
  COUNT(*)                                            AS dataset_count,
  SUM(COALESCE(c.table_count, 0))                     AS table_count_total,
  SUM(CASE WHEN c.review_status = 'approved' THEN 1 ELSE 0 END) AS datasets_approved,
  SUM(CASE WHEN c.review_status = 'rejected' THEN 1 ELSE 0 END) AS datasets_rejected,
  SUM(CASE WHEN c.review_status = 'pending'  THEN 1 ELSE 0 END) AS datasets_pending,
  MAX(c.observed_at)                                  AS last_observed_at
FROM vertex_public_dataset_catalog c
GROUP BY c.provider, COALESCE(c.recommended_ingest_mode, 'unspecified');

GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_profile TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_public_dataset_profile TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_profiles_table TO root;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_profiles_table TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_candidate_for_vertex_type TO root;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_candidate_for_vertex_type TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_candidate_for_training_task TO root;
GRANT SELECT, INSERT, UPDATE ON edge_public_dataset_candidate_for_training_task TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_dataset_produces_vertex_type TO root;
GRANT SELECT, INSERT, UPDATE ON edge_dataset_produces_vertex_type TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_dataset_allowed_for_training_task TO root;
GRANT SELECT, INSERT, UPDATE ON edge_dataset_allowed_for_training_task TO kaisya_app;
-- RisingWave requires `MATERIALIZED VIEW` keyword on GRANT for streaming MVs;
-- the ungated form returns "is not a table" during the create-job race.
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_profile_rank TO root;
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_profile_rank TO kaisya_app;
GRANT SELECT ON MATERIALIZED VIEW mv_training_source_eligibility TO root;
GRANT SELECT ON MATERIALIZED VIEW mv_training_source_eligibility TO kaisya_app;
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_ingest_status TO root;
GRANT SELECT ON MATERIALIZED VIEW mv_public_dataset_ingest_status TO kaisya_app;
