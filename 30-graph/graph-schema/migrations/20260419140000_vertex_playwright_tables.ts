import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * vertex_playwright_* tables for etzhayyim-project-playwright (pl4y1t8r).
 *
 * Session + action + artifact log. RLS 3-col + created_at.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_playwright_session (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      session_id VARCHAR, target VARCHAR, user_agent VARCHAR, locale VARCHAR, viewport_json VARCHAR,
      state VARCHAR, opened_at VARCHAR, closed_at VARCHAR, expires_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_playwright_action (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      action_id VARCHAR, session_id VARCHAR, op VARCHAR, args_json VARCHAR, result_json VARCHAR,
      state VARCHAR, error VARCHAR, enqueued_at VARCHAR, started_at VARCHAR, finished_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_playwright_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, session_id VARCHAR, kind VARCHAR, r2_key VARCHAR, cid VARCHAR,
      byte_size BIGINT, captured_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_playwright_action_in_session (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      action_id VARCHAR, session_id VARCHAR, created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_playwright_artifact_in_session (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      artifact_id VARCHAR, session_id VARCHAR, created_at VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_playwright_artifact_in_session`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_playwright_action_in_session`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_playwright_artifact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_playwright_action`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_playwright_session`.execute(db);
}
