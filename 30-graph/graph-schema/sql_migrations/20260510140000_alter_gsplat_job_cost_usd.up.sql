-- ADR 2605092800 §D14 — record per-job RunPod cost in USD.
--
-- Locks cost at job-time (the env-driven rate may shift, so
-- re-deriving from `runtime_ms × current_rate` is wrong for a finance
-- rollup). The dumper writes this from the RunPod response's
-- `stats.estimatedCostUsd`, which the handler computes as
-- `runtime_ms × RUNPOD_COST_USD_PER_SEC`.
--
-- Persistence model = "Record-log semantics": ALTER ADD only, no
-- destructive change, MV recreate inherits the new column.
ALTER TABLE vertex_maps_gsplat_job
  ADD COLUMN IF NOT EXISTS cost_usd double precision;

-- Refresh the latest-state MV so the cost field is queryable from the
-- worker hot path. RisingWave doesn't support ALTER on a MV body, so
-- DROP + CREATE is the standard pattern (idempotent).
DROP MATERIALIZED VIEW IF EXISTS mv_maps_gsplat_job_latest;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_gsplat_job_latest AS
  SELECT DISTINCT ON (job_id)
    job_id, job_kind, tile_h3, status, phase, message,
    splat_count, triangle_count, byte_size, runtime_ms, cost_usd, ts
  FROM vertex_maps_gsplat_job
  WHERE ts > to_char(now() - INTERVAL '7 days', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
  ORDER BY job_id, ts DESC;
