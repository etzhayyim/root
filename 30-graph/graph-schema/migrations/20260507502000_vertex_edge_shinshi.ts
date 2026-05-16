import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shinshi_model_profile (
      vertex_id VARCHAR PRIMARY KEY,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      model_did VARCHAR,
      char_name VARCHAR,
      series VARCHAR,
      age_look BIGINT,
      body_type VARCHAR,
      ethnicity_look VARCHAR,
      language TEXT,
      relationship_role VARCHAR,
      occupation VARCHAR,
      hobbies TEXT,
      personality TEXT,
      prompt_style TEXT,
      external_uri TEXT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shinshi_chat_message (
      vertex_id VARCHAR PRIMARY KEY,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      convo_id VARCHAR,
      model_did VARCHAR,
      user_did VARCHAR,
      role VARCHAR,
      content TEXT,
      in_reply_to VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shinshi_token_ledger (
      vertex_id VARCHAR PRIMARY KEY,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      user_did VARCHAR,
      balance BIGINT,
      granted BIGINT,
      purchased BIGINT,
      spent BIGINT,
      free_quota_used BIGINT,
      free_quota_reset_at VARCHAR,
      tier VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_shinshi_scene (
      vertex_id VARCHAR PRIMARY KEY,
      scene_id VARCHAR,
      model_did VARCHAR,
      user_did VARCHAR,
      scene_type VARCHAR,
      prompt TEXT,
      blob_key TEXT,
      post_uri TEXT,
      post_cid TEXT,
      tokens_spent BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  for (const table of ["edge_shinshi_model_profile", "edge_shinshi_conversation", "edge_shinshi_scene_post"]) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
        edge_id VARCHAR PRIMARY KEY,
        edge_key VARCHAR,
        src_vid VARCHAR,
        dst_vid VARCHAR,
        relation VARCHAR,
        value_json TEXT,
        created_at VARCHAR,
        updated_at VARCHAR,
        owner_did VARCHAR,
        sensitivity_ord BIGINT
      )
    `.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
  }

  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_model_profile_model ON vertex_shinshi_model_profile (model_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_model_profile_series ON vertex_shinshi_model_profile (series)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_chat_convo_created ON vertex_shinshi_chat_message (convo_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_chat_model_user ON vertex_shinshi_chat_message (model_did, user_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_token_user ON vertex_shinshi_token_ledger (user_did, updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_scene_model_created ON vertex_shinshi_scene (model_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_shinshi_scene_user_created ON vertex_shinshi_scene (user_did, created_at)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_model_activity AS
    SELECT
      p.model_did,
      max(p.char_name) AS char_name,
      max(p.series) AS series,
      count(DISTINCT c.vertex_id) AS chat_messages,
      count(DISTINCT s.vertex_id) AS scenes
    FROM vertex_shinshi_model_profile p
    LEFT JOIN vertex_shinshi_chat_message c ON c.model_did = p.model_did
    LEFT JOIN vertex_shinshi_scene s ON s.model_did = p.model_did
    GROUP BY p.model_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_token_liability AS
    SELECT
      count(*) AS ledger_count,
      sum(balance) AS outstanding_balance,
      sum(spent) AS total_spent
    FROM vertex_shinshi_token_ledger
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_token_liability`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_model_activity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shinshi_scene_post`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shinshi_conversation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_shinshi_model_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shinshi_scene`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shinshi_token_ledger`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shinshi_chat_message`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_shinshi_model_profile`.execute(db);
}
