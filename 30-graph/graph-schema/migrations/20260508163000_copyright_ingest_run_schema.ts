import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Copyright ingest graph schema.
 *
 * vertex_copyright_ingest_run — typed run-tracking vertex.
 *   One row per registry (crossref | datacite) per graph execution.
 *   Replaces the broken vertex_repo_commit.record_json audit pattern.
 *
 * edge_work_blob_of — traversable blob → work edge.
 *   src_vid = vertex_work_blob.vertex_id
 *   dst_vid = vertex_work.vertex_id
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_copyright_ingest_run (
      vertex_id       VARCHAR PRIMARY KEY,
      owner_did       VARCHAR NOT NULL,
      registry        VARCHAR NOT NULL,
      started_at      VARCHAR,
      finished_at     VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'running',
      rows_fetched    BIGINT DEFAULT 0,
      rows_inserted   BIGINT DEFAULT 0,
      error           VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_copyright_ingest_run_registry
      ON vertex_copyright_ingest_run(registry)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_copyright_ingest_run_status
      ON vertex_copyright_ingest_run(status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_copyright_ingest_run_started_at
      ON vertex_copyright_ingest_run(started_at)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_work_blob_of (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      owner_did       VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_work_blob_of_src
      ON edge_work_blob_of(src_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_work_blob_of_dst
      ON edge_work_blob_of(dst_vid)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_edge_work_blob_of_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_work_blob_of_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_work_blob_of`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_copyright_ingest_run_started_at`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_copyright_ingest_run_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_copyright_ingest_run_registry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_copyright_ingest_run`.execute(db);
}
