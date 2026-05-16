-- ADR 2605092800 §D7 — gsplat job-state log + latest-state MV.
--
-- Append-only, one row per phase transition. The streaming MV
-- `mv_maps_gsplat_job_latest` projects the most recent row per
-- `job_id` so the worker hot-path (`cmdGetGsplatJobStatus`) is a
-- single index lookup.
--
-- Persistence model = "Record-log semantics": no UPDATE, no
-- ON CONFLICT. PK = (vertex_id) where vertex_id encodes job_id + ts
-- so each phase is a fresh row; the MV deduplicates.

CREATE TABLE IF NOT EXISTS vertex_maps_gsplat_job (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 1,
  owner_did        varchar,
  job_id           varchar NOT NULL,
  job_kind         varchar NOT NULL,    -- 'train' | 'bake'
  tile_h3          varchar,
  status           varchar NOT NULL,    -- 'queued' | 'running' | 'completed' | 'failed'
  phase            varchar,             -- free-form, see dumper _state.phase
  message          varchar,
  splat_count      bigint,
  triangle_count   bigint,
  byte_size        bigint,
  runtime_ms       bigint,
  ts               varchar NOT NULL,    -- ISO 8601
  actor_did        varchar NOT NULL DEFAULT 'anon',
  org_did          varchar NOT NULL DEFAULT 'anon',
  at_did           varchar,
  created_at       varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_job_jobid_ts
  ON vertex_maps_gsplat_job (job_id, ts DESC);
CREATE INDEX IF NOT EXISTS idx_maps_gsplat_job_tile_ts
  ON vertex_maps_gsplat_job (tile_h3, ts DESC);
CREATE INDEX IF NOT EXISTS idx_maps_gsplat_job_kind_status_ts
  ON vertex_maps_gsplat_job (job_kind, status, ts DESC);

-- Latest snapshot per job_id. DISTINCT ON keyed first by job_id so
-- the streaming hash agg state is bounded by job count, not by
-- phase-event count. ts cutoff = 7 days so the MV doesn't accrete
-- forever; finished jobs older than that fall off.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_gsplat_job_latest AS
  SELECT DISTINCT ON (job_id)
    job_id, job_kind, tile_h3, status, phase, message,
    splat_count, triangle_count, byte_size, runtime_ms, ts
  FROM vertex_maps_gsplat_job
  WHERE ts > to_char(now() - INTERVAL '7 days', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
  ORDER BY job_id, ts DESC;
