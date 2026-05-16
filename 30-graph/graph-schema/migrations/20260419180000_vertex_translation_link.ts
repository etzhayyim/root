import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0034 — typed projection table for `ai.gftd.apps.media_gamers.record.translationLink`.
 *
 * Replaces value_json parsing in cmdListLinks with typed Kysely queries.
 * Graph worker handleCollection() routes the 6-segment NSID directly to
 * this table (convention fallback only matches 5-segment NSIDs).
 *
 * Indexes: (source_uri) and (translated_uri) so listLinks lookups by
 * either side of the pair stay O(log N).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_translation_link (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      source_uri       VARCHAR,
      source_lang      VARCHAR,
      translated_uri   VARCHAR,
      lang             VARCHAR,
      source           VARCHAR,
      quality_score    DOUBLE PRECISION,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_translation_link_source_uri ON vertex_translation_link (source_uri)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_translation_link_translated_uri ON vertex_translation_link (translated_uri)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_translation_link_translated_uri`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_translation_link_source_uri`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_translation_link`.execute(db);
}
