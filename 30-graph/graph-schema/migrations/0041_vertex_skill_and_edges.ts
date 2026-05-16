import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0041: vertex_skill + edge_occupation_skill + edge_skill_skill.
 *
 * Stores ESCO v1.1.1 skill taxonomy (~13,500 skills) and the
 * occupation↔skill / skill↔skill relationship graph.
 * License: CC-BY-4.0 (recorded per-row in source_license).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_skill (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      source_homepage   VARCHAR,
      code              VARCHAR,
      esco_id           VARCHAR,
      skill_type        VARCHAR,
      reuse_level       VARCHAR,
      name              VARCHAR,
      description       VARCHAR,
      alt_labels        VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_occupation_skill (
      edge_id           VARCHAR PRIMARY KEY,
      occupation_id     VARCHAR,
      skill_id          VARCHAR,
      relation_type     VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_skill_skill (
      edge_id           VARCHAR PRIMARY KEY,
      requiring_id      VARCHAR,
      required_id       VARCHAR,
      relation_type     VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_skill_skill`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_occupation_skill`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_skill`.execute(db);
}
