DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label_canonical;

DROP FUNCTION IF EXISTS maps_canonicalize_source_did(varchar);
