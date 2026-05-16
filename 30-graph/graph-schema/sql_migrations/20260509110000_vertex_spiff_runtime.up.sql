-- ADR 2605081200 — SpiffWorkflow runtime state on RisingWave (PoC Phase 1).
--
-- Adds runtime tables for the SpiffWorkflow BPMN engine adopted as the Zeebe
-- replacement. Process XML registry (`vertex_bpmn_process_def`) and XRPC NSID
-- bindings (`vertex_bpmn_lexicon_binding`) are **engine-agnostic** and reused
-- as-is from `migrations/20260423000000_vertex_bpmn_actor_def.ts` — do not
-- redefine here.
--
-- Namespace separation (CRITICAL): Spiff runtime tables are prefixed
-- `vertex_spiff_*` to avoid collision with the legacy Camunda 8 (Zeebe) shape
-- `vertex_bpmn_instance` / `vertex_bpmn_activity_event` / `vertex_bpmn_signal_log`
-- (see `migrations/20260419150000_vertex_bpmn_tables.ts` and
-- `0001_initial_schema.ts`). Both runtimes coexist; legacy can be retired
-- after Zeebe broker decommission (ADR 2605081200 Phase 2).
--
-- Persistence model (root CLAUDE.md "Record-log semantics"):
--   * No UPDATE / no ON CONFLICT. PK re-INSERT = implicit upsert.
--   * Engine host serializes BpmnWorkflow → JSON, writes 1 row per
--     `vertex_spiff_instance` per token transition.
--   * Job dispatch = INSERT into `vertex_spiff_job` (status='ready'),
--     worker pulls via `mv_spiff_ready_jobs` and re-INSERTs row with
--     status='claimed'/'completed' (delete-then-insert upsert via PK).
--   * History append-only.
--
-- Sensitivity: Tier 1 (`sensitivity_ord = 100`) — instance state JSON may
-- contain user variables. Engine MUST field-encrypt private vars with the
-- `signal:v1:{ciphertext}` convention before serialize.

-- ── vertex_spiff_instance ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_spiff_instance (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 100,
  owner_did          varchar,
  instance_id        varchar NOT NULL,
  bpmn_process_id    varchar NOT NULL,
  process_version    bigint NOT NULL DEFAULT 1,
  state_json         varchar,
  state_byte_size    bigint,
  status             varchar DEFAULT 'running',
  correlation_key    varchar,
  variables_json     varchar,
  started_at         varchar,
  updated_at         varchar,
  completed_at       varchar,
  error_msg          varchar,
  org_id             varchar,
  user_id            varchar,
  actor_id           varchar
);

CREATE INDEX IF NOT EXISTS idx_spiff_instance_status_proc
  ON vertex_spiff_instance (status, bpmn_process_id);
CREATE INDEX IF NOT EXISTS idx_spiff_instance_correlation
  ON vertex_spiff_instance (correlation_key);
CREATE INDEX IF NOT EXISTS idx_spiff_instance_instance_seq
  ON vertex_spiff_instance (instance_id, _seq);

-- ── vertex_spiff_job ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_spiff_job (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 100,
  owner_did          varchar,
  job_id             varchar NOT NULL,
  instance_id        varchar NOT NULL,
  bpmn_process_id    varchar NOT NULL,
  task_id            varchar NOT NULL,
  task_type          varchar NOT NULL,
  variables_json     varchar,
  status             varchar DEFAULT 'ready',
  claimed_by         varchar,
  claimed_at         varchar,
  claim_until        varchar,
  result_json        varchar,
  error_msg          varchar,
  retry_count        bigint DEFAULT 0,
  enqueued_at        varchar,
  completed_at       varchar,
  org_id             varchar,
  user_id            varchar,
  actor_id           varchar
);

CREATE INDEX IF NOT EXISTS idx_spiff_job_status_type
  ON vertex_spiff_job (status, task_type);
CREATE INDEX IF NOT EXISTS idx_spiff_job_status_type_enqueued
  ON vertex_spiff_job (status, task_type, enqueued_at);
CREATE INDEX IF NOT EXISTS idx_spiff_job_instance
  ON vertex_spiff_job (instance_id);
CREATE INDEX IF NOT EXISTS idx_spiff_job_claim_until
  ON vertex_spiff_job (claim_until);
CREATE INDEX IF NOT EXISTS idx_spiff_job_job_seq
  ON vertex_spiff_job (job_id, _seq);
CREATE INDEX IF NOT EXISTS idx_spiff_job_type_job_seq
  ON vertex_spiff_job (task_type, job_id, _seq);

-- ── vertex_spiff_timer ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_spiff_timer (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 100,
  owner_did          varchar,
  timer_id           varchar NOT NULL,
  instance_id        varchar NOT NULL,
  task_id            varchar,
  fire_at            varchar NOT NULL,
  status             varchar DEFAULT 'pending',
  cycle_expr         varchar,
  created_at         varchar,
  fired_at           varchar
);

CREATE INDEX IF NOT EXISTS idx_spiff_timer_pending_fire_at
  ON vertex_spiff_timer (status, fire_at);

-- ── vertex_spiff_history ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_spiff_history (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 100,
  owner_did          varchar,
  instance_id        varchar NOT NULL,
  seq                bigint NOT NULL,
  event_type         varchar NOT NULL,
  task_id            varchar,
  task_type          varchar,
  payload_json       varchar,
  ts                 varchar NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_spiff_history_instance_seq
  ON vertex_spiff_history (instance_id, seq);

-- ── MV: worker pull source ──────────────────────────────────────────────────
-- Exposes only the latest record-log snapshot per job_id.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_spiff_ready_jobs AS
SELECT
  j.job_id,
  j.instance_id,
  j.bpmn_process_id,
  j.task_id,
  j.task_type,
  j.variables_json,
  j.enqueued_at,
  j.retry_count
FROM vertex_spiff_job AS j
JOIN (
  SELECT job_id, max(_seq) AS latest_seq
  FROM vertex_spiff_job
  GROUP BY job_id
) AS latest
  ON j.job_id = latest.job_id
 AND j._seq = latest.latest_seq
WHERE j.status = 'ready';

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_spiff_ready_jobs_v2 AS
SELECT
  j.job_id,
  j.instance_id,
  j.bpmn_process_id,
  j.task_id,
  j.task_type,
  j.created_date,
  j.variables_json,
  j.enqueued_at,
  j.retry_count,
  j.org_id,
  j.user_id,
  j.actor_id,
  j._seq
FROM vertex_spiff_job AS j
JOIN (
  SELECT job_id, max(_seq) AS latest_seq
  FROM vertex_spiff_job
  GROUP BY job_id
) AS latest
  ON j.job_id = latest.job_id
 AND j._seq = latest.latest_seq
WHERE j.status = 'ready';
