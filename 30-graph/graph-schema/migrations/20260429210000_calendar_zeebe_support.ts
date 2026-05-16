import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gcal_oauth_token (
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
      last_sync_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gcal_oauth_token_email_status ON vertex_gcal_oauth_token (email, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_gcal_oauth_token_sync ON vertex_gcal_oauth_token (status, last_sync_at)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_gcal_oauth_token`.execute(db);
}
