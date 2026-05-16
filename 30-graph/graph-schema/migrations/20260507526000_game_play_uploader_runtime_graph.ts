import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      participant_did VARCHAR,
      session_id VARCHAR,
      upload_id VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_participant`)} ON ${sql.table(table)} (participant_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_session`)} ON ${sql.table(table)} (session_id, created_at)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await baseVertex(db, "vertex_game_play_participant");
  await sql`ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS participant_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS display_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS age_band VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_participant ADD COLUMN IF NOT EXISTS payout_handle VARCHAR`.execute(db);

  await baseVertex(db, "vertex_game_play_upload_session");
  await sql`ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS game_title VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS platform VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS duration_sec BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_game_play_upload_session ADD COLUMN IF NOT EXISTS capture_started_at VARCHAR`.execute(db);

  await baseVertex(db, "vertex_game_play_upload");
  await sql`ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS object_uri TEXT`.execute(db);
  await sql`ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS duration_sec BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_game_play_upload ADD COLUMN IF NOT EXISTS sha256 VARCHAR`.execute(db);

  await baseVertex(db, "vertex_game_play_review");
  await sql`ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS review_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS decision VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS reviewer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_game_play_review ADD COLUMN IF NOT EXISTS reward_estimate_jpy BIGINT`.execute(db);

  await baseVertex(db, "vertex_game_play_reward");
  await sql`ALTER TABLE vertex_game_play_reward ADD COLUMN IF NOT EXISTS reward_jpy BIGINT`.execute(db);

  await baseEdge(db, "edge_game_play_participant_session");
  await baseEdge(db, "edge_game_play_session_upload");
  await baseEdge(db, "edge_game_play_upload_review");
  await baseEdge(db, "edge_game_play_upload_reward");

  await sql`CREATE INDEX IF NOT EXISTS idx_game_play_participant_did ON vertex_game_play_participant (participant_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_game_play_upload_status ON vertex_game_play_upload (status, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_game_play_review_upload_decision ON vertex_game_play_review (upload_id, decision)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_game_play_reward_upload ON vertex_game_play_reward (upload_id, status)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_game_play_campaign_status`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_game_play_campaign_status AS
    SELECT
      count(DISTINCT p.vertex_id)::BIGINT AS participant_count,
      count(DISTINCT u.vertex_id)::BIGINT AS upload_count,
      coalesce(sum(CASE WHEN r.decision = 'approved' THEN u.duration_sec ELSE 0 END), 0)::BIGINT AS approved_duration_sec,
      coalesce(sum(rew.reward_jpy), 0)::BIGINT AS reward_jpy
    FROM vertex_game_play_participant p
    LEFT JOIN vertex_game_play_upload_session s ON s.participant_did = p.participant_did
    LEFT JOIN vertex_game_play_upload u ON u.session_id = s.session_id
    LEFT JOIN vertex_game_play_review r ON r.upload_id = u.upload_id
    LEFT JOIN vertex_game_play_reward rew ON rew.upload_id = u.upload_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_game_play_campaign_status`.execute(db);
  for (const table of [
    "edge_game_play_upload_reward",
    "edge_game_play_upload_review",
    "edge_game_play_session_upload",
    "edge_game_play_participant_session",
    "vertex_game_play_reward",
    "vertex_game_play_review",
    "vertex_game_play_upload",
    "vertex_game_play_upload_session",
    "vertex_game_play_participant",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
