import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_baminiku_record (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      record_id   VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      stream_id   VARCHAR,
      agent_did   VARCHAR,
      record_json VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_baminiku_record_collection ON vertex_baminiku_record (collection, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_baminiku_record_stream ON vertex_baminiku_record (stream_id, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_baminiku_record_agent ON vertex_baminiku_record (agent_did, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_baminiku_record`.execute(db);
}
