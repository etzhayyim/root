import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0039: vertex_occupation_wikidata — multilingual enrichment.
 *
 * Source: Wikidata SPARQL, property P8283 (ISCO-08 occupation class).
 * License: CC0.
 * Bridges ISCO-08 → Wikidata QID → 10-language labels for global UI.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_occupation_wikidata (
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
      wikidata_qid      VARCHAR,
      isco_code         VARCHAR,
      label_en          VARCHAR,
      label_ja          VARCHAR,
      label_fr          VARCHAR,
      label_de          VARCHAR,
      label_es          VARCHAR,
      label_zh          VARCHAR,
      label_ar          VARCHAR,
      label_ru          VARCHAR,
      label_pt          VARCHAR,
      label_it          VARCHAR,
      ingested_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_occupation_wikidata`.execute(db);
}
