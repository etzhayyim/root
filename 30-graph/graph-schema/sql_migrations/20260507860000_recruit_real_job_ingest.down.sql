DROP INDEX IF EXISTS idx_recruit_job_ingest_run_platform_status;

DROP INDEX IF EXISTS idx_recruit_job_ingest_run_started;

DROP TABLE IF EXISTS vertex_recruit_job_ingest_run;

DROP INDEX IF EXISTS idx_vertex_job_posting_ingested_at;

DROP INDEX IF EXISTS idx_vertex_job_posting_source_id;

ALTER TABLE vertex_job_posting DROP COLUMN IF EXISTS source_homepage;
