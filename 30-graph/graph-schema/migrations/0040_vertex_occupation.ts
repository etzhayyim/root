import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0040: vertex_occupation table for recruit.gftd.ai taxonomy ingest.
 *
 * Stores ILO ISCO-08 / EU ESCO v1.1.1 / US O*NET occupation records.
 * Each record carries `source_license` (CC-BY-3.0-IGO / CC-BY-4.0 / public-domain)
 * for audit lineage. No PII; pure public taxonomy data.
 *
 * Design: 20-actors/recruit/actor-manifest.jsonld (governance.dataSources)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_occupation (
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
      isco_code         VARCHAR,
      esco_code         VARCHAR,
      onet_soc_code     VARCHAR,
      level             VARCHAR,
      name              VARCHAR,
      description       VARCHAR,
      alt_labels        VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_occupation`.execute(db);
}
