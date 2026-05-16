DROP MATERIALIZED VIEW IF EXISTS mv_public_dataset_catalog_coverage;

DROP INDEX IF EXISTS idx_bigquery_profile_run_started;
DROP INDEX IF EXISTS idx_bigquery_profile_run_mode_status;
DROP TABLE IF EXISTS vertex_bigquery_profile_run;

DROP INDEX IF EXISTS idx_bigquery_export_artifact_sha256;
DROP INDEX IF EXISTS idx_bigquery_export_artifact_kind;
DROP INDEX IF EXISTS idx_bigquery_export_artifact_run;
DROP TABLE IF EXISTS vertex_bigquery_export_artifact;

DROP INDEX IF EXISTS idx_bigquery_ingest_job_hash;
DROP INDEX IF EXISTS idx_bigquery_ingest_job_kind_status;
DROP INDEX IF EXISTS idx_bigquery_ingest_job_run;
DROP TABLE IF EXISTS vertex_bigquery_ingest_job;

DROP INDEX IF EXISTS idx_public_dataset_sample_hash;
DROP INDEX IF EXISTS idx_public_dataset_sample_run;
DROP INDEX IF EXISTS idx_public_dataset_sample_table;
DROP TABLE IF EXISTS vertex_public_dataset_sample;

DROP INDEX IF EXISTS idx_public_dataset_table_size;
DROP INDEX IF EXISTS idx_public_dataset_table_fqn;
DROP INDEX IF EXISTS idx_public_dataset_table_dataset;
DROP TABLE IF EXISTS vertex_public_dataset_table;

DROP INDEX IF EXISTS idx_public_dataset_catalog_observed;
DROP INDEX IF EXISTS idx_public_dataset_catalog_review;
DROP INDEX IF EXISTS idx_public_dataset_catalog_provider;
DROP TABLE IF EXISTS vertex_public_dataset_catalog;
