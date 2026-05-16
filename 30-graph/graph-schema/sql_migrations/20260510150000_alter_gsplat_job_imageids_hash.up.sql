-- ADR 2605092800 §D16 — input-set hash for train idempotency.
--
-- `imageids_hash` is `sha256(",".join(sorted(imageIds))).hexdigest()`
-- computed by the dumper after Mapillary image-list resolution. Used
-- to short-circuit duplicate train calls on the same tile with an
-- unchanged Mapillary input set. Combined with content-addressing at
-- the output (D10) makes the train pipeline fully idempotent on
-- identical input.
--
-- Persistence model = "Record-log semantics": ALTER ADD only,
-- nullable so existing rows stay valid. MV recreate inherits the
-- new column.
ALTER TABLE vertex_maps_gsplat_job
  ADD COLUMN IF NOT EXISTS imageids_hash varchar;

-- DROP + CREATE the latest-state MV (RisingWave can't ALTER MV body).
DROP MATERIALIZED VIEW IF EXISTS mv_maps_gsplat_job_latest;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_gsplat_job_latest AS
  SELECT DISTINCT ON (job_id)
    job_id, job_kind, tile_h3, status, phase, message,
    splat_count, triangle_count, byte_size, runtime_ms, cost_usd,
    imageids_hash, ts
  FROM vertex_maps_gsplat_job
  WHERE ts > to_char(now() - INTERVAL '7 days', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
  ORDER BY job_id, ts DESC;
