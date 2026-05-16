-- Down: restore pre-imageids_hash MV shape. Column itself stays
-- (idempotent ADD — DROP COLUMN is destructive and unnecessary for
-- forward-only schemas).
DROP MATERIALIZED VIEW IF EXISTS mv_maps_gsplat_job_latest;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_gsplat_job_latest AS
  SELECT DISTINCT ON (job_id)
    job_id, job_kind, tile_h3, status, phase, message,
    splat_count, triangle_count, byte_size, runtime_ms, cost_usd, ts
  FROM vertex_maps_gsplat_job
  WHERE ts > to_char(now() - INTERVAL '7 days', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
  ORDER BY job_id, ts DESC;
