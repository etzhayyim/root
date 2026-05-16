import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add fetch diagnostics to vertex_gov_org.
 *
 * These columns separate "site could not be fetched" from "pipeline did not
 * process the site", so gov website coverage can distinguish public reachability
 * from hash coverage.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_status VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_error VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_checked_at VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_gov_org DROP COLUMN IF EXISTS last_fetch_checked_at`.execute(db);
  await sql`ALTER TABLE vertex_gov_org DROP COLUMN IF EXISTS last_fetch_error`.execute(db);
  await sql`ALTER TABLE vertex_gov_org DROP COLUMN IF EXISTS last_fetch_status`.execute(db);
}
