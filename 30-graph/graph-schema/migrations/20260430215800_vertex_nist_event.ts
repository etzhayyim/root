import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_nist_event (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      event_id    VARCHAR NOT NULL,
      event_kind  VARCHAR NOT NULL,
      event_json  VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_nist_event_kind ON vertex_nist_event (event_kind, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_nist_event`.execute(db);
}
