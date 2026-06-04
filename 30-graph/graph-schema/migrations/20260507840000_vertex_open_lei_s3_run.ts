/**
 * GLEIF LEI S3 bulk ingest tracking table.
 *
 * vertex_open_lei_s3_run tracks each weekly bulk-ingest run against the
 * GLEIF Golden Copy ZIP cached in B2 (b2://etzhayyim-nats/gleif/lei2.0/{date}/).
 * One row per publish_date; WHERE NOT EXISTS guards prevent duplicate rows.
 *
 * Companion pod: 50-infra/k8s/gleif-lei-s3-ingester/
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_lei_s3_run (
      vertex_id            VARCHAR         PRIMARY KEY,
      created_date         DATE,
      sensitivity_ord      INT             DEFAULT 1,
      owner_did            VARCHAR,
      publish_date         DATE            NOT NULL,
      b2_bucket            VARCHAR,
      b2_key               VARCHAR,
      records_read         BIGINT          DEFAULT 0,
      records_written      BIGINT          DEFAULT 0,
      run_status           VARCHAR,
      error_msg            VARCHAR,
      started_at           TIMESTAMP WITH TIME ZONE,
      finished_at          TIMESTAMP WITH TIME ZONE,
      created_at           TIMESTAMP WITH TIME ZONE,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_s3_run_publish_date
      ON vertex_open_lei_s3_run (publish_date)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_s3_run_status
      ON vertex_open_lei_s3_run (run_status)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_lei_s3_run`.execute(db);
}
