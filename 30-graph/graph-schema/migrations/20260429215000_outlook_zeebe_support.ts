import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_outlook_pending_oauth (
      vertex_id VARCHAR PRIMARY KEY,
      user_key VARCHAR,
      state VARCHAR,
      code_verifier VARCHAR,
      redirect_uri VARCHAR,
      created_at VARCHAR,
      expires_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_outlook_oauth_connection (
      vertex_id VARCHAR PRIMARY KEY,
      user_key VARCHAR,
      connected BOOLEAN,
      access_token VARCHAR,
      refresh_token VARCHAR,
      expires_at VARCHAR,
      token_type VARCHAR,
      display_name VARCHAR,
      email VARCHAR,
      scope VARCHAR,
      last_synced_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_outlook_sync_job (
      vertex_id VARCHAR PRIMARY KEY,
      user_key VARCHAR,
      email VARCHAR,
      status VARCHAR,
      emails_found BIGINT,
      emails_saved BIGINT,
      calendar_events_found BIGINT,
      calendar_events_saved BIGINT,
      error VARCHAR,
      created_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_outlook_pending_user_key ON vertex_outlook_pending_oauth (user_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_outlook_connection_user_key ON vertex_outlook_oauth_connection (user_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_outlook_connection_email ON vertex_outlook_oauth_connection (email)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_outlook_sync_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outlook_oauth_connection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outlook_pending_oauth`.execute(db);
}
