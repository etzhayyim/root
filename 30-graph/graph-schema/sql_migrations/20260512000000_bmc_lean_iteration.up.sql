-- BMC lean iteration loop — record-log graph for the
-- lg-yatabase `bmc_iteration` LangGraph.
--
-- Single writer = lg-yatabase Granian pod (mitama-yata-pool).
-- yatabase CF Worker is a thin XRPC forwarder and never writes here.
-- Persistence model = root CLAUDE.md "Record-log semantics":
--   no ON CONFLICT, no UPDATE, PK re-INSERT = implicit upsert. Status
--   transitions live in `vertex_bmc_hypothesis_event` (append-only).
--
-- All vertex/edge tables carry ADR-0095 RLS columns
-- (actor_did / org_did / at_did / created_at).
--
-- ── vertex_bmc_state — canvas snapshot (versioned) ─────────────────────
CREATE TABLE IF NOT EXISTS vertex_bmc_state (
  vertex_id        varchar PRIMARY KEY,
  version          bigint  NOT NULL,
  canvas_json      varchar NOT NULL,
  rationale        varchar,
  source           varchar NOT NULL,
  parent_vertex_id varchar,
  sensitivity_ord  bigint  DEFAULT 1,
  owner_did        varchar,
  actor_did        varchar NOT NULL DEFAULT 'anon',
  org_did          varchar NOT NULL DEFAULT 'anon',
  at_did           varchar,
  created_by       varchar NOT NULL,
  created_at       varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_state_version     ON vertex_bmc_state (version);
CREATE INDEX IF NOT EXISTS idx_bmc_state_org_version ON vertex_bmc_state (org_did, version);

-- ── vertex_bmc_hypothesis — immutable spec ─────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_bmc_hypothesis (
  vertex_id       varchar PRIMARY KEY,
  slug            varchar NOT NULL,
  block           varchar NOT NULL,
  statement       varchar NOT NULL,
  metric          varchar NOT NULL,
  metric_query    varchar NOT NULL,
  threshold       double precision NOT NULL,
  baseline        double precision NOT NULL,
  deadline_iso    varchar NOT NULL,
  min_sample      bigint  NOT NULL,
  authored_by     varchar NOT NULL,
  auto_apply_pivot bigint DEFAULT 0,
  sensitivity_ord bigint  DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_hyp_slug      ON vertex_bmc_hypothesis (slug);
CREATE INDEX IF NOT EXISTS idx_bmc_hyp_block     ON vertex_bmc_hypothesis (block, deadline_iso);
CREATE INDEX IF NOT EXISTS idx_bmc_hyp_org_block ON vertex_bmc_hypothesis (org_did, block);

-- ── vertex_bmc_hypothesis_event — status log (UPDATE-free) ─────────────
CREATE TABLE IF NOT EXISTS vertex_bmc_hypothesis_event (
  vertex_id           varchar PRIMARY KEY,
  hypothesis_slug     varchar NOT NULL,
  prev_status         varchar,
  next_status         varchar NOT NULL,
  reason              varchar,
  authored_by         varchar NOT NULL,
  iteration_vertex_id varchar,
  sensitivity_ord     bigint  DEFAULT 1,
  owner_did           varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_hyp_evt_slug_time ON vertex_bmc_hypothesis_event (hypothesis_slug, created_at);
CREATE INDEX IF NOT EXISTS idx_bmc_hyp_evt_org_time  ON vertex_bmc_hypothesis_event (org_did, created_at);

-- ── vertex_bmc_iteration — one row per BML cycle ───────────────────────
CREATE TABLE IF NOT EXISTS vertex_bmc_iteration (
  vertex_id           varchar PRIMARY KEY,
  hypothesis_slug     varchar NOT NULL,
  iteration_no        bigint  NOT NULL,
  bmc_version_in      bigint  NOT NULL,
  bmc_version_out     bigint  NOT NULL,
  measured_value      double precision NOT NULL,
  measured_at         varchar NOT NULL,
  measurement_source  varchar NOT NULL,
  passed              bigint  NOT NULL,
  notes               varchar,
  sensitivity_ord     bigint  DEFAULT 1,
  owner_did           varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_iter_slug_time ON vertex_bmc_iteration (hypothesis_slug, created_at);
CREATE INDEX IF NOT EXISTS idx_bmc_iter_org_time  ON vertex_bmc_iteration (org_did, created_at);

-- ── vertex_bmc_decision ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vertex_bmc_decision (
  vertex_id           varchar PRIMARY KEY,
  iteration_vertex_id varchar NOT NULL,
  hypothesis_slug     varchar NOT NULL,
  action              varchar NOT NULL,
  rationale           varchar NOT NULL,
  authored_by         varchar NOT NULL,
  applied_at          varchar NOT NULL,
  sensitivity_ord     bigint  DEFAULT 1,
  owner_did           varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_dec_iter      ON vertex_bmc_decision (iteration_vertex_id);
CREATE INDEX IF NOT EXISTS idx_bmc_dec_org_time  ON vertex_bmc_decision (org_did, created_at);

-- ── vertex_bmc_metric_sample — measurement raw sidecar (replay) ────────
-- Stripe / Plausible API echo can carry tier-2 surface (per-customer
-- aggregates), so sensitivity_ord defaults to 2.
CREATE TABLE IF NOT EXISTS vertex_bmc_metric_sample (
  vertex_id           varchar PRIMARY KEY,
  iteration_vertex_id varchar NOT NULL,
  hypothesis_slug     varchar NOT NULL,
  metric              varchar NOT NULL,
  metric_query        varchar NOT NULL,
  numerator           double precision,
  denominator         double precision,
  measured_value      double precision NOT NULL,
  sample_size         bigint NOT NULL,
  window_start_ms     bigint,
  window_end_ms       bigint,
  source              varchar NOT NULL,
  raw_response        varchar,
  latency_ms          bigint,
  error_text          varchar,
  sensitivity_ord     bigint  DEFAULT 2,
  owner_did           varchar,
  actor_did           varchar NOT NULL DEFAULT 'anon',
  org_did             varchar NOT NULL DEFAULT 'anon',
  at_did              varchar,
  created_at          varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_bmc_sample_iter      ON vertex_bmc_metric_sample (iteration_vertex_id);
CREATE INDEX IF NOT EXISTS idx_bmc_sample_hyp_time  ON vertex_bmc_metric_sample (hypothesis_slug, created_at);
CREATE INDEX IF NOT EXISTS idx_bmc_sample_window    ON vertex_bmc_metric_sample (hypothesis_slug, window_start_ms, window_end_ms);

-- ── edge_bmc_state_supersedes — version chain ──────────────────────────
CREATE TABLE IF NOT EXISTS edge_bmc_state_supersedes (
  edge_id         varchar PRIMARY KEY,
  src_vid         varchar NOT NULL,
  dst_vid         varchar NOT NULL,
  _seq            bigint,
  created_date    date,
  sensitivity_ord bigint DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_edge_bmc_supersedes_src ON edge_bmc_state_supersedes (src_vid);

-- ── edge_bmc_hypothesis_in_block ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_bmc_hypothesis_in_block (
  edge_id         varchar PRIMARY KEY,
  src_vid         varchar NOT NULL,
  dst_vid         varchar NOT NULL,
  _seq            bigint,
  created_date    date,
  sensitivity_ord bigint DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_edge_bmc_hyp_in_block_src ON edge_bmc_hypothesis_in_block (src_vid);

-- ── edge_bmc_iteration_of_hypothesis ───────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_bmc_iteration_of_hypothesis (
  edge_id         varchar PRIMARY KEY,
  src_vid         varchar NOT NULL,
  dst_vid         varchar NOT NULL,
  _seq            bigint,
  created_date    date,
  sensitivity_ord bigint DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_edge_bmc_iter_of_hyp_src ON edge_bmc_iteration_of_hypothesis (src_vid);

-- ── edge_bmc_decision_of_iteration ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS edge_bmc_decision_of_iteration (
  edge_id         varchar PRIMARY KEY,
  src_vid         varchar NOT NULL,
  dst_vid         varchar NOT NULL,
  _seq            bigint,
  created_date    date,
  sensitivity_ord bigint DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_edge_bmc_dec_of_iter_src ON edge_bmc_decision_of_iteration (src_vid);

-- ── edge_bmc_pivot_applied_to_state ────────────────────────────────────
-- Decision (pivot, applied) -> new BMC state row.
CREATE TABLE IF NOT EXISTS edge_bmc_pivot_applied_to_state (
  edge_id         varchar PRIMARY KEY,
  src_vid         varchar NOT NULL,
  dst_vid         varchar NOT NULL,
  _seq            bigint,
  created_date    date,
  sensitivity_ord bigint DEFAULT 1,
  owner_did       varchar,
  actor_did       varchar NOT NULL DEFAULT 'anon',
  org_did         varchar NOT NULL DEFAULT 'anon',
  at_did          varchar,
  created_at      varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);
CREATE INDEX IF NOT EXISTS idx_edge_bmc_pivot_applied_src ON edge_bmc_pivot_applied_to_state (src_vid);

-- ── Materialized Views ─────────────────────────────────────────────────
-- All MVs have cardinality bounded by (org × {hypothesis | block | head}),
-- well under the 500k-key safety threshold (graph-schema CLAUDE.md
-- §"MV Memory Safety Guardrails"). No high-cardinality GROUP BY, no wide
-- MAX(varchar) other than the head MV which keeps 1 row per org.

-- 1. Current BMC head (one row per org_did)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bmc_state_head AS
SELECT s1.vertex_id, s1.version, s1.canvas_json, s1.rationale, s1.source,
       s1.created_by, s1.created_at, s1.org_did
FROM vertex_bmc_state s1
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_bmc_state s2
  WHERE s2.org_did = s1.org_did AND s2.version > s1.version
);

-- 2. Hypothesis latest status (UPDATE-free status materialization)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bmc_hypothesis_status AS
SELECT DISTINCT ON (hypothesis_slug, org_did)
  hypothesis_slug,
  org_did,
  next_status        AS status,
  authored_by        AS status_authored_by,
  created_at         AS status_at
FROM vertex_bmc_hypothesis_event
ORDER BY hypothesis_slug, org_did, created_at DESC;

-- 3. Latest iteration per hypothesis (round-robin LRU + Studio view)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bmc_iteration_latest AS
SELECT DISTINCT ON (hypothesis_slug, org_did)
  hypothesis_slug,
  org_did,
  vertex_id          AS iteration_vertex_id,
  iteration_no,
  measured_value,
  passed,
  created_at
FROM vertex_bmc_iteration
ORDER BY hypothesis_slug, org_did, created_at DESC;

-- 4. Block × org rollup (Studio left pane, 9 × org_count rows)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bmc_block_health AS
SELECT
  h.org_did,
  h.block,
  COUNT(*)                                          AS hyp_total,
  COUNT(*) FILTER (WHERE s.status = 'active')       AS hyp_active,
  COUNT(*) FILTER (WHERE s.status = 'completed')    AS hyp_completed,
  COUNT(*) FILTER (WHERE s.status = 'killed')       AS hyp_killed,
  AVG(i.measured_value)                             AS avg_measured,
  MAX(i.created_at)                                 AS last_iter_at
FROM vertex_bmc_hypothesis h
LEFT JOIN mv_bmc_hypothesis_status s
  ON s.hypothesis_slug = h.slug AND s.org_did = h.org_did
LEFT JOIN mv_bmc_iteration_latest i
  ON i.hypothesis_slug = h.slug AND i.org_did = h.org_did
GROUP BY h.org_did, h.block;

-- ── grants ──────────────────────────────────────────────────────────────
-- root = lg-yatabase Granian pod (single writer). kaisya_app = read-only.
GRANT SELECT, INSERT ON vertex_bmc_state            TO root;
GRANT SELECT, INSERT ON vertex_bmc_hypothesis       TO root;
GRANT SELECT, INSERT ON vertex_bmc_hypothesis_event TO root;
GRANT SELECT, INSERT ON vertex_bmc_iteration        TO root;
GRANT SELECT, INSERT ON vertex_bmc_decision         TO root;
GRANT SELECT, INSERT ON vertex_bmc_metric_sample    TO root;
GRANT SELECT, INSERT ON edge_bmc_state_supersedes         TO root;
GRANT SELECT, INSERT ON edge_bmc_hypothesis_in_block      TO root;
GRANT SELECT, INSERT ON edge_bmc_iteration_of_hypothesis  TO root;
GRANT SELECT, INSERT ON edge_bmc_decision_of_iteration    TO root;
GRANT SELECT, INSERT ON edge_bmc_pivot_applied_to_state   TO root;

GRANT SELECT ON vertex_bmc_state            TO kaisya_app;
GRANT SELECT ON vertex_bmc_hypothesis       TO kaisya_app;
GRANT SELECT ON vertex_bmc_hypothesis_event TO kaisya_app;
GRANT SELECT ON vertex_bmc_iteration        TO kaisya_app;
GRANT SELECT ON vertex_bmc_decision         TO kaisya_app;
GRANT SELECT ON vertex_bmc_metric_sample    TO kaisya_app;
GRANT SELECT ON edge_bmc_state_supersedes         TO kaisya_app;
GRANT SELECT ON edge_bmc_hypothesis_in_block      TO kaisya_app;
GRANT SELECT ON edge_bmc_iteration_of_hypothesis  TO kaisya_app;
GRANT SELECT ON edge_bmc_decision_of_iteration    TO kaisya_app;
GRANT SELECT ON edge_bmc_pivot_applied_to_state   TO kaisya_app;
GRANT SELECT ON mv_bmc_state_head            TO kaisya_app;
GRANT SELECT ON mv_bmc_hypothesis_status     TO kaisya_app;
GRANT SELECT ON mv_bmc_iteration_latest      TO kaisya_app;
GRANT SELECT ON mv_bmc_block_health          TO kaisya_app;
