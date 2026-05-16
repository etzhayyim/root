DROP INDEX IF EXISTS idx_blockchain_tx_time;
DROP INDEX IF EXISTS idx_blockchain_tx_block;
DROP INDEX IF EXISTS idx_blockchain_tx_chain_hash;
DROP TABLE IF EXISTS vertex_blockchain_tx;

DROP INDEX IF EXISTS idx_blockchain_block_time;
DROP INDEX IF EXISTS idx_blockchain_block_hash;
DROP INDEX IF EXISTS idx_blockchain_block_chain_height;
DROP TABLE IF EXISTS vertex_blockchain_block;

DROP INDEX IF EXISTS idx_chempat_patent;
DROP INDEX IF EXISTS idx_chempat_inchi;
DROP TABLE IF EXISTS vertex_chemistry_patent;

DROP INDEX IF EXISTS idx_target_evidence_score;
DROP INDEX IF EXISTS idx_target_evidence_disease;
DROP INDEX IF EXISTS idx_target_evidence_target;
DROP TABLE IF EXISTS vertex_target_evidence;

DROP INDEX IF EXISTS idx_forest_state_year;
DROP INDEX IF EXISTS idx_forest_plot;
DROP TABLE IF EXISTS vertex_forest_inventory;

DROP INDEX IF EXISTS idx_synthetic_condition;
DROP INDEX IF EXISTS idx_synthetic_person;
DROP TABLE IF EXISTS vertex_synthetic_patient;

DROP INDEX IF EXISTS idx_marine_platform;
DROP INDEX IF EXISTS idx_marine_geo;
DROP INDEX IF EXISTS idx_marine_time;
DROP TABLE IF EXISTS vertex_marine_observation;

DROP INDEX IF EXISTS idx_qa_post_tags;
DROP INDEX IF EXISTS idx_qa_post_owner;
DROP INDEX IF EXISTS idx_qa_post_parent;
DROP INDEX IF EXISTS idx_qa_post_community_id;
DROP TABLE IF EXISTS vertex_qa_post;

DROP INDEX IF EXISTS idx_taxi_trip_id;
DROP INDEX IF EXISTS idx_taxi_city_pickup;
DROP TABLE IF EXISTS vertex_taxi_trip;

DROP INDEX IF EXISTS idx_air_quality_geo;
DROP INDEX IF EXISTS idx_air_quality_parameter;
DROP INDEX IF EXISTS idx_air_quality_site;
DROP TABLE IF EXISTS vertex_air_quality_observation;
