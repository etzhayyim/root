import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_game_play_uploader_record (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT NOT NULL,
      owner_did       VARCHAR NOT NULL,
      record_id       VARCHAR NOT NULL,
      collection      VARCHAR NOT NULL,
      record_kind     VARCHAR NOT NULL,
      participant_did VARCHAR,
      session_id      VARCHAR,
      upload_id       VARCHAR,
      record_json     VARCHAR NOT NULL,
      created_at      TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX idx_vertex_gpu_record_collection ON vertex_game_play_uploader_record (collection, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_gpu_record_participant ON vertex_game_play_uploader_record (participant_did, created_at DESC)`.execute(db);
  await sql`CREATE INDEX idx_vertex_gpu_record_session ON vertex_game_play_uploader_record (session_id, created_at DESC)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_game_play_uploader_record`.execute(db);
}
