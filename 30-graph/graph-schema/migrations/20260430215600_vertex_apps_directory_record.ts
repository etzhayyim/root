import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_apps_directory_record (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      record_id   VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      app_did     VARCHAR,
      listing_id  VARCHAR,
      category    VARCHAR,
      record_json VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_apps_directory_collection ON vertex_apps_directory_record (collection, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_apps_directory_listing ON vertex_apps_directory_record (listing_id, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_apps_directory_category ON vertex_apps_directory_record (category, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_apps_directory_record`.execute(db);
}
