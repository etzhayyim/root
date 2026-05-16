DROP VIEW IF EXISTS view_world_coverage_live;

DROP VIEW IF EXISTS mv_world_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host;

DELETE FROM dim_world_domain WHERE domain = 'oil_tanker';

DROP TABLE IF EXISTS vertex_oil_tanker;
