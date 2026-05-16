import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_kami_eng_record (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      record_id   VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      record_json VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_kami_eng_record_collection ON vertex_kami_eng_record (collection, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_kami_eng_record_kind ON vertex_kami_eng_record (record_kind, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_kami_eng_record`.execute(db);
}
