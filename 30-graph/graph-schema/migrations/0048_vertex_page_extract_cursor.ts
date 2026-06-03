import { Kysely, sql } from 'kysely';

/**
 * Migration 0048: per-domain extraction cursor columns on vertex_page (2026-04-14).
 *
 * Supports the commoncrawl.etzhayyim.com CF Worker entity-extraction pipeline
 * (`60-apps/etzhayyim-project-common-crawl/appview/.../src/app.ts`).
 *
 * Each `extracted_for_<domain>` column records when the Worker processed
 * a page for that domain (success or explicit skip). NULL = not yet
 * attempted. TIMESTAMP = attempted at this time. Re-processing for a
 * specific domain = set column back to NULL.
 *
 * Design: 90-docs/260414-domain-coverage-depth-design.md §CC-Worker
 */
export async function up(db: Kysely<unknown>): Promise<void> {
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
  const cols = new Set(existing.rows.map((row) => row.column_name));

  if (!cols.has('extracted_for_kuruma')) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_kuruma TIMESTAMP`.execute(db);
  }
  if (!cols.has('extracted_for_media_anime')) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_media_anime TIMESTAMP`.execute(db);
  }
  if (!cols.has('extracted_for_media_gamers')) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_media_gamers TIMESTAMP`.execute(db);
  }
  if (!cols.has('extracted_for_handotai')) {
    await sql`ALTER TABLE vertex_page ADD COLUMN extracted_for_handotai TIMESTAMP`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN; migration is forward-only.
}
