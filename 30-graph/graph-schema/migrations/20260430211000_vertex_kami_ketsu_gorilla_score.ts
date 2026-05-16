import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_atrecord_kami_ketsu_gorilla_score (
      vertex_id  VARCHAR PRIMARY KEY,
      _seq       BIGINT NOT NULL,
      owner_did  VARCHAR NOT NULL,
      player_did VARCHAR NOT NULL,
      score      INTEGER NOT NULL,
      slaps      INTEGER NOT NULL,
      bananas    INTEGER NOT NULL,
      run_sec    DOUBLE PRECISION NOT NULL,
      created_at TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX idx_kami_ketsu_gorilla_score_rank
      ON vertex_atrecord_kami_ketsu_gorilla_score (score DESC, bananas DESC, run_sec ASC, created_at ASC)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_atrecord_kami_ketsu_gorilla_score`.execute(db);
}
