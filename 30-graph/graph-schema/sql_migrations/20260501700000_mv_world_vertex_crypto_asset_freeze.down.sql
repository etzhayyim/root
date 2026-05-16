DROP VIEW IF EXISTS view_world_coverage_live;

DROP VIEW IF EXISTS mv_world_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host;

UPDATE dim_world_domain
    SET app_host = 'sanctions'
    WHERE domain = 'crypto_asset_freeze';
