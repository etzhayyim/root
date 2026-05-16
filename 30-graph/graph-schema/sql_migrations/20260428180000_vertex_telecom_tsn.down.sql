DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_breach_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_sync_health;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_shaper_state;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_stream_state;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_bridge_inventory;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_tsn_domain_state;

DROP TABLE IF EXISTS edge_telecom_tsn_breach_for_stream;

DROP TABLE IF EXISTS edge_telecom_tsn_stream_via_bridges;

DROP TABLE IF EXISTS edge_telecom_tsn_bridge_in_domain;

DROP TABLE IF EXISTS vertex_telecom_tsn_sla_breach;

DROP TABLE IF EXISTS vertex_telecom_tsn_sync_deviation;

DROP TABLE IF EXISTS vertex_telecom_tsn_frer_profile;

DROP TABLE IF EXISTS vertex_telecom_tsn_shaper;

DROP TABLE IF EXISTS vertex_telecom_tsn_stream;

DROP TABLE IF EXISTS vertex_telecom_tsn_sync_profile;

DROP TABLE IF EXISTS vertex_telecom_tsn_bridge;

DROP TABLE IF EXISTS vertex_telecom_tsn_domain;
