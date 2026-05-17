import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_animeka — graph-native landing table for animeka.etzhayyim.com (team-based
 * anime creation appview).
 *
 * Parallel to vertex_mangaka (mangaka) but with cut (ショット) as the production
 * atom instead of page/panel. Supports the 18 domain record kinds:
 *   work · episode · script · scene · cut · storyboard · layout · keyframe ·
 *   inbetween · colorModel · colorTrace · background · composite · soundCue ·
 *   retake · character · asset · project · chatMessage
 *
 * - CREATE TABLE with typed columns (no EAV fallback to catch_all_vertex)
 * - Indexes on hot-path lookups (episode_id, cut_id, scene_id, stage, priority)
 * - view_animeka_record_flat — merges props JSON overflow onto typed columns
 * - MVs for Pipeline Board (stage status rollup), Review Room (open retake count),
 *   Series Dashboard (per-episode progress heatmap).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Base table — mirrors vertex_mangaka shape + anime-specific typed columns.
  await sql`
    CREATE TABLE IF NOT EXISTS "vertex_animeka" (
      "vertex_id"       VARCHAR PRIMARY KEY,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "did"             VARCHAR,
      "collection"      VARCHAR,
      "label"           VARCHAR,
      "kind"            VARCHAR,
      "title"           VARCHAR,
      "name"            VARCHAR,
      "display_name"    VARCHAR,
      "description"     TEXT,
      "parent_rkey"     VARCHAR,

      -- Anime pipeline foreign keys
      "work_id"         VARCHAR,
      "episode_id"      VARCHAR,
      "scene_id"        VARCHAR,
      "cut_id"          VARCHAR,
      "character_id"    VARCHAR,
      "project_id"      VARCHAR,
      "convo_id"        VARCHAR,
      "storyboard_id"   VARCHAR,
      "layout_id"       VARCHAR,
      "keyframe_id"     VARCHAR,
      "retake_id"       VARCHAR,
      "target_uri"      VARCHAR,

      -- Sequence + timing columns
      "episode_num"     BIGINT,
      "scene_num"       BIGINT,
      "cut_num"         BIGINT,
      "frame_num"       BIGINT,
      "duration_frames" BIGINT,
      "duration_sec"    DOUBLE PRECISION,
      "fps"             BIGINT,
      "in_frame"        BIGINT,
      "out_frame"       BIGINT,
      "timecode_frame"  BIGINT,

      -- Pipeline state
      "stage"           VARCHAR,
      "stage_status"    TEXT,   -- JSON map {script,storyboard,...,delivery → status}
      "assignees"       TEXT,   -- JSON map {stage → DID}
      "priority"        VARCHAR,
      "severity"        VARCHAR,
      "method"          VARCHAR,

      -- Camera + lighting + identity
      "camera_mode"     VARCHAR,
      "lighting_mood"   VARCHAR,
      "lighting_condition" VARCHAR,
      "slug"            VARCHAR,
      "author"          VARCHAR,
      "writer"          VARCHAR,
      "speaker"         VARCHAR,
      "track_type"      VARCHAR,
      "layer_role"      VARCHAR,

      -- Media / blob CIDs
      "image_cid"       VARCHAR,
      "thumb_cid"       VARCHAR,
      "master_cid"      VARCHAR,
      "layers_cid"      VARCHAR,
      "bg_cid"          VARCHAR,
      "color_layers_cid" VARCHAR,
      "flat_cid"        VARCHAR,
      "output_cid"      VARCHAR,
      "cover_cid"       VARCHAR,
      "ref_sheet_cid"   VARCHAR,
      "material_map_cid" VARCHAR,
      "asset_cid"       VARCHAR,
      "mime_type"       VARCHAR,
      "image_url"       VARCHAR,

      -- Geometry + aspect
      "width"           DOUBLE PRECISION,
      "height"          DOUBLE PRECISION,
      "x"               DOUBLE PRECISION,
      "y"               DOUBLE PRECISION,
      "w"               DOUBLE PRECISION,
      "h"               DOUBLE PRECISION,

      -- Heads-up fields
      "comment"         TEXT,
      "dialogue"        TEXT,
      "action"          TEXT,
      "camera_note"     TEXT,
      "sound_note"      TEXT,
      "body_cid"        VARCHAR,
      "heading_jp"      VARCHAR,
      "location"        VARCHAR,
      "time_of_day"     VARCHAR,
      "mood"            VARCHAR,

      -- Status + bookkeeping
      "cid"             VARCHAR,
      "status"          VARCHAR,
      "created_at"      VARCHAR,
      "props"           TEXT
    )
  `.execute(db);

  // Hot-path indexes (RisingWave index creation is idempotent via IF NOT EXISTS).
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_collection_created ON vertex_animeka (repo, collection, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_collection_rkey    ON vertex_animeka (repo, collection, rkey)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_parent_rkey        ON vertex_animeka (repo, parent_rkey)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_work_id            ON vertex_animeka (repo, work_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_episode_id         ON vertex_animeka (repo, episode_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_scene_id           ON vertex_animeka (repo, scene_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_cut_id             ON vertex_animeka (repo, cut_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_character_id       ON vertex_animeka (repo, character_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_project_id         ON vertex_animeka (repo, project_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_convo_id           ON vertex_animeka (repo, convo_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_stage              ON vertex_animeka (repo, stage)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_priority           ON vertex_animeka (repo, priority)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_episode_cut_num         ON vertex_animeka (episode_id, cut_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_animeka_cut_frame_num           ON vertex_animeka (cut_id, frame_num)`.execute(db);

  // Flat read view — direct projection of vertex_animeka typed columns.
  // (vertex_record_attribute EAV fallback dropped in Shannon Phase 2 cleanup
  //  20260419020000; all fields live on the typed table.)
  await sql`
    CREATE VIEW IF NOT EXISTS view_animeka_record_flat AS
    SELECT
      vertex_id,
      _seq,
      created_date,
      sensitivity_ord,
      owner_did,
      rkey,
      repo,
      did,
      collection,
      label,
      COALESCE(kind, split_part(collection, '.', array_length(string_to_array(collection, '.'), 1)), '') AS kind,
      title,
      name,
      COALESCE(display_name, name, title) AS display_name,
      description,
      parent_rkey,
      work_id,
      episode_id,
      episode_num,
      scene_id,
      scene_num,
      cut_id,
      cut_num,
      frame_num,
      duration_frames,
      duration_sec,
      fps,
      in_frame,
      out_frame,
      timecode_frame,
      character_id,
      COALESCE(project_id, convo_id) AS project_id,
      COALESCE(convo_id, project_id) AS convo_id,
      storyboard_id,
      layout_id,
      keyframe_id,
      target_uri,
      stage,
      stage_status,
      assignees,
      COALESCE(priority, 'normal') AS priority,
      severity,
      method,
      camera_mode,
      lighting_mood,
      lighting_condition,
      slug,
      author,
      writer,
      speaker,
      track_type,
      layer_role,
      image_cid,
      thumb_cid,
      master_cid,
      layers_cid,
      bg_cid,
      color_layers_cid,
      flat_cid,
      output_cid,
      cover_cid,
      ref_sheet_cid,
      material_map_cid,
      asset_cid,
      mime_type,
      image_url,
      width,
      height,
      x,
      y,
      w,
      h,
      comment,
      dialogue,
      action,
      camera_note,
      sound_note,
      body_cid,
      heading_jp,
      location,
      time_of_day,
      mood,
      cid,
      status,
      created_at,
      rkey AS id,
      props
    FROM vertex_animeka
  `.execute(db);

  // Rollup MVs.
  //
  // CARDINALITY check (per MV Memory Safety Guardrails in 30-graph/graph-schema/CLAUDE.md):
  // - mv_vertex_animeka_count:       GROUP BY (repo, collection, kind) — bounded by ~10 workers × 19 collections × 19 kinds ≪ 500K
  // - mv_animeka_cut_progress:       GROUP BY episode_id — bounded by episode count, LOW cardinality
  // - mv_animeka_open_retake_by_cut: GROUP BY cut_id — bounded by cut count, LOW cardinality
  //
  // All safe to materialize.

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_animeka_count AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(collection, '') AS collection,
      COALESCE(kind, split_part(collection, '.', array_length(string_to_array(collection, '.'), 1)), '') AS kind,
      COUNT(*)::bigint AS cnt
    FROM vertex_animeka
    GROUP BY 1, 2, 3
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_cut_progress AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(episode_id, '') AS episode_id,
      COUNT(*)::bigint AS cut_count,
      SUM(CASE WHEN priority = 'retake' THEN 1 ELSE 0 END)::bigint AS retake_count
    FROM vertex_animeka
    WHERE collection = 'ai.gftd.apps.animeka.cut'
    GROUP BY 1, 2
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_open_retake_by_cut AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COUNT(*)::bigint AS open_cnt
    FROM vertex_animeka
    WHERE collection = 'ai.gftd.apps.animeka.retake'
      AND COALESCE(status, 'open') = 'open'
    GROUP BY 1, 2
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_children_by_parent AS
    SELECT
      src_vid AS parent_vid,
      COALESCE(label, '') AS child_label,
      COUNT(*)::bigint AS cnt
    FROM edge_contains
    GROUP BY 1, 2
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_children_by_parent`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_open_retake_by_cut`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_animeka_cut_progress`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_animeka_count`.execute(db);
  await sql`DROP VIEW IF EXISTS view_animeka_record_flat`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_cut_frame_num`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_episode_cut_num`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_priority`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_stage`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_convo_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_project_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_character_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_cut_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_scene_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_episode_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_work_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_parent_rkey`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_collection_rkey`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_animeka_repo_collection_created`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_animeka`.execute(db);
}
