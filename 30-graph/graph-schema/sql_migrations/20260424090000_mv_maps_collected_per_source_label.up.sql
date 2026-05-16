DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label;

CREATE MATERIALIZED VIEW mv_maps_collected_per_source_label AS
    SELECT
      source_did,
      label,
      COUNT(*)::bigint AS collected_count
    FROM vertex_spatial
    GROUP BY source_did, label;
