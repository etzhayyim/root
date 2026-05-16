import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * fukkou diet-speech ingest — recovered stub.
 *
 * Originally applied to prod out-of-band (kysely_migration row exists but
 * the source file was never committed). DDL here reproduces the live
 * prod schema (verified via information_schema + pg_indexes on
 * 2026-04-20) so that `pnpm db:migrate` no longer reports
 * `corrupted migrations: missing` and so local dev spin-ups get the
 * same shape. All statements are idempotent — on prod the existing
 * objects are preserved; on a fresh DB the table is created.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fukkou_diet_speech (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      owner_did         VARCHAR,
      speech_id         VARCHAR,
      meeting_url       VARCHAR,
      issue_id          VARCHAR,
      session           VARCHAR,
      chamber           VARCHAR,
      committee_name    VARCHAR,
      meeting_date      DATE,
      speech_order      INTEGER,
      speaker_name      VARCHAR,
      speaker_yomi      VARCHAR,
      speaker_group     VARCHAR,
      speaker_position  VARCHAR,
      speaker_role      VARCHAR,
      speech_text       VARCHAR,
      speech_length     INTEGER,
      topic_tag         VARCHAR,
      sentiment         VARCHAR,
      created_at        TIMESTAMP WITH TIME ZONE,
      llm_topic         VARCHAR,
      llm_position      VARCHAR,
      llm_commitment    VARCHAR,
      llm_summary       VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_diet_speech_committee ON vertex_fukkou_diet_speech (committee_name, meeting_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_diet_speech_session ON vertex_fukkou_diet_speech (session, chamber, meeting_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_diet_speech_speaker ON vertex_fukkou_diet_speech (speaker_name, speaker_group)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_diet_speech_speaker`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_diet_speech_session`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_diet_speech_committee`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fukkou_diet_speech`.execute(db);
}
