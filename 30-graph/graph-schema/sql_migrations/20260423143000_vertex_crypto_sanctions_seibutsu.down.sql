DROP MATERIALIZED VIEW IF EXISTS mv_vertex_seibutsu_observation_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_sanctions_entry_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_crypto_asset_freeze_incident_count;

DROP TABLE IF EXISTS vertex_seibutsu_observation;

DROP TABLE IF EXISTS vertex_seibutsu_traits;

DROP TABLE IF EXISTS vertex_seibutsu_taxon;

DROP TABLE IF EXISTS vertex_sanctions_list_update;

DROP TABLE IF EXISTS vertex_sanctions_match;

DROP TABLE IF EXISTS vertex_sanctions_entry;

DROP TABLE IF EXISTS vertex_crypto_asset_freeze_forensic_trace;

DROP TABLE IF EXISTS vertex_crypto_asset_freeze_request;

DROP TABLE IF EXISTS vertex_crypto_asset_freeze_incident;
