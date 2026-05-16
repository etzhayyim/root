import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * App-specific edge tables for animeka (TODO #5).
 *
 * Three edges cover the hot-path queries that the UI / reactive pipeline needs:
 *
 *   edge_retakes         — retake → target record (cut / keyframe / layout / ...)
 *                          (+ stage, severity, status columns for Review Room filters)
 *
 *   edge_cut_has_keyframe — cut → keyframe|inbetween|colorTrace|composite
 *                           (+ frame_num + kind for X-sheet timeline ordering)
 *
 *   edge_assigned_to      — any animeka record → actor DID
 *                           (+ stage column for stage-specific assignee lookups)
 *
 * The existing generic edge_contains table still rolls up children per label
 * (see mv_animeka_children_by_parent in 20260420140000); these dedicated edges
 * give O(log N) point lookups instead of scanning the generic table.
 *
 * RisingWave notes:
 *   - VARCHAR without explicit length (parser rejects VARCHAR(N) in CREATE TABLE).
 *   - No CREATE INDEX IF NOT EXISTS ambiguity — RW accepts IF NOT EXISTS.
 *   - MV uses low-cardinality GROUP BY (per-cut) — safe per MV Memory Safety Guardrails.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── edge_retakes — retake → target ─────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "edge_retakes" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "stage"           VARCHAR,
      "severity"        VARCHAR,
      "status"          VARCHAR,
      "timecode_frame"  BIGINT,
      "author"          VARCHAR,
      "assignee"        VARCHAR,
      "created_at"      VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_retakes_src       ON edge_retakes (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_retakes_dst       ON edge_retakes (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_retakes_cut_stage ON edge_retakes (cut_id, stage)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_retakes_status    ON edge_retakes (status, severity)`.execute(db);

  // ── edge_cut_has_keyframe — cut → keyframe|inbetween|colorTrace|composite
  await sql`
    CREATE TABLE IF NOT EXISTS "edge_cut_has_keyframe" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "frame_num"       BIGINT,
      "kind"            VARCHAR,
      "layer_role"      VARCHAR,
      "created_at"      VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_src           ON edge_cut_has_keyframe (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_dst           ON edge_cut_has_keyframe (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_cut_frame     ON edge_cut_has_keyframe (cut_id, frame_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_cut_kind      ON edge_cut_has_keyframe (cut_id, kind)`.execute(db);

  // ── edge_assigned_to — record → actor DID ──────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS "edge_assigned_to" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "stage"           VARCHAR,
      "assignee_did"    VARCHAR,
      "created_at"      VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_src       ON edge_assigned_to (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_dst       ON edge_assigned_to (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_cut_stage ON edge_assigned_to (cut_id, stage)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_assignee  ON edge_assigned_to (assignee_did, stage)`.execute(db);

  // ── Rollup MVs ────────────────────────────────────────────────────────
  //
  // Cardinality check (MV Memory Safety Guardrails): all GROUP BYs are per-cut
  // or per-actor, bounded by cut count × severity (~4) or actor count (~100).

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_retake_queue AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COALESCE(stage, '') AS stage,
      COALESCE(severity, 'minor') AS severity,
      COUNT(*)::bigint AS open_cnt
    FROM edge_retakes
    WHERE COALESCE(status, 'open') = 'open'
    GROUP BY 1, 2, 3, 4
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_frame_count_by_cut AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COALESCE(kind, 'unknown') AS kind,
      COUNT(*)::bigint AS frame_cnt
    FROM edge_cut_has_keyframe
    GROUP BY 1, 2, 3
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_workload_by_assignee AS
    SELECT
      COALESCE(assignee_did, '') AS assignee_did,
      COALESCE(stage, '') AS stage,
      COUNT(*)::bigint AS cnt
    FROM edge_assigned_to
    GROUP BY 1, 2
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_workload_by_assignee`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_frame_count_by_cut`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_retake_queue`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_assigned_to_assignee`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_assigned_to_cut_stage`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_assigned_to_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_assigned_to_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_assigned_to`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_cut_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_cut_frame`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_cut_has_keyframe`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_retakes_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_retakes_cut_stage`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_retakes_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_retakes_src`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_retakes`.execute(db);
}
