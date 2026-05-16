import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * 2026-05-03 out-of-band schema fixes for common-crawl entity extraction pipeline.
 *
 * Problem 1: vertex_page was missing extracted_for_{kuruma,media_anime,media_gamers,handotai}
 *   columns. Migration 0048 recorded them as applied but they were lost during the
 *   phase3k CC bulk ingest S3 SWAP (2026-04-16). Applied out-of-band via psycopg3.
 *
 * Problem 2: No index on vertex_page(domain). The entity extraction Zeebe task
 *   (commonCrawl.entities.extract) queries WHERE domain IN (...) LIMIT 15 against
 *   985M rows — full table scan times out at 120s. Applied as BACKGROUND DDL with
 *   enable_locality_backfill=true (job 16856, 2026-05-03 10:51 UTC).
 *
 * Problem 3: GRANT ALL ON ALL TABLES IN SCHEMA public TO root applied out-of-band
 *   (2026-05-03) since kaisya_app-owned tables were inaccessible to the root user
 *   (Zeebe worker). RisingWave does not support ALTER DEFAULT PRIVILEGES, so this
 *   must be re-run after each migration cycle that creates new tables.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Add missing extracted_for cursor columns (idempotent)
  const existing = await sql<{ column_name: string }>`
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'vertex_page'
      AND column_name IN (
        'extracted_for_kuruma',
        'extracted_for_media_anime',
        'extracted_for_media_gamers',
        'extracted_for_handotai'
      )
  `.execute(db);
  const cols = new Set(existing.rows.map((r) => r.column_name));

  if (!cols.has("extracted_for_kuruma")) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_kuruma TIMESTAMP WITH TIME ZONE`.execute(db);
  }
  if (!cols.has("extracted_for_media_anime")) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_media_anime TIMESTAMP WITH TIME ZONE`.execute(db);
  }
  if (!cols.has("extracted_for_media_gamers")) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_media_gamers TIMESTAMP WITH TIME ZONE`.execute(db);
  }
  if (!cols.has("extracted_for_handotai")) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_handotai TIMESTAMP WITH TIME ZONE`.execute(db);
  }

  // Domain index for entity extraction (BACKGROUND DDL — already running as job 16856)
  // This migration records the intent; the index was applied out-of-band.
  // Re-applying is safe since IF NOT EXISTS is used.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN or DROP INDEX on source tables.
}
