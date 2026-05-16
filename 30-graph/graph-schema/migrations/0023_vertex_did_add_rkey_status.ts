/**
 * Migration 0023: Add rkey + status columns to vertex_did.
 *
 * The kagami graph write path (insert-columns.ts) includes rkey in all
 * vertex INSERT statements. vertex_did was missing this column, causing
 * every identity.create to fail with "Column rkey not found" (500).
 */
import { type Kysely, sql } from 'kysely';

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS rkey VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS status VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS collection VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS controller VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS display_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_did ADD COLUMN IF NOT EXISTS description VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // RisingWave does not support DROP COLUMN; migration is forward-only.
}
