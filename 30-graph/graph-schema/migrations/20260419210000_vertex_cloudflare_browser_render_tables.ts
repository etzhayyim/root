import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_cloudflare_browser_render_* tables for cfbr0w53.
 * Session + render artifact log. RLS 3-col + created_at.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cloudflare_browser_render_session (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      session_id VARCHAR, durable_object_id VARCHAR, options VARCHAR,
      opened_at VARCHAR, expires_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cloudflare_browser_render_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, url VARCHAR, output VARCHAR, cid VARCHAR, byte_size BIGINT, note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_cloudflare_browser_render_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cloudflare_browser_render_session`.execute(db);
}
