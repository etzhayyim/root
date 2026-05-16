ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS last_rows_written integer;

ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS last_run_at timestamp;

DROP VIEW IF EXISTS view_maps_coverage_gap_ranked;

CREATE VIEW view_maps_coverage_gap_ranked AS
    SELECT
      vertex_id,
      source_did,
      label,
      collected_count,
      world_total,
      priority_weight,
      last_fetched_at,
      last_rows_written,
      last_run_at,
      ttl_hours,
      CASE
        WHEN last_fetched_at IS NULL THEN ttl_hours
        ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
      END AS hours_since_fetch,
      CASE
        WHEN last_rows_written IS NULL                THEN 1.0
        WHEN last_rows_written >= 20                  THEN 1.0
        WHEN last_rows_written >= 1                   THEN 0.7
        ELSE                                               0.3
      END::real AS productivity_factor,
      maps_coverage_gap_score(
        collected_count,
        world_total,
        priority_weight,
        CASE
          WHEN last_fetched_at IS NULL THEN ttl_hours
          ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
        END
      ) *
      (CASE
        WHEN last_rows_written IS NULL                THEN 1.0
        WHEN last_rows_written >= 20                  THEN 1.0
        WHEN last_rows_written >= 1                   THEN 0.7
        ELSE                                               0.3
      END)::double precision AS gap_score
    FROM vertex_maps_coverage_target
    ORDER BY gap_score DESC;
