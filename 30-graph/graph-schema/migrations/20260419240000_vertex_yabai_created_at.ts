import { Kysely, sql } from 'kysely';

/**
 * ADR-0036 follow-up — add `created_at` to 3 yabai tables whose original
 * 20260417120000 migration only carried domain-specific timestamps
 * (scored_at / synced_at / banned_at). Worker-direct writeRecord() always
 * stamps created_at, so inserts silently failed until this ran.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`ALTER TABLE vertex_yabai_risk ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_enforcement ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_yabai_registration_ban ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`ALTER TABLE vertex_yabai_risk DROP COLUMN IF EXISTS created_at`.execute(db);
  await sql`ALTER TABLE vertex_yabai_enforcement DROP COLUMN IF EXISTS created_at`.execute(db);
  await sql`ALTER TABLE vertex_yabai_registration_ban DROP COLUMN IF EXISTS created_at`.execute(db);
}
