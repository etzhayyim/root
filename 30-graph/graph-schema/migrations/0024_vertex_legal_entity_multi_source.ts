/**
 * Migration 0024: Add multi-source columns to vertex_legal_entity.
 *
 * Supports ingesting legal entity data from 194+ country registries
 * alongside GLEIF LEI. source/source_record_id identify the origin,
 * wikidata_qid/opencorporates_id enable cross-registry entity resolution.
 *
 * Design: 90-docs/260414-global-legal-entity-data-sources-design.md
 */
import { type Kysely, sql } from 'kysely';

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS source VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS source_record_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS wikidata_qid VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_legal_entity ADD COLUMN IF NOT EXISTS opencorporates_id VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN; migration is forward-only.
}
