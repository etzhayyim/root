import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables touched in this migration.
// tier: B

/**
 * Recruit real public job ingest support.
 *
 * Adds lineage/index columns needed by keyless public ATS board ingest
 * (Greenhouse, Lever, Ashby) while preserving the public-postings-only boundary.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`ALTER TABLE vertex_job_posting ADD COLUMN IF NOT EXISTS source_homepage VARCHAR`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_recruit_job_ingest_run (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      run_id          VARCHAR NOT NULL,
      platform        VARCHAR,
      status          VARCHAR,
      fetched         BIGINT,
      inserted        BIGINT,
      skipped         BIGINT,
      limit_count     BIGINT,
      batch_size      BIGINT,
      started_at      VARCHAR,
      finished_at     VARCHAR,
      duration_ms     BIGINT,
      error           VARCHAR,
      props           VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_job_posting_source_id ON vertex_job_posting (source, source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_job_posting_ingested_at ON vertex_job_posting (ingested_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_job_ingest_run_started ON vertex_recruit_job_ingest_run (started_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_job_ingest_run_platform_status ON vertex_recruit_job_ingest_run (platform, status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_recruit_job_ingest_run_platform_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_recruit_job_ingest_run_started`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_recruit_job_ingest_run`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_job_posting_ingested_at`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_job_posting_source_id`.execute(db);
  await sql`ALTER TABLE vertex_job_posting DROP COLUMN IF EXISTS source_homepage`.execute(db);
}
