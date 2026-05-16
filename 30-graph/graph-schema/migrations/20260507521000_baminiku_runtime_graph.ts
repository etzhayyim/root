import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      stream_id VARCHAR,
      agent_did VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_stream`)} ON ${sql.table(table)} (stream_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_agent`)} ON ${sql.table(table)} (agent_did)`.execute(db);
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
  await baseVertex(db, "vertex_baminiku_agent_profile");
  await sql`ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS display_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS voice_preset VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_agent_profile ADD COLUMN IF NOT EXISTS personality TEXT`.execute(db);

  await baseVertex(db, "vertex_baminiku_stream");
  await sql`ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS title VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS stage_preset VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS visibility VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS scheduled_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_stream ADD COLUMN IF NOT EXISTS knp_room VARCHAR`.execute(db);

  await baseVertex(db, "vertex_baminiku_stage_patch");
  await baseVertex(db, "vertex_baminiku_chat");
  await sql`ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS viewer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS convo_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_chat ADD COLUMN IF NOT EXISTS text TEXT`.execute(db);

  await baseVertex(db, "vertex_baminiku_tip");
  await sql`ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS viewer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS amount DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS currency VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_tip ADD COLUMN IF NOT EXISTS effect_type VARCHAR`.execute(db);

  await baseVertex(db, "vertex_baminiku_track");
  await sql`ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS title VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS artist VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS audio_uri TEXT`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS requested_by_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_track ADD COLUMN IF NOT EXISTS queue_position BIGINT`.execute(db);

  await baseVertex(db, "vertex_baminiku_track_event");
  await sql`ALTER TABLE vertex_baminiku_track_event ADD COLUMN IF NOT EXISTS skipped_track_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_baminiku_track_event ADD COLUMN IF NOT EXISTS reason TEXT`.execute(db);

  await baseEdge(db, "edge_baminiku_stream_agent");
  await baseEdge(db, "edge_baminiku_stream_stage_patch");
  await baseEdge(db, "edge_baminiku_stream_chat");
  await baseEdge(db, "edge_baminiku_stream_tip");
  await baseEdge(db, "edge_baminiku_stream_track");
  await baseEdge(db, "edge_baminiku_stream_track_event");

  await sql`CREATE INDEX IF NOT EXISTS idx_baminiku_stream_status ON vertex_baminiku_stream (status, visibility, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_baminiku_chat_viewer ON vertex_baminiku_chat (viewer_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_baminiku_tip_viewer ON vertex_baminiku_tip (viewer_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_baminiku_track_queue ON vertex_baminiku_track (stream_id, status, queue_position)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_baminiku_stream_activity_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_baminiku_stream_activity_counts AS
    SELECT s.stream_id, s.agent_did, s.status, s.visibility,
      count(DISTINCT c.vertex_id)::BIGINT AS chat_count,
      count(DISTINCT t.vertex_id)::BIGINT AS tip_count,
      coalesce(sum(t.amount), 0) AS tip_amount_total,
      count(DISTINCT tr.vertex_id)::BIGINT AS track_count
    FROM vertex_baminiku_stream s
    LEFT JOIN vertex_baminiku_chat c ON c.stream_id = s.stream_id
    LEFT JOIN vertex_baminiku_tip t ON t.stream_id = s.stream_id
    LEFT JOIN vertex_baminiku_track tr ON tr.stream_id = s.stream_id
    GROUP BY s.stream_id, s.agent_did, s.status, s.visibility
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_baminiku_stream_activity_counts`.execute(db);
  for (const table of [
    "edge_baminiku_stream_track_event",
    "edge_baminiku_stream_track",
    "edge_baminiku_stream_tip",
    "edge_baminiku_stream_chat",
    "edge_baminiku_stream_stage_patch",
    "edge_baminiku_stream_agent",
    "vertex_baminiku_track_event",
    "vertex_baminiku_track",
    "vertex_baminiku_tip",
    "vertex_baminiku_chat",
    "vertex_baminiku_stage_patch",
    "vertex_baminiku_stream",
    "vertex_baminiku_agent_profile",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
