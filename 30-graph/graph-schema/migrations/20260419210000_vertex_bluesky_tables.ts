import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_bluesky_* tables for Bluesky Search Ingest actor (ADR-0037).
 *
 * 6 landing tables + IVF vector column on post for semantic search.
 * All records carry source_did / source_rkey to preserve AT Protocol
 * provenance for 47条の5 attribution + tombstone cascade lookup.
 *
 * Invariants:
 * - post.text is public per Bluesky AT Protocol design; snippet display
 *   capped to 200 char at query layer (see searchPosts lexicon).
 * - opt_out + tombstone tables drive erasure cascade (hard delete).
 * - embedding column pre-allocated for future IVF index creation
 *   (CREATE INDEX ... USING ivf WITH (lists=...) applied separately
 *   once post count passes threshold).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_post (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      source_rkey           VARCHAR,
      source_uri            VARCHAR,
      source_cid            VARCHAR,
      handle                VARCHAR,
      text                  VARCHAR,
      lang                  VARCHAR,
      lang_detected         VARCHAR,
      created_at            VARCHAR,
      indexed_at            VARCHAR,
      reply_root_uri        VARCHAR,
      reply_parent_uri      VARCHAR,
      embed_kind            VARCHAR,
      embed_media_cids      VARCHAR,
      embed_alt_text        VARCHAR,
      embed_external_uri    VARCHAR,
      labels                VARCHAR,
      embedding             VARCHAR,
      embedding_norm        DOUBLE PRECISION,
      ivf_cluster_id        BIGINT,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_profile (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      handle                VARCHAR,
      display_name          VARCHAR,
      description           VARCHAR,
      avatar_cid            VARCHAR,
      banner_cid            VARCHAR,
      pds                   VARCHAR,
      labels                VARCHAR,
      opt_out_signal        VARCHAR,
      indexed_at            VARCHAR,
      embedding             VARCHAR,
      embedding_norm        DOUBLE PRECISION,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_follow (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      subject_did           VARCHAR,
      source_rkey           VARCHAR,
      created_at            VARCHAR,
      indexed_at            VARCHAR,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_opt_out (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      handle                VARCHAR,
      reason                VARCHAR,
      labeler_did           VARCHAR,
      detected_at           VARCHAR,
      purged_at             VARCHAR,
      note                  VARCHAR,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_tombstone (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      source_rkey           VARCHAR,
      source_collection     VARCHAR,
      event_kind            VARCHAR,
      detected_at           VARCHAR,
      cascade_completed_at  VARCHAR,
      actor_id              VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_bluesky_follows (
      edge_id               VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      src_vid               VARCHAR,
      dst_vid               VARCHAR,
      source_did            VARCHAR,
      subject_did           VARCHAR,
      created_at            VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_bluesky_follows`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_tombstone`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_opt_out`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_follow`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_post`.execute(db);
}
