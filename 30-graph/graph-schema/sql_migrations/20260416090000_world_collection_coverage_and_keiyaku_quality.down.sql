DROP MATERIALIZED VIEW IF EXISTS mv_data_quality_latest;

DROP TABLE IF EXISTS vertex_data_quality_daily;

DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection;

DROP TABLE IF EXISTS dim_world_domain_collection;

DROP TABLE IF EXISTS edge_keiyaku_canonicalizes;

DROP TABLE IF EXISTS vertex_keiyaku_contract_observation;

DROP TABLE IF EXISTS vertex_keiyaku_contract_canonical;
