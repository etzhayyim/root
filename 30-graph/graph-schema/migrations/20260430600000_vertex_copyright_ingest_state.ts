// tier: C
import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_copyright_ingest_state (
      registry         VARCHAR NOT NULL,
      cursor           VARCHAR,
      last_ingested_at VARCHAR,
      total_ingested   BIGINT  NOT NULL DEFAULT 0,
      last_post_count  BIGINT  NOT NULL DEFAULT 0,
      last_posted_at   VARCHAR,
      owner_did        VARCHAR NOT NULL DEFAULT 'did:web:copyright.gftd.ai',
      created_at       VARCHAR NOT NULL,
      updated_at       VARCHAR NOT NULL,
      PRIMARY KEY (registry)
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_copyright_ingest_state`.execute(db);
}
