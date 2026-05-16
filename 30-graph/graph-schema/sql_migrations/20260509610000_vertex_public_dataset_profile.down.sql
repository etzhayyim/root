DROP MATERIALIZED VIEW IF EXISTS mv_public_dataset_ingest_status;
DROP MATERIALIZED VIEW IF EXISTS mv_training_source_eligibility;
DROP MATERIALIZED VIEW IF EXISTS mv_public_dataset_profile_rank;

DROP INDEX IF EXISTS idx_dataset_allowed_training_task;
DROP INDEX IF EXISTS idx_dataset_allowed_training_src;
DROP TABLE IF EXISTS edge_dataset_allowed_for_training_task;

DROP INDEX IF EXISTS idx_dataset_produces_vertex_label;
DROP INDEX IF EXISTS idx_dataset_produces_vertex_src;
DROP TABLE IF EXISTS edge_dataset_produces_vertex_type;

DROP INDEX IF EXISTS idx_public_dataset_candidate_training_task;
DROP INDEX IF EXISTS idx_public_dataset_candidate_training_src;
DROP TABLE IF EXISTS edge_public_dataset_candidate_for_training_task;

DROP INDEX IF EXISTS idx_public_dataset_candidate_vertex_label;
DROP INDEX IF EXISTS idx_public_dataset_candidate_vertex_dst;
DROP INDEX IF EXISTS idx_public_dataset_candidate_vertex_src;
DROP TABLE IF EXISTS edge_public_dataset_candidate_for_vertex_type;

DROP INDEX IF EXISTS idx_public_dataset_profiles_table_run;
DROP INDEX IF EXISTS idx_public_dataset_profiles_table_dst;
DROP INDEX IF EXISTS idx_public_dataset_profiles_table_src;
DROP TABLE IF EXISTS edge_public_dataset_profiles_table;

DROP INDEX IF EXISTS idx_public_dataset_profile_review;
DROP INDEX IF EXISTS idx_public_dataset_profile_decision;
DROP INDEX IF EXISTS idx_public_dataset_profile_dataset;
DROP INDEX IF EXISTS idx_public_dataset_profile_run;
DROP TABLE IF EXISTS vertex_public_dataset_profile;
