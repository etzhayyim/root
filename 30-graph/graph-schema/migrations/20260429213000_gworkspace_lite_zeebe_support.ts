import type { Kysely } from "kysely";
import { sql } from "kysely";

const tokenTables = [
  "vertex_gtasks_oauth_token",
  "vertex_gsheets_oauth_token",
  "vertex_gdrive_oauth_token",
  "vertex_gcontacts_oauth_token",
  "vertex_gmeet_oauth_token",
  "vertex_gdocs_oauth_token",
  "vertex_gslides_oauth_token",
  "vertex_gmail_oauth_token",
] as const;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const table of tokenTables) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
        vertex_id VARCHAR PRIMARY KEY,
        account_did VARCHAR,
        email VARCHAR,
        encrypted_refresh_token VARCHAR,
        wrapped_data_key VARCHAR,
        iv VARCHAR,
        scope VARCHAR,
        access_token_cache VARCHAR,
        access_expires_at BIGINT,
        status VARCHAR,
        cursor VARCHAR,
        history_id VARCHAR,
        last_sync_at VARCHAR,
        created_at VARCHAR,
        updated_at VARCHAR,
        actor_did VARCHAR,
        org_did VARCHAR,
        at_did VARCHAR
      )
    `.execute(db);

    await sql`ALTER TABLE ${sql.table(table)} ADD COLUMN IF NOT EXISTS history_id VARCHAR`.execute(db);
    await sql`ALTER TABLE ${sql.table(table)} ADD COLUMN IF NOT EXISTS at_did VARCHAR`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.raw(`idx_${table}_email_status`)} ON ${sql.table(table)} (email, status)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.raw(`idx_${table}_sync`)} ON ${sql.table(table)} (status, last_sync_at)`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const table of [...tokenTables].reverse()) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
